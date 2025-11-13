from data.upgrades import Progression

class Keys:
  '''Constants for expected keys in the Azathoth scheme.'''
  NAME = "name"
  GAME = "game"
  WEIGHT = "weight"
  WHEEL = "wheel"
  UPGRADE = "upgrade"
  PATH = "path"
  PROGRESSION = "progression"
  TYPE = "type"
  AT_MOST = "atMost"
  LIMIT = "limit"
  VALUES = "values"
  INCREMENT = "increment"


class UpgradeType:
  '''Constants for expected special values in the Azathoth scheme.'''
  MANUAL = "manual"


class ProgressionMacro:
  '''Constants for expected Progression Macros in the Azathoth scheme.'''
  UNIQUE = "UNIQUE"
  ONE_PER = "ONE_PER"


# Mapping of shorthand macros to Progression YAMLs that they represent.
RECOGNIZED_PROGRESSION_MACROS = {
  # Macros can map either to YAMLs that can be parsed as Progressions or even
  # to other macros as aliases.
  "ONE_PER": {Keys.INCREMENT: 1},
  "UNIQUE": {Keys.VALUES: 1},
}
