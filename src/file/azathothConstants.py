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


'''Mapping of shorthand macros to common Progressions that they represent.'''
RECOGNIZED_PROGRESSION_MACROS = {
  "ONE_PER": Progression(increment=1),
  "UNIQUE": Progression(values=[1]),
}
