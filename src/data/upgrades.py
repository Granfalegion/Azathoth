# Data classes describing upgrades that you can make to YAMLs and the machinery
#   around their selection.

from enum import Enum

UNLIMITED = -1

class Progression:
  '''Describes the progressive values produced by an upgrade, depending on how
  many times the upgrade has been selected.

  Attributes:
    values:     List of values corresponding to how many of the Upgrade you have.
                e.g. roll 1, receive values[0]; roll 2, receive values[1], &c.
                Converted to tuple internally for immutability.

    increment:  If given, enables upgrade to be selected further beyond the 
                N values listed in the values attribute. After reaching the Nth
                value, subsequent selections add increment to the total value.
                
                For example: If values=[0,1,2,4,7], and increment=1, then
                selecting this upgrade 8 times results in a final value of 10.

    stopAt:     If given, increment-driven selections are only available until
                this value is reached. If an increment would take the upgrade
                past this value, it instead stops at this value.

                For example: If values=[3], increment=2, and stopAt=10, then
                this upgrade can be selected 5 times, yielding [3,5,7,9,10].

    limit:      If given, explicit limit on how many times this upgrade can be
                selected.

  Must include at least one of values or increment.
  '''
  def __init__(self, values=None, increment=None, stopAt=None, limit=None):
    self.values = values if values == None else tuple(values)
    self.increment = increment
    self.stopAt = stopAt
    self.limit = limit

    self._finalize()

  def __repr__(self):
    return f"values: {self.values}\nincrement: {self.increment}\nstopAt: {self.stopAt}"

  def __eq__(self, other):
    return (isinstance(other, Progression)
      and self.values == other.values
      and self.increment == other.increment
      and self.stopAt == other.stopAt)

  def __hash__(self):
    return hash((self.values, self.increment, self.stopAt))


  def _getStopAt(self):
    '''Returns the last reachable value of this upgrade. If the upgrade can be
    selected indefinitely, returns None.
    '''
    if self.increment == None:
      return len(self.values or [])

    if self.limit in (UNLIMITED, None):
      return None
    
    lastValue = self.values[-1] if self.values else 0
    remainingIncrements = self.limit - len(self.values or [])
    return lastValue + (remainingIncrements * self.increment)


  def _getSpinLimit(self) -> int:
    '''Returns the maximum number of times this upgrade can be selected.
    Returns -1 if it can be selected indefinitely.
    '''
    numValues = len(self.values or [])
    if self.increment:
      if self.stopAt == None:
        return UNLIMITED
      
      finalValue = self.values[-1] if self.values else 0
      remainingValue = self.stopAt - finalValue
      remainingIncrements = remainingValue / self.increment
      if remainingIncrements < 0:
        raise ValueError(f"Progression {self} has an unreachable stopAt.")
      
      numValues += -(remainingValue // -self.increment)  # Ceiling divide.
    
    return numValues
  

  def _finalize(self):
    '''Derive unprovided end conditions once all parameters are initialized.'''
    if self.limit == None and self.stopAt != None:
      self.limit = self._getSpinLimit()
    if self.stopAt == None and self.limit != None:
      self.stopAt = self._getStopAt()



class Upgrade:
  """Describes an upgrade that can be selected.

  Attributes:
    name:         Display name for upgrade.
    type:         Type of upgrade.
    yamlPath:     Path to where in the YAML the upgrade is located, if any.
    progression:  Upgraded value to be added.
  """

  class Type(Enum):
    UNSPECIFIED = 0
    OVERRIDE = 1    # Overrides a setting that may exist in the base YAML.
    MANUAL = 2      # Manually-enforced change with no YAML change.

  def __init__(
      self, name="", type=Type.UNSPECIFIED, yamlPath=None, progression=None):

    self.name = name
    self.type = type
    self.yamlPath = tuple(yamlPath or [])
    self.progression = progression

  def __eq__(self, other):
    return (isinstance(other, Upgrade)
      and self.name == other.name
      and self.type == other.type
      and self.yamlPath == other.yamlPath
      and self.progression == other.progression)
  
  def __hash__(self):
    return hash((self.name, self.type, self.yamlPath, self.progression))

  def __repr__(self) -> str:
    return self.name


class WeightedChoice:
  '''Describes a possible choice on a Wheel.

  Attributes:
    name:             Name to display for this choice.
    weight:           Integer weight for choice. Probability of making this
                        choice is weight over the sum of all weights in this
                        wheel.
    cost:             Integer cost for choice. Selecting this choice costs
                        this many points.
    wheelResult:      If present, the choice leads to the described sub-wheel
                        and must be spun again.
    upgradeResult:    If present, the choice grants the described upgrade.
  '''
  def __init__(self, name, weight, cost, wheelResult=None, upgradeResult=None):
    self.name = name
    self.weight = weight
    self.cost = cost

    # Exactly one of these should be defined.
    self.wheelResult = wheelResult
    self.upgradeResult = upgradeResult

  def __eq__(self, other):
    return (isinstance(other, WeightedChoice)
      and self.name == other.name
      and self.weight == other.weight
      and self.cost == other.cost
      and self.wheelResult == other.wheelResult
      and self.upgradeResult == other.upgradeResult)
  
  def __hash__(self):
    return hash((self.name, self.weight, self.cost,
                 self.wheelResult, self.upgradeResult))

  def __repr__(self) -> str:
    return self.name


class Wheel:
  '''Describes a group of weighted choices that can be "spun" to make random
  selections.

  Attributes:
    displayName:  Name to display for this wheel.
    gameName:     Name of the game that this wheel describes.
    choices:      List of choices that populate this Wheel's spinnable options.
  '''
  def __init__(self, displayName, gameName="", choices = None):
    self.displayName = displayName
    self.gameName = gameName
    self.choices = tuple(choices or [])

  def __eq__(self, other):
    return (isinstance(other, Wheel)
      and self.displayName == other.displayName
      and self.gameName == other.gameName
      and self.choices == other.choices)
  
  def __hash__(self):
    return hash((self.displayName, self.gameName, self.choices))

  def __repr__(self) -> str:
    return self.displayName
  