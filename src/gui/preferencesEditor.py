from data.preferences import Fields as PrefFields, MultipleChoice
from enum import Enum
from gui import resources
from pathlib import Path
import tkinter as tk
from tkinter import colorchooser, filedialog, messagebox
from tkinter.simpledialog import Dialog

class EditablePreference():
  '''Editable Preference as described by its data type, the field under which
  it is stored, and an explanation of what the preference does. May optionally
  also specify an initial directory to start file dialogs under.
  '''

  class Type(Enum):
    UNSPECIFIED = 0
    BOOLEAN = 1
    FILEPATH = 2
    FILEPATH_LIST = 3
    MULTIPLE_CHOICE = 4
    COLOR = 5

  def __init__(self, title, prefType: Type, explanation, validChoices=None,
               setButtonTitle=None, setButtonFiletypes=None):
    self.title = title
    self.prefType = prefType
    self.explanation = explanation
    self.validChoices = validChoices if validChoices is not None else {}
    self.setButtonTitle = setButtonTitle
    self.setButtonFiletypes = setButtonFiletypes

EDITABLES_BY_FIELD = {
  PrefFields.ON_START_GAME_YAMLS: EditablePreference(
    title="Default Game YAMLs",
    prefType=EditablePreference.Type.FILEPATH_LIST,
    explanation="Listed Game YAMLs will be automatically loaded into Azathoth"
                " when the program opens.",
    setButtonTitle="Select Default Game YAMLs",
    setButtonFiletypes=[('Game YAMLs', '*.yaml')],
    ),

  PrefFields.ON_START_WHEEL: EditablePreference(
    "Default Wheel",
    EditablePreference.Type.FILEPATH,
    "Listed Wheel will be automatically loaded into Azathoth when the program"
    " opens.",
    setButtonTitle="Select Default Azathoth Wheel",
    setButtonFiletypes=[('Azathoth Wheel', '*.yaml')],
    ),
  
  PrefFields.SILENCE_UPGRADE_CLEAR_WARNING: EditablePreference(
    "Silence Upgrade Clear Warning",
    EditablePreference.Type.BOOLEAN,
    "If enabled, silences and skips warnings when taking an action that would"
    " clear or change your selected upgrades, such as clearing or spinning"
    " new upgrades."),

  PrefFields.NEXT_SPIN_BEHAVIOR: EditablePreference(
    "Next Spin Behavior",
    EditablePreference.Type.MULTIPLE_CHOICE,
    "If set, skips the Spin button's prompt asking if you want to replace or"
    " add to any existing spins and performs the set behavior instead.",
    validChoices={
      MultipleChoice.NextSpinBehavior.REPLACE: "Always Replace",
      MultipleChoice.NextSpinBehavior.ADD: "Always Add",
    }
  ),

  PrefFields.WARN_ON_SAVE_OVERWRITE: EditablePreference(
    "Warn on Save Overwrite",
    EditablePreference.Type.BOOLEAN,
    "If enabled, requires confirmation before overwriting existing files when"
    " saving upgraded YAMLs."
  ),

  PrefFields.UPGRADE_HIGHLIGHT_COLOR: EditablePreference(
    "Upgrade Highlight Color",
    EditablePreference.Type.COLOR,
    "Describes the color used for newly-spun upgrades to distinguish them from"
    " other "
  ),

  PrefFields.DISABLE_BLINK: EditablePreference(
    "Disable Blink",
    EditablePreference.Type.BOOLEAN,
    "If enabled, Azathoth no longer blinks to confirm successful file saves."
  ),
}

