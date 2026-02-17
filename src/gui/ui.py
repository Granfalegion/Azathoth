from data.preferences import Preferences, Fields as PrefFields
from data.upgrades import Wheel
from file import azathothReader, upgrader, writer, yamlReader
from gui import resources
from gui.preferencesEditor import PreferencesEditor
from gui.upgradeChooser import UpgradeChooser
import os
from pathlib import Path
from spin import spinner
import tkinter as tk
from tkinter import filedialog, messagebox, PhotoImage

# Prefix prepended to output upgraded YAML files. Prevents overwrite of inputs.
UPGRADE_PREFIX = "upgraded-"

# Fake upper limit to apply to spinbox to= values.
INF_LIMIT = 999999999999

# Placeholder Wheel variable for when unset.
# TODO: Re-examine using EMPTY_WHEEL over a more explicit None.
#       This stems from my wanting to distinguish "Failed to upload something"
#       from "Haven't uploaded anything yet"
EMPTY_WHEEL = Wheel("")

class keys():
  """Namespace for keys in collected dicts of UI widgets."""
  gamesButton = "gameButton"
  wheelButton = "wheelButton"
  preferencesButton = "preferencesButton"
  exitButton = "exitButton"

  spinButton = "spinButton"
  clearButton = "clearButton"
  saveButton = "saveButton"

  bg = "backgroundImage"
  ok = "okImage"
  warn = "warnImage"
  no = "badImage"

  azathothBlock = "azathoth"
  azathothVersion = "version"


def requireWheel(fn):
  """Decorator function to require the presence of a loaded wheel."""
  def inner(*args, **kwargs):
    self = args[0]
    if not self.appData.wheel or self.appData.wheel == EMPTY_WHEEL:
      self.errorModal("No Wheel Loaded",
        "You must first load a Wheel before taking this action.")
      return
    else:
      return fn(*args, **kwargs)
  return inner


def requireGames(fn):
  """Decorator function to require the presence of loaded games."""
  def inner(*args, **kwargs):
    self = args[0]
    if not self.appData.gameYamls:
      self.errorModal("No Games Loaded",
        "You must first load Game YAMLs before taking this action.")
      return
    else:
      return fn(*args, **kwargs)
  return inner


def warnOnUpgradeOverride(fn):
  """Decorator function to warn about clearing upgrade counts."""
  def inner(*args, **kwargs):
    self = args[0]
    silenced = self.preferences.get(PrefFields.SILENCE_UPGRADE_CLEAR_WARNING)
    if self.chooser and self.chooser.hasAnyUpgrades() and not silenced:
      saidYes = messagebox.askyesno("Really overwrite upgrades?",
        "This action will replace all upgrades you have already set.")
      if not saidYes:
        return
    return fn(*args, **kwargs)
  return inner


class AppData():
  """Data Bundle to track data as we load it."""

  # TODO: Calling this `gameYamls` when that's only part of it is kinda dumb.

  # gameYamls -> List of tuples: (gameYaml, gameYamlFileName)
  # wheel -> Azathoth Wheel object.
  def __init__(self, gameYamls = None, wheel = None):
    super().__init__()
    self.gameYamls = gameYamls
    self.wheel = wheel



