# Data classes describing upgrades that you can make to YAMLs and the machinery
#   around their selection.

from enum import Enum


class Progression:
  '''Describes the progressive values produced by an upgrade, depending on how
  many times the upgrade has been selected.

  Attributes:
    Limit:      Explicit limit on how many times the upgrade can be selected.
    Values:     List of values corresponding to how many of the Upgrade you have.
                e.g. roll 1, receive values[0]; roll 2, receive values[1], &c.
    Increment:  Describes indefinite pattern of values from the last. If values
                has length 5, values[4]=7, and increment is 1, then rolling
                this upgrade 8 times results in a value of 10.

  Must include at least one of values or increment.  May include both.
  '''
  def __init__(self, limit=None, values=None, increment=None):
    self.limit = limit
    self.values = values
    self.increment = increment

  def __repr__(self):
    return f"limit: {self.limit}\nvalues: {self.values}\nincrement: {self.increment}"



class Upgrade:
  """Describes an upgrade that can be selected.

  Attributes:
    Type:         Type of upgrade. 
    YamlPath:     Path to where in the YAML the upgrade is located, if any.
    Progression:  Upgraded value to be added.
  """

  class Type(Enum):
    UNSPECIFIED = 0
    OVERRIDE = 1    # Overrides a setting that may exist in the base YAML.
    MANUAL = 2      # Manually-enforced change with no YAML change.
  
  def __init__(self, uniqueId="", type=Type.UNSPECIFIED, yamlPath=None, progression=None):
    self.uniqueId = uniqueId
    self.type = type
    self.yamlPath = yamlPath if yamlPath is not None else []
    self.progression = progression
  
  def __repr__(self) -> str:
    return self.uniqueId


class WeightedChoice:
  '''Describes a possible choice on a Wheel.

  Attributes:
    Name:             Name to display for this choice.
    Weight:           Integer weight for selection.  Summed across all choices.
    WheelResult:      If spins, rolls a new option from this sub-wheel.
    UpgradeResult:    If chosen, grants the described upgrade.
  '''
  def __init__(self, name, weight, wheelResult=None, upgradeResult=None):
    self.name = name
    self.weight = weight

    # Exactly one of these should be defined.
    self.wheelResult = wheelResult
    self.upgradeResult = upgradeResult


class Wheel:
  '''Describes a group of weighted choices that can be "spun" to make random
  selections.

  Attributes:
    DisplayName:  Name to display for this wheel.
    GameName:     Name of the game that this wheel describes.
    Choices:      List of choices that populate this Wheel's spinnable options.
  '''
  def __init__(self, displayName, gameName="", choices = None):
    self.displayName = displayName
    self.gameName = gameName
    self.choices = choices if choices is not None else []