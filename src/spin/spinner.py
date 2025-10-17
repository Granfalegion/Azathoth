from data.upgrades import *
import random


def getLimitForUpgrade(upgrade: Upgrade, currentResults):
  '''Returns the number of times you can still select a particular upgrade,
  given how many selections have already been made in the given results, or
  -1 if unlimited.
  '''
  existingUses = currentResults.get(upgrade, 0)

  # Either a limit is explicitly defined...
  if upgrade.progression and upgrade.progression.limit:
    return upgrade.progression.limit - existingUses
  
  # ... or it is inferred from the number of values without increment...
  elif upgrade.progression and upgrade.progression.increment is None:
    try:
      return len(upgrade.progression.values) - existingUses
    except:
      print(f"Encountered invalid  {upgrade}")
      return -1
    
  # ... but if there's an increment and no limit, we can go forever.
  else:
    return -1



def getLimitForWheel(wheel: Wheel, currentResults={}):
  '''Returns the number of times you can still spin a wheel, or -1 if
  unlimited.
  '''

  limitedLeft = 0

  # Iterate through choices on the wheel.
  # If any choices can be rolled indefinitely, so can this.
  for choice in wheel.choices:
    if choice.upgradeResult:
      if (upgradeLimit := getLimitForUpgrade(choice.upgradeResult, currentResults)) == -1:
        return -1
      else:
        limitedLeft += upgradeLimit

    elif choice.wheelResult:
      if (wheelLimit := getLimitForWheel(choice.wheelResult, currentResults)) == -1:
        return -1
      else:
        limitedLeft += wheelLimit

  return limitedLeft


def _getLimitForChoice(choice: WeightedChoice, currentResults):
  '''Returns the number of times you could still select a particular choice, or
  -1 if unlimited.
  '''
  if upgrade:= choice.upgradeResult:
    return getLimitForUpgrade(upgrade, currentResults)
  elif wheel:= choice.wheelResult:
    return getLimitForWheel(wheel, currentResults)
  else:
    raise ValueError(f"Weighted Choice {choice} doesn't have any results!")


def _spinWheel(wheel: Wheel, currentResults) -> WeightedChoice:
  '''Returns a WeightedChoice from the given Wheel, given the current results.
  '''
  validChoices = []

  # First identify which choices are still allowed.
  for choice in wheel.choices:
    if _getLimitForChoice(choice, currentResults) != 0:
      validChoices.append(choice)

  # IF THERE ARE NO VALID CHOICES, FAIL OUT.
  if not validChoices:
    raise ValueError(f"Tried to spin wheel {wheel.displayName} with no valid choices!")

  # Pair all valid choices with their weights.
  weights = [choice.weight for choice in validChoices]

  choice = random.choices(population=validChoices, weights=weights)[0]
  return choice



def spinUpgrades(wheel: Wheel, numSpins: int):
  '''Returns Upgrades produced by spinning the given Wheel {spins} times, as a
  dict mapping Upgrades to the number of times rolled.

  Raises ValueError if the given Wheel cannot produce {spins} spins.
  '''

  # First check that the given wheel can support X spins.
  wheelLimit = getLimitForWheel(wheel)
  if getLimitForWheel(wheel) < numSpins and wheelLimit != -1:
    raise ValueError(f"Wheel {wheel.displayName} has a limit of {wheelLimit}"
                     f" and cannot spin {numSpins} times.")
  
  # Roll your upgrades, tracking how often they each get picked.
  currentResults = {}

  # TODO: This is recursive. Make it iterative to support GUI-hooked spinners?
  #       A GUI-hooked Spinner that prompts at every level probably needs to
  #       instead allow user prompts and display results and things.
  #       Probably a GUISpinner inherits this and overloads this method though.
  for _ in range(numSpins):
    choice: WeightedChoice = _spinWheel(wheel, currentResults)
    while(choice.upgradeResult is None):
      if choice.wheelResult:
        wheelResult = choice.wheelResult
        choice = _spinWheel(wheelResult, currentResults)
      else:
        raise ValueError(f"WeightedChoice {choice.name} has no result!")
    upgrade = choice.upgradeResult
    currentResults[upgrade] = currentResults.get(upgrade, 0) + 1
  return currentResults
