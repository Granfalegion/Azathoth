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
    # NOTE(gran): This assumes that existingUses cannot be higher than limit.
    #             Some odd behaviors emerge if that somehow manages to occur.
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


def getMinCostForWheel(wheel: Wheel, currentResults=None,
                       overrideWeights=None):
  '''Returns the minimum cost for any still-selectable choices on the given
  wheel, given what's been selected already.'''

  if currentResults == None:
    currentResults = {}
  if overrideWeights == None:
    overrideWeights = {}

  minCost = None
  for choice in wheel.choices:

    # Skip maxed-out upgrade choices.
    if (choice.upgradeResult and 
        getLimitForUpgrade(choice.upgradeResult, currentResults) == 0):
      continue

    # Skip zero-weight choices.
    if (choice.upgradeResult and
        overrideWeights.get(choice, choice.weight) == 0):
      continue

    choiceCost = (choice.cost if choice.upgradeResult
                  else getMinCostForWheel(choice.wheelResult, currentResults))

    if choiceCost != None:
      minCost = choiceCost if minCost == None else min(minCost, choiceCost)
  return minCost


def couldSelect(choice, currentResults, budget, overrideWeights):
  '''Returns true if you could make the selected choice given what choices have
  already been selected, the available cost budget, and the operating weights.
  '''

  if (upgrade := choice.upgradeResult):
    return (choice.cost <= budget
            and getLimitForUpgrade(upgrade, currentResults) != 0
            and overrideWeights.get(choice, 1) > 0)

  if (wheel := choice.wheelResult):
    minWheelCost = getMinCostForWheel(wheel, currentResults, overrideWeights)
    return minWheelCost != None and minWheelCost <= budget


def _spinWheel(wheel, currentResults, budget, overrideWeights):
  '''Randomly makes a weighted selection of choices from the given wheel,
  given already-made selections and the available cost budget. If any choices
  are present in the given dictionary of overrideWeights, its corresponding
  value is used as its weight instead.
  '''
  validChoices = [choice for choice in wheel.choices
                  if couldSelect(choice, currentResults, budget, overrideWeights)]
  if not validChoices:
    return None

  # Pair all valid choices with their weights.
  weights = [overrideWeights.get(choice, choice.weight)
             for choice in validChoices]
  choice = random.choices(population=validChoices, weights=weights)[0]
  return choice


def spinUpgrades(wheel: Wheel, spinBudget: int, existingResults=None,
                 overrideWeights=None):
  '''Randomly selects upgrades by repeatedly spinning the given Wheel and
  deducting each selection's cost from the given budget until no more upgrades
  can be selected. Can optionally be given a baseline dict of results that have
  already been selected and return results added to those.

  Returns results as a dict mapping Upgrades to the number of times selected.
  '''

  # Roll your upgrades, tracking how often they each get picked.
  currentResults = {} if existingResults is None else existingResults
  weights = {} if overrideWeights is None else overrideWeights

  # TODO: This is recursive. Make it iterative to support GUI-hooked spinners?
  #       A GUI-hooked Spinner that prompts at every level probably needs to
  #       instead allow user prompts and display results and things.
  #       Probably a GUISpinner inherits this and overloads this method though.
  while (choice := _spinWheel(wheel, currentResults, spinBudget, weights)):
    
    while(choice.upgradeResult is None):
      if (wheelResult := choice.wheelResult):
        choice = _spinWheel(wheelResult, currentResults, spinBudget, weights)

    upgrade, cost = choice.upgradeResult, choice.cost
    currentResults[upgrade] = currentResults.get(upgrade, 0) + 1
    spinBudget -= cost

  # TODO: Bolting this into a tuple feels inelegant. Create a better data
  #       structure for returned results.
  return currentResults, spinBudget