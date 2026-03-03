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
  SPIN_LIMIT = "spinLimit"
  VALUES = "values"
  INCREMENT = "increment"
  STOP_AT = "stopAt"

  # Outdated Keys
  AT_MOST = "atMost"  # Replaced by STOP_AT in v0.2.3
  LIMIT = "limit"     # Replaced by SPIN_LIMIT in v0.2.3


class UpgradeType:
  '''Constants for expected special values in the Azathoth scheme.'''
  MANUAL = "manual"


class ProgressionMacro:
  '''Constants for expected Progression Macros in the Azathoth scheme.'''
  UNIQUE = "UNIQUE"
  ONE_PER = "ONE_PER"


# Mapping of shorthand macros to Progression YAMLs that they represent.
PROGRESSION_MACROS = {
  # Macros can map either to YAMLs that can be parsed as Progressions or even
  # to other macros as aliases.
  "ONE_PER": {Keys.INCREMENT: 1},
  "UNIQUE": {Keys.VALUES: 1},
}

# Mapping of outdated Progression fields to their replacements.
PROGRESSION_FIELD_ALIASES = {
  Keys.AT_MOST: Keys.STOP_AT,
  Keys.LIMIT: Keys.SPIN_LIMIT,
}