from data.preferences import Fields as PrefFields
from enum import Enum
from gui import resources
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox

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

  def __init__(self, title, prefType: Type, explanation, initialDir=None):
    self.title = title
    self.prefType = prefType
    self.explanation = explanation

EDITABLES_BY_FIELD = {
  PrefFields.ON_START_GAME_YAMLS: EditablePreference(
    "Default Game YAMLs",
    EditablePreference.Type.FILEPATH_LIST,
    'Listed Game YAMLs will be automatically loaded into Azathoth when the'\
    ' program opens.'
    ),

  PrefFields.ON_START_WHEEL: EditablePreference(
    "Default Wheel",
    EditablePreference.Type.FILEPATH,
    'Listed Wheel will be automatically loaded into Azathoth when the program'\
    ' opens.'),
  
  PrefFields.SILENCE_UPGRADE_CLEAR_WARNING: EditablePreference(
    "Silence Upgrade Clear Warning",
    EditablePreference.Type.BOOLEAN,
    'If enabled, silences and skips warnings when taking an action that would'\
    ' clear or change your selected upgrades, such as clearing or spinning'\
    ' new upgrades.'),

  PrefFields.WARN_ON_SAVE_OVERWRITE: EditablePreference(
    "Warn on Save Overwrite",
    EditablePreference.Type.BOOLEAN,
    "If enabled, requires confirmation before overwriting existing files when"\
    " saving upgraded YAMLs."
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
    self.iconbitmap(bitmap=resources.getPath("img", "Thoth-t.ico"))
    self.resizable(False, False)

    # Registry of preference field name to its corresponding label variable.
    self.fieldToLabelVar = dict()

    # Registry of preference field name to its corresponding setter button.
    self.fieldToSetButton = dict()

    self.createUI()


  def getDisplayValue(self, field):
    '''Produces a display-ready string describing the current setting of the
    preference at the given field.'''
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
        case EditablePreference.Type.UNSPECIFIED:
          raise ValueError(f"Cannot display value for unrecognized preference"
                          f" type {pref.prefType}")
    raise ValueError(f"Did not recognize preference field {field}")


  def refreshLabel(self, field):
    '''Refreshes the display label associated with the given field to reflect
    its most recent value.
    '''
    if (sVar := self.fieldToLabelVar.get(field)):
      sVar.set(self.getDisplayValue(field))


  def createFilepathButton(self, parent, field, initialDir=None):
    '''Creates and returns a Button that sets and clears the single filepath
    stored in the given preference field.
    '''
    def updateFilepath():
      '''Helper function to open a file modal, save its result as a preference,
      and update the corresponding display label.
      '''
      filename = filedialog.askopenfilename(
          parent=parent,
          title="Select Default Azathoth Wheel",
          filetypes=[('Azathoth Wheel', '*.yaml')],
          initialdir=initialDir)
      if filename:
        self.preferences.set(field, filename)

    def clearFilepath():
      '''Helper function to clear the associated field '''
      self.preferences.clear(field)

    return self.createAlternatingSetButton(
        parent, field, updateFilepath, clearFilepath)


  def createFilepathListButton(self, parent, field, initialDir=None):
    '''Creates and returns a Button that sets and clears a list of filepaths
    for the preference at given field.
    '''
    def updateFilepathList():
      '''Helper function to open a multi-file modal, save its result as a
      preference, and update the corresponding display label.
      '''
      filenames = filedialog.askopenfilenames(
          parent=parent,
          title="Select Default Game YAMLs",
          filetypes=[('Game YAMLs', '*.yaml')],
          initialdir=initialDir)
      filenames = list(filenames)
      if filenames:
        self.preferences.set(field, filenames)

    def clearFilepathList():
      '''Helper function to clear the associated field '''
      self.preferences.clear(field)
    
    return self.createAlternatingSetButton(
        parent, field, updateFilepathList, clearFilepathList)



  def createAlternatingSetButton(self, parent, field, updateCommand, clearCommand):
    '''Creates and returns a button that '''
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
      '''Refreshes the preference's set button and its label to reflect state.
      A set preference is clearable '''
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


  def createPrefWidgets(self, field, layout) -> tuple[
      tk.Label, tk.Button|tk.Checkbutton, tk.Label|None, tk.Button]:
    '''Creates, registers, and returns a pack of GUI widgets representing the
    given editable preference. These are:
      - The title of the preference
      - A button or checkbox to change a preference value
      - [Optional] A label describing the current preference
      - A button that explains what the preference means
    '''
    editable = EDITABLES_BY_FIELD.get(field)
    if not editable:
      raise ValueError(f"Did not recognize field {field} to create widgets.")

    title = tk.Label(layout, text=editable.title, font="Hultog", justify="left", anchor="w")

    setButton, explainer, displayValue = [None for _ in range(3)]
    
    # Create labels and associated StringVars first, as buttons refer to them.
    displayValueVar = tk.StringVar(layout, value=self.getDisplayValue(field))
    self.fieldToLabelVar[field] = displayValueVar
    displayValue = tk.Label(layout, textvariable=displayValueVar, justify="left", anchor="w")

    # Construct and associate the setting buttons.
    match editable.prefType:
      case EditablePreference.Type.BOOLEAN:
        setButton = self.createCheckbox(layout, field)
        displayValue = None   # Checkboxes don't need a display value.
      case EditablePreference.Type.FILEPATH:
        setButton = self.createFilepathButton(
          layout, field, initialDir=self.getInitialDir(field))
        self.fieldToSetButton[field] = setButton
      case EditablePreference.Type.FILEPATH_LIST:
        setButton = self.createFilepathListButton(
          layout, field, initialDir=self.getInitialDir(field))
        self.fieldToSetButton[field] = setButton
      case _:
        raise ValueError(f"Unsupported editable preference type {editable.prefType}")

    explainer = self.toExplainer(layout, editable.title, editable.explanation)

    return (title, setButton, displayValue, explainer)
    


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
      title, setButton, value, explainer = self.createPrefWidgets(field, preferencesLayout)
      
      if setButton:
        setButton.grid(row=titleRow, column=0)
      title.grid(row=titleRow, column=1, columnspan=3, sticky="w")
      if value:
        value.grid(row=buttonRow, column=1, columnspan=2)
      if explainer:
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
