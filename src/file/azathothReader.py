from data.upgrades import Progression, Upgrade, Wheel, WeightedChoice
from file import azathothValidator, yamlReader
from file.azathothConstants import Keys, RECOGNIZED_PROGRESSION_MACROS, UpgradeType


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
    if yaml in RECOGNIZED_PROGRESSION_MACROS:
      return _yamlToProgression(RECOGNIZED_PROGRESSION_MACROS[yaml])
    else:
      raise ValueError(f"Progression macro '{yaml}' not recognized.")

  atMost = yaml.get(Keys.AT_MOST)
  limit = yaml.get(Keys.LIMIT)
  increment = yaml.get(Keys.INCREMENT)

  # Allow for singleton values; just wrap them in a list.
  values = yaml.get(Keys.VALUES)
  if values is not None and not isinstance(values, list):
    values = [values]

  # If `increment` and `atMost` are given in the absence of `limit`,
  #   calculate and set the implied limit.
  if Keys.INCREMENT in yaml:
    if Keys.LIMIT not in yaml and Keys.AT_MOST in yaml:
      numValues = len(values or [])
      lastValue = values[-1] if numValues > 0 else 0
      remainingIncrements = (atMost - lastValue)/increment
      limit = numValues + remainingIncrements
  
  return Progression(limit, values, increment)



def _yamlToUpgrade(yaml, game="", upgradeName=""):
  '''Produces an initial Upgrade structure directly reflecting the given Wheel.

  Presumes that values have already been validated.
  '''
  yamlPath = yaml.get("path")

  # Singletons yaml paths are permitted, but turn them into a list.
  if yamlPath and not isinstance(yamlPath, list):
    yamlPath = [yamlPath]
  elif not yamlPath:
    yamlPath = []
  assert(isinstance(yamlPath, list))

  # Ensure that every Upgrade's yamlPath begins with its game.
  if len(yamlPath) == 0 or yamlPath[0] != game:
    yamlPath.insert(0, game)

  type = Upgrade.Type.OVERRIDE
  if yaml.get(Keys.TYPE, 0) == UpgradeType.MANUAL:
    type = Upgrade.Type.MANUAL

  progression = _yamlToProgression(yaml[Keys.PROGRESSION])

  return Upgrade(upgradeName, type, yamlPath, progression)


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
  for choice in yaml[Keys.WHEEL]:
    choiceName = _getDisplayName(choice)
    choiceWeight = choice.get(Keys.WEIGHT, 1)

    if Keys.WHEEL in choice:
      choiceWheel = _yamlToWheel(choice, game)
      weightedChoice = WeightedChoice(
        choiceName, choiceWeight, wheelResult=choiceWheel)
      wheel.choices.append(weightedChoice)

    elif Keys.UPGRADE in choice:
      choiceUpgrade = _yamlToUpgrade(choice[Keys.UPGRADE], game, choiceName)
      weightedChoice = WeightedChoice(
        choiceName, choiceWeight, upgradeResult=choiceUpgrade)
      wheel.choices.append(weightedChoice)

  return wheel



def azathothToWheel(azathothYamlFilePath):
  '''Opens a YAML file at the given path, parses it, validates contents, and
  converts it to a Wheel ready for use with a Spinner.
  '''
  azathothYaml = yamlReader.readToYaml(azathothYamlFilePath)
  azathothValidator.validateAzathothYaml(azathothYaml)
  return _yamlToWheel(azathothYaml)