class AzathothApp(tk.Tk):
  """App class managing Azathoth UI and stateful data."""
  def __init__(self, parent, version, *args, **kwargs):
    self.parent = parent
    self.version = version
    self.frame = tk.Frame(self.parent)
    self.appData = AppData()
    self.images = {}
    self.buttons = {}
    self.chooser = None
    self.parent.protocol("WM_DELETE_WINDOW", self.onClose)

  
  # TODO: It's not clear to me _why_ this must be in its own function exactly,
  #       but every time I tried to initialize PhotoImages as part of __init__
  #       nothing worked. Instead, I'm using this as a prerequisite method that
  #       runs at the head of run(), but leverages existing variables in the
  #       top level class.
  def loadImages(self):
    """Loads and initializes the images in the app."""
    
    # Background image.
    bg = PhotoImage(file = resources.getPath("img", "thoth-w.png"))

    # Status Icons for file upload.
    ok = PhotoImage(file = resources.getPath("img", "ok-sm.png"))
    warn = PhotoImage(file = resources.getPath("img", "warn-sm.png"))
    no = PhotoImage(file = resources.getPath("img", "no-sm.png"))

    self.images = {
      keys.bg: bg,
      keys.ok: ok,
      keys.warn: warn,
      keys.no: no,
    }

  
  def loadMainButtons(self):
    """Initializes the buttons in the app."""
    bgLabel = tk.Label(self.parent, image=self.images[keys.bg])
    bgLabel.place(x=0,y=0,relwidth=1, relheight=1, anchor='nw', )

    loadGamesButton = tk.Button(self.parent, text = "Load Game YAMLs",
                                compound = "left",
                                command = self.loadGamesFiles)

    loadWheelButton = tk.Button(self.parent, text = "Load Upgrade Wheel",
                                compound = "left",
                                command = self.loadWheelFile)
    
    preferencesButton = tk.Button(self.parent, text = "Preferences",
                                compound = "left",
                                command = self.loadPreferencesEditor)
    exitButton = tk.Button(self.parent, text = "Exit", command = self.onClose)
    
    self.buttons.update({
      keys.gamesButton: loadGamesButton,
      keys.wheelButton: loadWheelButton,
      keys.preferencesButton: preferencesButton,
      keys.exitButton: exitButton,
    })

    loadGamesButton.place(x=5, y=5)
    loadWheelButton.place(x=5, y=35)
    preferencesButton.place(x=5, y=340)
    exitButton.place(x=5, y=370)


  def loadPreferences(self):
    self.preferences = Preferences(version=self.version)

    try:
      self.preferences.load()
    except FileNotFoundError:
      # This is fine. Preferences files must be created once, after all.
      pass
    except ValueError as e:
      # Bad value in preferences file.
      self.errorModal("Failed to load preferences",
                      f"Could not parse contents as YAML: {e}")

    # Take initialization actions dictated by preferences.    
    if (startGameYamlFilenames := self.preferences.get(PrefFields.ON_START_GAME_YAMLS)):
      self.loadGamesFiles(filenames=startGameYamlFilenames)
    if (startWheelFilename := self.preferences.get(PrefFields.ON_START_WHEEL)):
      self.loadWheelFile(filename=startWheelFilename)


  def onClose(self):
    try:
      self.preferences.close()
    except OSError:
      self.errorModal("Unsupported OS",
                      "Cannot save preferences for unrecognized OS."
                      " Please report to maintainers.")
    self.parent.destroy()


  def refresh(self):
    """Updates UI to reflect the app's current state."""
    hasGames = self.appData.gameYamls
    hasWheel = self.appData.wheel and self.appData.wheel != EMPTY_WHEEL

    # Set games select button icon
    if self.appData.gameYamls == None:
      self.buttons[keys.gamesButton].configure(image = None)
    elif self.appData.gameYamls == []:
      self.buttons[keys.gamesButton].configure(image = self.images[keys.no])
    else:
      self.buttons[keys.gamesButton].configure(image = self.images[keys.ok])
    
    # Set wheel select button icon
    if self.appData.wheel == None:
      self.buttons[keys.wheelButton].configure(image = None)
    elif self.appData.wheel == EMPTY_WHEEL:
      self.buttons[keys.wheelButton].configure(image = self.images[keys.no])
    else:
      self.buttons[keys.wheelButton].configure(image = self.images[keys.ok])

    # Enable/disable save button, if any, if both data types are present.
    saveEnabled = hasGames and hasWheel
    if keys.saveButton in self.buttons:
      self.buttons[keys.saveButton].configure(
        state=tk.NORMAL if saveEnabled else tk.DISABLED)

  
  def run(self):
    """Starts UI."""
    self.loadImages()
    self.loadMainButtons()
    self.loadPreferences()
    
    self.parent.mainloop()

  
  @warnOnUpgradeOverride
  def loadWheelFile(self, filename=None):
    """Opens a new dialog to fetch an indicated Azathoth wheel, parses and
    validates it, then opens an UpgradeChooser reflecting that data state.
    """
    if not filename:
      filename = filedialog.askopenfilename(
                  title="Select Azathoth Wheel",
                  filetypes=[('Azathoth Wheel', '*.yaml')],
                  initialdir=self.preferences.get(PrefFields.LAST_WHEEL_FOLDER) or None)
    if filename:
      try:
        self.appData.wheel = azathothReader.azathothToWheel(filename)
        self.openChooser()
        wheelFolder = Path(filename).parent.as_posix()
        self.preferences.set(PrefFields.LAST_WHEEL_FOLDER, wheelFolder)
      except ValueError as e:
        # TODO: Consider if there's a cleaner way to signal failure and clear.
        self.appData.wheel = EMPTY_WHEEL
        if self.chooser:
          self.chooser.clearObjects()
        self.errorModal("Failed to load Wheel", e)
      finally:
        self.refresh()

  
  def loadGamesFiles(self, filenames=[]):
    """Opens a new dialog to fetch an indicated set of game YAMLs, parses them,
    then sets them to the current data state.
    """
    if not filenames:
      filenames = filedialog.askopenfilenames(
                    title="Select Game YAMLs",
                    filetypes=[('Game YAMLs', '*.yaml')],
                    initialdir=self.preferences.get(PrefFields.LAST_GAME_YAMLS_FOLDER) or None)
    if filenames:
      gameYamls = []
      try:
        for filename in filenames:
          gameYaml = yamlReader.readToYaml(filename)
          gameYamls.append((gameYaml, filename))
        self.appData.gameYamls = gameYamls
        if filenames:
          gameYamlsFolder = Path(filenames[-1]).parent.as_posix()
          self.preferences.set(PrefFields.LAST_GAME_YAMLS_FOLDER, gameYamlsFolder)
      except Exception as e:
        self.appData.gameYamls = []
        self.errorModal("Failed to load game YAMLs", e)
      finally:
        self.refresh()


  @requireWheel
  @requireGames
  def saveUpgrades(self, upgradeResults):
    """Copies the game YAMLs stored in AppData, upgrades them according to the
    given upgrade results, and saves them to a designated output folder.
    """

    # Don't save files without upgrades.
    if not upgradeResults:
      self.errorModal("No Upgrades",
                      "Cannot save upgrades if no upgrades are selected.")
      return

    # Validate that all reported upgrades belong to loaded games.
    gameTitlesToUpgrade = {upgrade.yamlPath[0] for upgrade in upgradeResults.keys()}
    gameYamlKeys = set(sum(
      [list(gameYaml[0].keys()) for gameYaml in self.appData.gameYamls],
      []))
    if missingGames := gameTitlesToUpgrade.difference(gameYamlKeys):
      reallyProceed = messagebox.askyesnocancel("Game YAMLs Missing",
                      f"Attempting to save upgrades for games not included in"
                      " your loaded game YAMLs. These upgrades will have no"
                      " effect.\n\n"
                      "Really proceed?",
                      detail=f"Missing YAMLs: {', '.join(missingGames)}",
                      icon='error')
      if not reallyProceed:
        return
    

    # Ask where to save, then save upgraded YAMLs and the meta summary.
    saveDirectory = filedialog.askdirectory(
        title="Select folder to save upgraded files",
        initialdir=Path(self.preferences.get(PrefFields.LAST_SAVE_FOLDER)) or None)
    if saveDirectory:

      # TODO: Add preference to silence it, but warn about save overwrites.

      for gameYaml, gameFilePath in self.appData.gameYamls:
        upgradedYaml = self.withAzathothHeader(
          upgrader.toUpgradedYaml(upgradeResults, gameYaml))

        # Write a new yaml with the upgrades included.
        filename = Path(gameFilePath).name
        upgradedFilename = UPGRADE_PREFIX + filename

        upgradedYamlFilePath = os.path.join(saveDirectory, upgradedFilename)
        writer.writeYamlToFile(upgradedYaml, upgradedYamlFilePath)

      summaryYaml = upgrader.toSummaryYamlStr(
        upgradeResults, version=self.version)
      summaryYamlFilePath = os.path.join(saveDirectory, "azathothSummary.yaml")
      writer.writeToFile(summaryYaml, summaryYamlFilePath)
      self.preferences.set(PrefFields.LAST_SAVE_FOLDER, saveDirectory)

      # TODO: Add a pop-up modal here that confirms that [X] saves succeeded or
      #   explains what went wrong.
      # TODO: Consider making this more idempotent by creating all of the saves
      #   and their target locations at once and then saving the group after.


  def withAzathothHeader(self, yaml):
    '''Returns a copy of the given YAML with an Azathoth header prepended.'''

    # Only this complicated so we can force to appear early/first in the dict.
    headedDict = {}
    if self.version:
      headedDict[keys.azathothBlock] = {
        keys.azathothVersion: self.version,
      }
    headedDict.update(yaml)
    return headedDict


  @warnOnUpgradeOverride
  def clearUpgrades(self):
    self.chooser.zeroCounters()

  
  @requireWheel
  @warnOnUpgradeOverride
  def spinNewUpgrades(self, numSpins):
    """Spins the loaded wheel the indicated number of times, then updates the
    UpgradeChooser to reflect the results.
    """

    wheelLimit =  spinner.getLimitForWheel(self.appData.wheel) # type: ignore
    if wheelLimit != -1 and wheelLimit < numSpins:
      self.errorModal("Too Many Spins",
                      f"Current wheel only supports {wheelLimit} spins, but"
                      f" {numSpins} were requested.")
      return

    upgradeResults = spinner.spinUpgrades(self.appData.wheel, numSpins) # type: ignore
    self.chooser.applyUpgrades(upgradeResults) # type: ignore


  
  @requireWheel
  def openChooser(self):
    """Opens a new window that displays all the upgrades detected along with
    counters that allow you to select how many times each particular upgrade
    has been selected.
    """
    allUpgrades = self.getAllUpgrades()
    if allUpgrades:
      chooserPanel = tk.Frame(self.parent, borderwidth=0, highlightthickness=0)
      chooserPanel.place(x=300, y=0, relwidth=0.5, relheight=1)

      self.chooser = UpgradeChooser(chooserPanel, borderwidth=0, highlightthickness=0, height=400, width=400)
      self.chooser.loadUpgrades(self.getAllUpgrades())
      self.chooser.place(x=0, y=0, relwidth=1, relheight=0.90)

      wheelLimit = spinner.getLimitForWheel(self.appData.wheel) # type: ignore
      spinEntry = tk.Spinbox(chooserPanel, from_=0, increment=1,
                             to=wheelLimit if wheelLimit >= 0 else INF_LIMIT,
                             # Validation prevents entering non-numbers.
                             validate="key",
                             validatecommand=(
                               self.parent.register(
                                 lambda P: P.isdigit() or P == ""
                               ),
                               "%P"),
                             )
      spinEntry.place(x=10, y=375, width=40)

      spinButton = tk.Button(chooserPanel, text="Spin",
                             command=lambda:self.spinNewUpgrades(int(spinEntry.get())))
      spinButton.place(x=60, y=372, width=60)

      clearButton = tk.Button(chooserPanel, text="Clear",
                              command=self.clearUpgrades)
      clearButton.place(x=140, y=372, width=60)
      
      saveButton = tk.Button(chooserPanel, text = "Save",
                            command=lambda:self.saveUpgrades(self.chooser.getUpgradeResults()))
      saveButton.place(x=220, y=372, width=60)

      self.buttons.update({
        keys.spinButton: spinButton,
        keys.clearButton: clearButton,
        keys.saveButton: saveButton,
      })


  
  @requireWheel
  def getAllUpgrades(self):
    """Returns a list of all upgrades contained in the current AppData's wheel."""

    def getAllUpgradesFromWheel(wheel: Wheel):
      """Helper function extracting all upgrades in a wheel and its subwheels."""
      allUpgrades = []
      for choice in wheel.choices:
        if choice.wheelResult:
          allUpgrades = allUpgrades + getAllUpgradesFromWheel(choice.wheelResult)
        elif choice.upgradeResult:
          allUpgrades.append(choice.upgradeResult)
      return allUpgrades

    return getAllUpgradesFromWheel(self.appData.wheel)


  def errorModal(self, title, text):
    """Brings up an error modal."""
    return messagebox.showwarning(
      title=title,
      message=text,
      icon='error',
      parent=self.parent
    )
  
  def loadPreferencesEditor(self):
    '''Loads Preferences Editor as a toplevel sub-window with forced focus.'''
    editor = PreferencesEditor(self.parent, self.preferences)
    editor.grab_set()
    editor.focus()


def start(version):
  """Initializes the main UI for Azathoth and starts running it."""
  root = tk.Tk()
  root.geometry("600x400")
  root.title(f"Azathoth v{version}")
  root.iconbitmap(bitmap=resources.getPath("img", "Thoth-t.ico"))  # Set icon.
  root.resizable(False, False)  # Disable window resizing
  
  app = AzathothApp(root, version)
  app.run()