class PreferencesEditor(tk.Toplevel):
  
  def __init__(self, parent, preferences):
    super().__init__()
    self.parent = parent
    self.preferences = preferences

    # Set up main window.
    self.geometry("600x400")
    self.title(f"Preferences Editor")
    self.iconbitmap(default=resources.getPath("img", "Thoth-t.ico"))
    self.resizable(False, False)

    # Registries of preference field name to its corresponding widgets.
    self.fieldToTitle = {}            # Title for preference
    self.fieldToSetButton = {}        # Button for setting preference
    self.fieldToDisplayLabel = {}     # Label for displaying preference's value
    self.fieldToDisplayLabelVar = {}  # Underlying variable powering said label
    self.fieldToExplainer = {}        # Explainer button for preference

    self.createUI()


  def getDisplayValue(self, field):
    '''Produces a display-ready string describing the current setting of the
    preference at the given field.
    '''
    pref = EDITABLES_BY_FIELD.get(field)

    if pref:
      rawValue = self.preferences.get(field)
      match pref.prefType:
        case EditablePreference.Type.BOOLEAN:
          # TODO: Consider cleaning up.  Checkboxes currently display no value.
          return "True" if rawValue else "False"
        case EditablePreference.Type.FILEPATH:
          return Path(rawValue).name
        case EditablePreference.Type.FILEPATH_LIST:
          return '\n'.join([Path(path).name for path in rawValue])
        case EditablePreference.Type.MULTIPLE_CHOICE:
          return (""
                  if rawValue is MultipleChoice.UNSPECIFIED
                  else pref.validChoices.get(rawValue))
        case EditablePreference.Type.COLOR:
          return rawValue
        case EditablePreference.Type.UNSPECIFIED:
          raise ValueError(f"Cannot display value for unrecognized preference"
                          f" type {pref.prefType}")
    raise ValueError(f"Did not recognize preference field {field}")


  def refreshLabel(self, field):
    '''Refreshes the display label associated with the given field to reflect
    its most recent value.
    '''
    if (sVar := self.fieldToDisplayLabelVar.get(field)):
      sVar.set(self.getDisplayValue(field))

      # Color labels are written in the given color.
      if EDITABLES_BY_FIELD[field].prefType == EditablePreference.Type.COLOR:
        if (displayLabel := self.fieldToDisplayLabel.get(field)):
          displayLabel.configure(foreground = self.preferences.get(field))


  def createFilepathButton(self, parent, field, title="", filetypes=None,
                           initialDir=None):
    '''Creates and returns a Button that sets and clears the single filepath
    stored in the given preference field.
    '''
    def updateFilepath():
      '''Helper function to open a file modal, save its result as a preference,
      and update the corresponding display label.
      '''
      filename = filedialog.askopenfilename(
          parent=parent,
          title=title,
          filetypes=filetypes,
          initialdir=initialDir)
      if filename:
        self.preferences.set(field, filename)

    def clearFilepath():
      '''Helper function to clear the associated field '''
      self.preferences.clear(field)

    return self.createAlternatingSetButton(
        parent, field, updateFilepath, clearFilepath)


  def createFilepathListButton(self, parent, field, title=None, filetypes=None,
                               initialDir=None):
    '''Creates and returns a Button that sets and clears a list of filepaths
    for the preference at given field.
    '''
    def updateFilepathList():
      '''Helper function to open a multi-file modal, save its result as a
      preference, and update the corresponding display label.
      '''
      filenames = filedialog.askopenfilenames(
          parent=parent,
          title=title,
          filetypes=filetypes,
          initialdir=initialDir)
      filenames = list(filenames)
      if filenames:
        self.preferences.set(field, filenames)

    def clearFilepathList():
      '''Helper function to clear the associated field '''
      self.preferences.clear(field)
    
    return self.createAlternatingSetButton(
        parent, field, updateFilepathList, clearFilepathList)


  def createValidChoicesSetButton(self, parent, field):
    '''Creates and returns a button that can clear or set a preference value
    from among a set of pre-defined valid choices.
    '''

    initialChoice = self.preferences.get(field)
    validChoices = EDITABLES_BY_FIELD[field].validChoices

    class MultipleChoiceDialog(Dialog):
      '''Custom dialog to present radio button choices from among a list of
      options specific to the relevant preference.
      '''

      def body(self, master):
        '''Constructs a stacked set of buttons describing the valid choices.'''
        self.choiceVar = tk.StringVar(master, initialChoice)
        for choice, choiceName in validChoices.items():
          tk.Radiobutton(master, variable=self.choiceVar, text=choiceName,
                          value=choice, indicatoron=False).pack(fill='x')
          

      def apply(self):
        '''Returns the ValidChoice value selected.'''
        self.result = self.choiceVar.get()

    def setChoice():
      '''Helper function to open a radio button selector for a list of valid
      choices.
      '''
      selector = MultipleChoiceDialog(self, "Select Preference")
      result = (selector.result
                if selector.result is not None
                else MultipleChoice.UNSPECIFIED)
      self.preferences.set(field, result)
      

    def clearChoice():
      '''Helper function to clear the associated field.'''
      self.preferences.clear(field)

    return self.createAlternatingSetButton(
      parent, field, setChoice, clearChoice)

  def createColorSelectorButton(self, parent, field):
    '''Creates and returns a Button that sets and clears a color for the
    preference at given field.
    '''
    def updateColor():
      '''Helper function to open a color selector, save its result as a
      preference, and update the corresponding display label.
      '''
      colorChooserResult = colorchooser.askcolor(
        parent=parent,
        title="Choose Color",
        color=self.preferences.get(field),
      )
      color = colorChooserResult[1]
      if color:
        self.preferences.set(field, color)

    def clearColor():
      '''Helper function to clear the associated field.'''
      self.preferences.clear(field)
    
    return self.createAlternatingSetButton(
        parent, field, updateColor, clearColor)


  def createAlternatingSetButton(self, parent, field, updateCommand, clearCommand):
    '''Creates and returns a button that alternates function between setting the
    preference at the given field and clearing it, refreshing relevant widgets.
    '''
    def updateAndRefresh():
      '''Runs the given update command, then refreshes relevant widgets.'''
      updateCommand()
      refresh()

    def clearAndRefresh():
      '''Runs the given clear command, then refreshes relevant widgets.'''
      clearCommand()
      refresh()

    setButton = tk.Button(parent)
    def refresh():
      '''When a preference has been set, the button's function is to clear it.
      When a preference is not set, the button's function is to set it.
      '''
      self.refreshLabel(field)
      if self.preferences.isDefault(field):
        setButton.configure(text="Set", command=updateAndRefresh)
      else:
        setButton.configure(text="Clear", command=clearAndRefresh)

    refresh()
    return setButton


  def createCheckbox(self, parent, field):
    '''Creates and returns a checkbox for the boolean preference with the given
    field.
    '''
    rawValue = self.preferences.get(field)
    iVar = tk.IntVar(parent, value = 1 if rawValue else 0)

    def updatePref():
      newVal = True if iVar.get() else False
      self.preferences.set(field, newVal)
    return tk.Checkbutton(parent, variable=iVar, command=updatePref)


  def toExplainer(self, parent, prefName, explanation):
    def explain():
      '''Pops up a message box displaying the given explanation.'''
      return messagebox.showinfo(
        title=prefName,
        message=explanation,
        icon='info',
        parent=parent
      )
    return tk.Button(parent, text="  ?  ", command=explain)


  def getInitialDir(self, field):
    '''Returns the preferred initial directory to use when setting the given
    field, if any. Note that this is not stored in our constants because the
    setting can be dynamic and stateful.
    '''
    match field:
      case PrefFields.ON_START_GAME_YAMLS:
        return self.preferences.get(PrefFields.LAST_GAME_YAMLS_FOLDER)
      case PrefFields.ON_START_WHEEL:
        return self.preferences.get(PrefFields.LAST_WHEEL_FOLDER)
      case _:
        return None


  def createPrefWidgets(self, field, layout):
    '''Creates and registers GUI widgets representing the given editable
    preference. These include:
      - The title of the preference
      - A button or checkbox to change a preference value
      - [Optional] A label describing the current preference
      - A button that explains what the preference means
    '''
    editable = EDITABLES_BY_FIELD.get(field)
    if not editable:
      raise ValueError(f"Did not recognize field {field} to create widgets.")
    
    # Create labels and associated StringVars first, as buttons refer to them.
    displayValueVar = tk.StringVar(layout, value=self.getDisplayValue(field))
    displayValue = tk.Label(layout, textvariable=displayValueVar,
                            justify="left", anchor="w")

    # Construct and associate the setting buttons.
    setButton = None
    match editable.prefType:
      case EditablePreference.Type.BOOLEAN:
        setButton = self.createCheckbox(layout, field)
        displayValue = None   # Checkboxes don't need a display value.
      case EditablePreference.Type.FILEPATH:
        setButton = self.createFilepathButton(
          layout, field,
          title=editable.setButtonTitle,
          filetypes=editable.setButtonFiletypes,
          initialDir=self.getInitialDir(field))
      case EditablePreference.Type.FILEPATH_LIST:
        setButton = self.createFilepathListButton(
          layout, field,
          title=editable.setButtonTitle,
          filetypes=editable.setButtonFiletypes,
          initialDir=self.getInitialDir(field))
      case EditablePreference.Type.MULTIPLE_CHOICE:
        setButton = self.createValidChoicesSetButton(layout, field)
      case EditablePreference.Type.COLOR:
        setButton = self.createColorSelectorButton(layout, field)
        displayValue.configure(foreground = self.preferences.get(field))
      case _:
        raise ValueError(f"Unsupported preference type {editable.prefType}")

    self.fieldToTitle[field] = tk.Label(layout, text=editable.title,
                                        font="Hultog", justify="left",
                                        anchor="w")
    self.fieldToSetButton[field] = setButton
    self.fieldToDisplayLabel[field] = displayValue
    self.fieldToDisplayLabelVar[field] = displayValueVar
    self.fieldToExplainer[field] = self.toExplainer(
      layout, editable.title, editable.explanation)
    


  def createUI(self):
    canvas = tk.Canvas(self, borderwidth=0, highlightthickness=0)
    scrollbar = tk.Scrollbar(self, command=canvas.yview)

    preferencesLayout = tk.Frame(canvas, borderwidth=0, highlightthickness=0)
    preferencesLayout.columnconfigure(0, minsize=50)
    preferencesLayout.pack()

    for i, field in enumerate(EDITABLES_BY_FIELD.keys()):
      titleRow = i * 2
      buttonRow = titleRow + 1
      preferencesLayout.grid_rowconfigure(buttonRow, minsize=25)
      self.createPrefWidgets(field, preferencesLayout)
      
      if (setButton := self.fieldToSetButton[field]):
        setButton.grid(row=titleRow, column=0)

      self.fieldToTitle[field].grid(row=titleRow, column=1, columnspan=3,
                                    sticky="w")
      if (displayValue := self.fieldToDisplayLabel[field]):
        displayValue.grid(row=buttonRow, column=1, columnspan=2, sticky='w')
      if (explainer := self.fieldToExplainer[field]):
        explainer.grid(row=titleRow, column=4, sticky="e")

    
    preferencesLayout.bind(
      "<Configure>",
      lambda e: canvas.configure(
        scrollregion=canvas.bbox("all")
      )
    )

    canvas.create_window((170,20), window=preferencesLayout, anchor='n')
    canvas.configure(yscrollcommand=scrollbar.set)

    # Set up mouse wheel scrolling on canvas.
    def scrollCanvas(event):
      canvas.yview_scroll(int(-1*(event.delta/120)), "units")
    canvas.bind('<Enter>',
                lambda _: canvas.bind_all("<MouseWheel>", scrollCanvas))
    canvas.bind('<Leave>',
                lambda _: canvas.unbind_all("<MouseWheel>"))

    scrollbar.pack(side="right", fill="y")
    canvas.pack(side="left", fill="both", expand=True)
