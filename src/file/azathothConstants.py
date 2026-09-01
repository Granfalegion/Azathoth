class Keys:
  '''Constants for expected keys in the Azathoth scheme.'''
  NAME = "name"
  GAME = "game"
  WEIGHT = "weight"
  COST = "cost"
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
  DEPRECATED_AT_MOST = "atMost"  # Replaced by STOP_AT in v0.2.3
  DEPRECATED_LIMIT = "limit"     # Replaced by SPIN_LIMIT in v0.2.3


class Defaults:
  '''Default values for omittable YAML fields'''
  WEIGHT = 1
  UPGRADE_COST = 1
  WHEEL_COST = 0


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
  Keys.DEPRECATED_AT_MOST: Keys.STOP_AT,
  Keys.DEPRECATED_LIMIT: Keys.SPIN_LIMIT,
}