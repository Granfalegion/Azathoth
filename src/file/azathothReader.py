from copy import deepcopy
from data.upgrades import Progression, Upgrade, Wheel, WeightedChoice
from file import azathothValidator, yamlReader
from file.azathothConstants import Defaults, Keys, PROGRESSION_FIELD_ALIASES, PROGRESSION_MACROS, UpgradeType

def _getDisplayName(yaml):
  '''Returns the display name to use for the given YAML object.'''
  if Keys.NAME in yaml:
    return yaml[Keys.NAME]
  elif Keys.GAME in yaml:
    return yaml[Keys.GAME]
  else:
    return ""


def _yamlToProgression(yaml):
  '''Produces a Progression from the given YAML representation of one.'''

  if isinstance(yaml, str):
    if yaml in PROGRESSION_MACROS:
      return _yamlToProgression(PROGRESSION_MACROS[yaml])
    else:
      raise ValueError(f"Progression macro '{yaml}' not recognized.")

  # If any fields are aliased, replace them and reprocess.
  if yaml.keys() & PROGRESSION_FIELD_ALIASES.keys():
    return _yamlToProgression(
      {PROGRESSION_FIELD_ALIASES.get(k, k): v for k,v in yaml.items()})

  increment = yaml.get(Keys.INCREMENT)
  stopAt = yaml.get(Keys.STOP_AT)
  spinLimit = yaml.get(Keys.SPIN_LIMIT)

  # Allow for singleton values; just wrap them in a list.
  values = yaml.get(Keys.VALUES)
  if values is not None and not isinstance(values, list):
    values = [values]

  # Allow for singleton display values; just wrap them in a list.
  displayValues = yaml.get(Keys.DISPLAY_VALUES)
  if displayValues is not None and not isinstance(displayValues, list):
    displayValues = [displayValues]

  return Progression(values=values, displayValues=displayValues,
                     increment=increment, stopAt=stopAt, limit=spinLimit)


def _yamlToUpgrade(yaml, game="", choiceName=""):
  '''Produces an initial Upgrade structure directly reflecting the given YAML.

  Presumes that values have already been validated.
  '''
  yamlPath = yaml.get(Keys.PATH)

  # Singleton yaml paths are permitted, but turn them into a list.
  if yamlPath and not isinstance(yamlPath, list):
    yamlPath = [yamlPath]
  elif not yamlPath:
    yamlPath = []

  # Ensure that every Upgrade's yamlPath begins with its game.
  if len(yamlPath) == 0 or yamlPath[0] != game:
    yamlPath.insert(0, game)

  type = Upgrade.Type.OVERRIDE
  if yaml.get(Keys.TYPE, 0) == UpgradeType.MANUAL:
    type = Upgrade.Type.MANUAL

  progression = _yamlToProgression(yaml[Keys.PROGRESSION])

  return Upgrade(choiceName, type, yamlPath, progression)


def _yamlToWheel(yaml, game=""):
  '''Produces an initial Wheel structure directly reflecting the given YAML,
  propagating game field to all downstream upgrades.

  Presumes that values have already been validated.
  '''
  game = yaml.get(Keys.GAME, game)
  displayName = _getDisplayName(yaml)
  wheel = Wheel(displayName)

  if game:
    wheel.gameName = game

  # Recursively parse and add each weighted choice.
  wheelChoices = []
  for choice in yaml[Keys.WHEEL]:
    choiceName = _getDisplayName(choice)
    choiceWeight = choice.get(Keys.WEIGHT, Defaults.WEIGHT)

    if Keys.WHEEL in choice:
      choiceWheel = _yamlToWheel(choice, game)
      choiceCost = choice.get(Keys.COST, Defaults.WHEEL_COST)
      weightedChoice = WeightedChoice(
        choiceName, choiceWeight, cost=choiceCost, wheelResult=choiceWheel)
      wheelChoices.append(weightedChoice)

    elif Keys.UPGRADE in choice:
      game = choice.get(Keys.GAME, game)  # UpgradeChoice can set game too.
      choiceUpgrade = _yamlToUpgrade(choice[Keys.UPGRADE], game, choiceName)
      choiceCost = choice.get(Keys.COST, Defaults.UPGRADE_COST)
      weightedChoice = WeightedChoice(
        choiceName, choiceWeight, cost=choiceCost, upgradeResult=choiceUpgrade)
      wheelChoices.append(weightedChoice)

  wheel.choices = tuple(wheelChoices)
  return wheel


def getValidYaml(azathothYamlFilePath):
  '''Opens a YAML file at the given path, parses it, validates contents, and
  returns it.
  '''
  azathothYaml = yamlReader.readToYaml(azathothYamlFilePath)
  azathothValidator.validateAzathothYaml(azathothYaml)
  return azathothYaml


def azathothToWheel(azathothYamlFilePath=None, azathothYaml=None):
  '''Opens a YAML file at the given path, parses it, validates contents, and
  converts it to a Wheel ready for use with a Spinner.
  '''
  yaml = azathothYaml if azathothYaml else getValidYaml(azathothYamlFilePath)
  if yaml == None:
    raise ValueError("Must provide one of YAML or a filepath to one.")
  return _yamlToWheel(deepcopy(yaml))
