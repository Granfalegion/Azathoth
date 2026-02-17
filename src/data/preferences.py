from file import writer, yamlReader
from pathlib import Path
import sys

# File navigation constants
APPLICATION_AUTHOR = "Granfalegion"
APPLICATION_NAME = "Azathoth"
PREFERENCES_FILENAME = "preferences.yaml"

# Preference field names.
class Fields:
  VERSION = "version"
  ON_START_GAME_YAMLS = "on_start_game_yamls"
  ON_START_WHEEL = "on_start_wheel"
  LAST_GAME_YAMLS_FOLDER = "last_game_yamls_folder"
  LAST_WHEEL_FOLDER = "last_wheel_folder"
  LAST_SAVE_FOLDER = "last_save_folder"
  IGNORE_AZATHOTH_SUMMARY = "ignore_azathoth_summary"
  SILENCE_UPGRADE_CLEAR_WARNING = "silence_upgrade_clear_warning"
  WARN_ON_SAVE_OVERWRITE = "warn_on_save_overwrite"
  DISABLE_BLINK = "disable_blink"

# Default values used for preference fields.
DEFAULTS = {
  Fields.VERSION: "",
  Fields.ON_START_GAME_YAMLS: [],
  Fields.ON_START_WHEEL: "",
  Fields.LAST_GAME_YAMLS_FOLDER: "",
  Fields.LAST_WHEEL_FOLDER: "",
  Fields.LAST_SAVE_FOLDER: "",
  Fields.IGNORE_AZATHOTH_SUMMARY: False,
  Fields.SILENCE_UPGRADE_CLEAR_WARNING: False,
  Fields.WARN_ON_SAVE_OVERWRITE: False,
  Fields.DISABLE_BLINK: False,
}

class Preferences():
  '''Configuration and preferences settings, stored in a YAML file in your OS'
  typical application data folder.
  '''
  
  def __init__(self, version):
    self.version = version
    self.config = {}
    self.originalConfig = {}


  def get(self, field):
    '''Returns the preference in the given field, or its default if unset.'''
    if field not in DEFAULTS:
      raise ValueError(f"Cannot get unrecognized preferences field {field}")
    return self.config.get(field, DEFAULTS[field])
  

  def set(self, field, newValue):
    '''Either sets the field to new value, or removes it if same as default.'''
    if field not in DEFAULTS:
      raise ValueError(f"Cannot set unrecognized preferences field {field}")
    if not isinstance(newValue, type(DEFAULTS[field])):
      raise ValueError(f"Cannot set preferences field {field} to {newValue},"
                       f" expected type {type(DEFAULTS[field])}")

    if newValue != DEFAULTS[field]:
      self.config[field] = newValue
    else:
      self.clear(field)


  def clear(self, field):
    '''Clears the field from preferences, effectively setting it to default.'''
    self.config.pop(field, None)


  def isDefault(self, field):
    '''Returns true if the current field is set to its field default.'''
    if field not in DEFAULTS:
      raise ValueError(f"Cannot query unrecognized preferences field {field}")
    return self.get(field) == DEFAULTS[field]


  def load(self):
    '''Attempts to load preferences from standard storage location.'''
    self.config: dict = yamlReader.readToYaml(_preferencesFilePath()) or dict()
    self.originalConfig: dict = dict(self.config)  # Unclear if deep copy.


  def isDirty(self):
    return self.config != self.originalConfig


  def close(self):
    '''Handles on-close actions for preferences, e.g. saving changes.'''

    # Nothing to save if not dirty.
    if self.isDirty():
      # TODO: Consider finding a way to sort this, as with OAML.
      self.config[Fields.VERSION] = self.version  # Update version on save.
      self._save()


  def _save(self):
    '''Saves preferences to file.'''
    _getAzathothDataDirectory().mkdir(parents=True, exist_ok=True)
    writer.writeYamlToFile(self.config, _preferencesFilePath())


# TODO: Should these bits move into the file package maybe?

def _preferencesFilePath() -> Path:
  return _getAzathothDataDirectory() / PREFERENCES_FILENAME


def _getAzathothDataDirectory() -> Path:
  '''Returns directory under which Azathoth application data can be stored.'''
  return _getOsDataDirectory() / APPLICATION_AUTHOR / APPLICATION_NAME


def _getOsDataDirectory() -> Path:
  """
  Returns directory under which general application data can be stored.

  For Windows: C:/Users/<USER>/AppData/Roaming
  For macOS: ~/Library/Application Support
  For Linux: ~/.local/share
  """

  home = Path.home()

  if sys.platform == "win32":
    return home / "AppData" / "Roaming"
  elif sys.platform == "darwin":  # MacOS
    return home / "Library" / "Application Support"
  elif sys.platform == "linux":
    return home / ".local" / "share"
  else:
    raise(OSError(f"Unrecognized platform {sys.platform}."))
