import collections.abc
from data.upgrades import *
import yaml as pyyaml

# Standard indent of two spaces.
INDENT = "  "


def _indent(level):
  '''Produces an indent of the given level, based on the constant INDENT.'''
  return ''.join([INDENT for _ in range(level)])


def _getValue(upgrade: Upgrade, num: int):
  '''Returns the value output by this upgrade when it has been selected a
  number of times.
  '''

  if num <= 0:
    raise ValueError(f"Upgrade {upgrade} was rolled <{num}> times, but"
                     f" requested anyway!")

  progression = upgrade.progression
  if not progression:
    raise ValueError(f"Upgrade {upgrade} has no value to set. Please provide a"
                      " Progression.")
  if progression.limit and num > progression.limit:
    raise ValueError(f"Upgrade {upgrade} exceeded its given limit of "
                     f" {progression.limit}!")
    
  # First check if we have a values list to base this on...
  if values:= progression.values:
    # If num is in the values list, report it directly.
    if num <= len(values):
      return progression.values[num-1]
        
    # Otherwise, go to the end of the values and calculate increment therefrom.
    else:
      lastValue = progression.values[-1]
      numIncrements = num-len(values)
      return lastValue + (numIncrements * progression.increment)
        
  # ... but in the absence of a values list, just count up from 0.
  else:
    # NOTE: This makes the assumption that the progression is for numbers.
    #       This _should_ be assured by validation, but I wanted to note it.
    return num * progression.increment


def toMetaYamlManual(upgradeResults: dict):
  '''Constructs and returns the contents of a meta.yaml file representing the
  given UpgradeResults. meta.yaml is a simple solution that hard-overrides the
  indicated settings of all instances of the given games in the Archipelago.

  Azathoth uses this information to produce a summary that describes upgrades
  that have been selected in one place.
  '''

  # Alphabetize upgrades by their YAML path, ensuring upgrades are grouped.
  alphaItems = sorted(upgradeResults.items(), key=lambda x: tuple(x[0].yamlPath))

  output = ""      # yaml to output
  lastPath = []    # Track the path you're on.
  for upgrade, count in alphaItems:
    currentPath = upgrade.yamlPath

    # Manual upgrades receive special treatment because they don't conform to the
    #   tree-like patterns we assume for yamlPath.
    # We can assume that they contain a yamlPath of just their game, but they
    #   should otherwise be written as indented comments so the YAML at least
    #   mentions them for later reference.
    if upgrade.type == Upgrade.Type.MANUAL:
      gameTitle = currentPath[0]

      # Start the game block if you're not already in it.
      if not lastPath or lastPath[0] != gameTitle:
        output += f"{gameTitle}:\n"

      # Then write the upgrade as a comment.
      output += f"{_indent(1)}# MANUAL - {upgrade}: {_getValue(upgrade, count)}\n"

    else:

      onTheSamePath = True
      for i, step in enumerate(currentPath):
        if onTheSamePath and i < len(lastPath) and step == lastPath[i]:
          continue
        else:
          onTheSamePath = False

        # And middle steps should just state themselves.
        if i < len(currentPath) - 1:
          output += f"{_indent(i)}{step}:\n"

        # Final steps give a value.
        else:
          output += f"{_indent(i)}{step}: {_getValue(upgrade, count)}\n"

    lastPath = currentPath

  return output


def _getValueAtPath(yamlPath, yaml):
  '''Returns the value defined at the given path in the given yaml, if any.'''
  if not yamlPath:
    return yaml
  
  next = yamlPath[0]
  if next in yaml:
    _getValueAtPath(yamlPath[1:], yaml[next])
  else:
    return None


def _toNestedDict(path, value):
  '''Creates and returns a nested dict where each step in the given path is a
  nested key. The final key is assigned the given value.
  '''
  if not path:
    raise ValueError(f"Received empty path.")

  if len(path) == 1:
    return {path[0]: value}
  return {
    path[0]: _toNestedDict(path[1:], value)
  }



def _deepUpdate(target, update):
  """Updates the target dictionary to include the given update. Differs from
  the extant .update() method to include nested field support.
  """
  for key, value in update.items():
    if isinstance(value, collections.abc.Mapping):
      target[key] = _deepUpdate(target.get(key, {}), value)
    else:
      target[key] = value
  return target



def _applyUpgradeToYaml(upgrade, count, yaml):
  '''Updates the given YAML to reflect the given upgrade when it has been
  selected the given times. Updates YAML to include the indicated fields,
  if absent.
  '''

  newValue = _getValue(upgrade, count)
  update = _toNestedDict(upgrade.yamlPath, newValue)
  _deepUpdate(yaml, update)


def toUpgradedYaml(upgradeResults: dict, originalYaml):
  '''Creates a copy of the given YAML applies any relevant upgrades in the
  given upgrade dict to it, then returns the copy.
  '''

  # Make a copy of the given yaml to update.
  yaml = pyyaml.safe_load(pyyaml.safe_dump(originalYaml))
  
  for upgrade, count in upgradeResults.items():
    game = upgrade.yamlPath[0]
    if game not in yaml:
      continue

    if upgrade.type == Upgrade.Type.MANUAL:
      continue

    _applyUpgradeToYaml(upgrade, count, yaml)

  return yaml
