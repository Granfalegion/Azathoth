from file.azathothConstants import Keys, UpgradeType
from file.azathothConstants import RECOGNIZED_PROGRESSION_MACROS

# map of all valid wheel Keys to the type of values permitted for them
VALID_WHEEL_KEYS_TO_ALLOWED_TYPES: dict[str, list] = {
  Keys.NAME: [str],
  Keys.GAME: [str],
  Keys.WEIGHT: [int],
  Keys.WHEEL: [list]
}

# map of all valid Upgrade Choice Keys to the type of values permitted for them
VALID_UPGRADE_CHOICE_KEYS_TO_ALLOWED_TYPES: dict[str, list] = {
  Keys.NAME: [str],
  Keys.WEIGHT: [int],
  Keys.UPGRADE: [dict],
}

# map of all valid Upgrade Keys to the type of values permitted for them
VALID_UPGRADE_KEYS_TO_ALLOWED_TYPES: dict[str, list] = {
  Keys.PATH: [str, list],
  Keys.PROGRESSION: [str, dict],
  Keys.TYPE: [str],
}

# map of all valid Progression Keys to the type of values permitted for them
VALID_PROGRESSION_KEYS_TO_ALLOWED_TYPES: dict[str, list] = {
  Keys.AT_MOST: [int],
  Keys.LIMIT: [int],
  Keys.VALUES: [int|str, list],  # Consider if there are other raw types here.
  Keys.INCREMENT: [int],
}


def _isUpgradeChoice(yaml):
  '''Returns true if the given YAML contains an upgrade.'''
  return Keys.UPGRADE in yaml


def _isWheel(yaml):
  '''Returns true if the given YAML contains a wheel.'''
  return Keys.WHEEL in yaml


def _validateKeysAndValues(yaml, validKeys):
  '''Validates that the given yaml only contains Keys in the given validKeys
  and that its associated values are of permitted types.
  '''

  for key, value in yaml.items():
    if key not in validKeys:
      raise ValueError(f"YAML contained unexpected key '{key}',"
                       f" only allows {list(validKeys.Keys())}")
    if not isinstance(value, tuple(validKeys[key])):
      raise ValueError(f"YAML contained unexpected value {value},"
                       f" must be of type {list(validKeys[key])}")


def _validateProgression(yaml):
  '''Validates that the given YAML describes a Progression, per Azathoth spec.
  '''

  if isinstance(yaml, str):
    if yaml in RECOGNIZED_PROGRESSION_MACROS:
      return _validateProgression(RECOGNIZED_PROGRESSION_MACROS[yaml])
    else:
      raise ValueError(f"Progression {yaml} not a recognized macro.")

  _validateKeysAndValues(yaml, VALID_PROGRESSION_KEYS_TO_ALLOWED_TYPES)

  if Keys.AT_MOST in yaml and Keys.LIMIT in yaml:
    raise ValueError(f"Progression {yaml} listed both {Keys.AT_MOST} and"
                     f" {Keys.LIMIT}, but only one is allowed.")

  if Keys.LIMIT in yaml and Keys.VALUES in yaml:
    if len(yaml[Keys.VALUES]) < yaml[Keys.LIMIT]:
      raise ValueError(f"Progression {yaml} listed more values than its"
                       f" limit of {yaml[Keys.LIMIT]} allows.")

  # TODO: Consider validating that, if present, `increment` and `atMost` allow
  #         for more rolls beyond values[-1].
  #       That said, I can see an argument for convenience's sake to allowing
  #         increments that may not get a chance to fire because you might edit
  #         the base value without wanting to care about restructuring the
  #         rest of the upgrade as well.

  if Keys.VALUES not in yaml and Keys.INCREMENT not in yaml:
    raise ValueError(f"Progression {yaml} has neither `values` nor `increment`."
                     " At least one must be given.")


def _validateUpgrade(yaml, game):
  '''Validates that the given YAML describes an Upgrade, per Azathoth spec.'''
  _validateKeysAndValues(yaml, VALID_UPGRADE_KEYS_TO_ALLOWED_TYPES)

  if not game:
    raise ValueError(f"Upgrade {yaml} does not belong to a listed game.")

  if Keys.TYPE in yaml and yaml[Keys.TYPE] == UpgradeType.MANUAL:
    if Keys.PATH in yaml:
      raise ValueError(f"Manual upgrade {yaml} contained a yaml path!"
                       f" {yaml[Keys.PATH]}")
  
  if Keys.PROGRESSION not in yaml:
    raise ValueError(f"Upgrade {yaml} does not contain a progression.")

  _validateProgression(yaml[Keys.PROGRESSION])


def _validateUpgradeChoice(yaml, game):
  '''Validates that the given YAML describes a Weighted Choice containing an
  Upgrade, per Azathoth spec.
  '''

  _validateKeysAndValues(yaml, VALID_UPGRADE_CHOICE_KEYS_TO_ALLOWED_TYPES)

  if Keys.UPGRADE not in yaml:
    raise ValueError(f"Upgrade choice {yaml} contained no upgrade!")  
  if Keys.WEIGHT not in yaml:
    raise ValueError(f"Upgrade choice {yaml} contained no weight!")
  
  _validateUpgrade(yaml[Keys.UPGRADE], game)


def _validateWheel(yaml, game=""):
  '''Validates that the given sub-YAML matches the Azathoth scheme, that all
  Keys are expected and valid and lead to expected value types.

  Recursively checks all sub-YAMLs within as well.
  '''

  _validateKeysAndValues(yaml, VALID_WHEEL_KEYS_TO_ALLOWED_TYPES)

  if game and Keys.GAME in yaml and game != yaml[Keys.GAME]:
    raise ValueError(f"Wheel {yaml} listed a game {yaml[Keys.GAME]} but was"
                     f" already downstream of game {game}!")

  if Keys.NAME not in yaml and Keys.GAME not in yaml:
    raise ValueError(f"Wheel {yaml} has no name!")

  # Validate all downstream choices.
  gameToPassDown = yaml.get(Keys.GAME, game)
  for choice in yaml[Keys.WHEEL]:
    if _isWheel(choice) and _isUpgradeChoice(choice):
      raise ValueError(f"Wheel choice {yaml} has both wheel and upgrade!")
    elif _isWheel(choice):
      _validateWheel(choice, gameToPassDown)
    elif _isUpgradeChoice(choice):
      _validateUpgradeChoice(choice, gameToPassDown)
    else:
      raise ValueError(f"Wheel choice {yaml} contained no wheel nor upgrade!")




def validateAzathothYaml(yaml):
  '''Performs full validation of the given Azathoth YAML.

  This includes verifying Azathoth Wheel structure, presence of required
  fields, and permitted typing of given values.
  '''

  if not _isWheel(yaml):
    raise ValueError("Azathoth Wheel file must begin with a wheel.")

  _validateWheel(yaml)
