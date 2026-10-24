from data.preferences import Fields as PrefFields
from file import upgrader
from gui.images import keys as imageKeys
from gui.uiConstants import Colors
from spin import spinner
import tkinter as tk

class UpDownCounter(tk.Frame):
  """Frame comprising a numeric label flanked by up and down increment
  buttons.
  """
  def __init__(self, parent, upperLimit=None, lowerLimit=None, startVal=0,
               *args, **kwargs):
    super().__init__(parent, *args, **kwargs)
    self.parent = parent
    self.upperLimit = upperLimit
    self.lowerLimit = lowerLimit

    self.counter = tk.IntVar(self, startVal)
    self.downButton = tk.Button(self, text="-",
                                command=lambda: self.increment(-1))
    self.counterLabel = tk.Label(self, textvariable=self.counter)
    self.upButton = tk.Button(self, text="+",
                              command=lambda: self.increment(1))
    
    self.downButton.grid(row=0, column=0)
    self.counterLabel.grid(row=0, column=1)
    self.upButton.grid(row=0, column=2)

    self.refresh()

  
  def increment(self, num):
    """Adds the given amount to the counter IntVar."""
    self.set(self.get() + num)
    self.refresh()

  
  def set(self, num):
    """Passes set(n) requests down to the counter IntVar."""
    self.counter.set(num)


  def get(self):
    """Pass get() requests down to the counter IntVar."""
    return self.counter.get()


  def refresh(self):
    """Refreshes the counter's UI to reflect current state."""
    currentVal = self.counter.get()

    self.downButton.configure(
      state=tk.DISABLED if currentVal == self.lowerLimit else tk.NORMAL)
    self.upButton.configure(
      state=tk.DISABLED if currentVal == self.upperLimit else tk.NORMAL)


class UpgradeCounter():
  """Representation of an Upgrade's WeightedChoice and its corresponding
  widgets in the upgrade chooser interface.
  """
  def __init__(self, choice, gridRow, nameLabel, choiceCounter, valueLabel,
               weightCounter):
    self.choice = choice
    self.gridRow = gridRow

    self.nameLabel = nameLabel
    self.choiceCounter = choiceCounter
    self.valueLabel = valueLabel
    self.color = Colors.UPGRADE_DEFAULT

    self.choiceCounter.counter.trace_add('write', self.refresh)

    self.weightCounter = weightCounter


  def refresh(self, *args):
    '''Update widgets' state to reflect newly-changed counter value.'''

    # Update Value Label
    if numUpgrades := self.get():
      upgradedValue = upgrader.getValue(self.choice.upgradeResult, numUpgrades,
                                        useDisplayValues=True)
      upgradedText = str(upgradedValue)
      if upgradedText.isnumeric():
        # Numeric upgrades use an arrow to distinguish count and value.
        upgradedText = f"=> {upgradedText}"
      self.valueLabel.configure(text=upgradedText)
    else:
      # Make invisible
      self.valueLabel.configure(text="")

    # Update color.
    self.choiceCounter.counterLabel.configure(fg=self.color)
    self.valueLabel.configure(fg=self.color)

    self.choiceCounter.refresh()


  def destroy(self):
    """Destroys all objects contained by the counter."""
    self.nameLabel.destroy()
    self.choiceCounter.destroy()
    self.valueLabel.destroy()
    self.weightCounter.destroy()


  def get(self):
    """Gets the internal counter variable."""
    return self.choiceCounter.get()


  def getWeight(self):
    """Gets the weight counter variable."""
    return self.weightCounter.get()


  def set(self, value):
    """Sets the internal choice counter variable to the given value."""
    self.choiceCounter.set(value)


  def setWeight(self, weight):
    """Sets the internal weight counter variable to the given value."""
    self.weightCounter.set(weight)


  def setColor(self, color=Colors.UPGRADE_DEFAULT):
    """Sets the color to use for displaying the counter value. If no color is
    given, reverts to its default.
    """
    self.color = color



class UpgradeChooser(tk.Frame):
  """Class containing subframe listing upgrades all at once."""

  def __init__(self, parent, preferences, images, *args, **kwargs):
    super().__init__(parent, *args, **kwargs)
    self.parent = parent
    self.preferences = preferences
    self.images = images

    # Dict mapping upgrade to corresponding UpgradeCounter widget collection.
    self.choiceToUpgradeCounter = {}

    # Dict mapping row to its relevant game label and weight icon.
    self.gameLabels = {}
    self.weightIcons = {}


  def clearObjects(self):
    """Clears all widgets that may already be contained in the chooser."""
    for upgradeCounter in self.choiceToUpgradeCounter.values():
      upgradeCounter.destroy()
    for gameLabel in self.gameLabels.values():
      gameLabel.destroy()
    for weightIcon in self.weightIcons.values():
      weightIcon.destroy()

    self.upgradeCountersByUpgrade = {}
    self.gameLabels = {}
    self.weightIcons = {}


  def zeroCounters(self):
    """Zeroes out all upgrade counters."""
    for upgradeCounter in self.choiceToUpgradeCounter.values():
      upgradeCounter.set(0)
      upgradeCounter.setColor()
      upgradeCounter.refresh()

  
  def hasAnyUpgrades(self):
    """Returns whether any of the upgrade counters have a positive count."""
    for upgradeCounter in self.choiceToUpgradeCounter.values():
      if upgradeCounter.get() > 0:
        return True
    return False

  
  def loadUpgrades(self, allUpgradeChoices):
    """Loads in a set of possible upgrade choices, creating widgets to
    represent them.
    """
    canvas = tk.Canvas(self, borderwidth=0, highlightthickness=0)
    scrollbar = tk.Scrollbar(self, command=canvas.yview)

    upgradeLayout = tk.Frame(canvas, borderwidth=0, highlightthickness=0)
    upgradeLayout.grid_columnconfigure(3, minsize=50)   # Minimize UI-thrashing
    upgradeLayout.pack()
    
    if allUpgradeChoices:

      # Track these conditions as we iterate through the upgrade list.
      # Exact row may differ depending on inserted headers.
      currentRow = 0
      currentGame = ""

      for choice in allUpgradeChoices:
        upgrade = choice.upgradeResult
        game = upgrade.yamlPath[0]

        if currentGame != game:
          # TODO: Add an icon here to indicate whether this game is loaded.
          gameLabel = tk.Label(upgradeLayout, text=game, font="Hultog")
          self.gameLabels[currentRow] = gameLabel

          weightIcon = tk.Label(upgradeLayout,
                                image=self.images.get(imageKeys.weight))
          self.weightIcons[currentRow] = weightIcon # TODO: Singleton label.

          currentRow = currentRow + 1
          currentGame = game

        # Create representative widgets for each upgrade.
        upgradeLabel = tk.Label(upgradeLayout, text=choice.name, width=24)

        upperLimit = spinner.getLimitForUpgrade(upgrade, {})
        upDownCounter = UpDownCounter(upgradeLayout,
                                      upperLimit if upperLimit >= 0 else None,
                                      lowerLimit=0)

        upgradeValue = tk.Label(upgradeLayout, text="", width=8)

        weightCounter = UpDownCounter(upgradeLayout,
                                      upperLimit=None,
                                      lowerLimit=0,
                                      startVal=choice.weight)

        upgradeCounter = UpgradeCounter(choice, currentRow, upgradeLabel,
                                        upDownCounter, upgradeValue,
                                        weightCounter)
        self.choiceToUpgradeCounter[choice] = upgradeCounter

        currentRow = currentRow + 1
    
    upgradeLayout.bind(
      "<Configure>",
      lambda e: canvas.configure(
        scrollregion=canvas.bbox("all")
      )
    )

    canvas.create_window((100,100), window=upgradeLayout, anchor='n')
    canvas.configure(yscrollcommand=scrollbar.set)

    # Set up mouse wheel scrolling on canvas.
    def scrollCanvas(event):
      canvas.yview_scroll(int(-1*(event.delta/120)), "units")
    canvas.bind('<Enter>',
                lambda _: canvas.bind_all("<MouseWheel>", scrollCanvas))
    canvas.bind('<Leave>',
                lambda _: canvas.unbind_all("<MouseWheel>"))

    scrollbar.pack(side="right", fill="y")
    canvas.pack(side="left", fill="both", expand=True)


  def refresh(self):
    """Updates the various widgets to account for current app state."""

    for row, gameLabel in self.gameLabels.items():
      gameLabel.grid(row=row, column=1, columnspan=3)

    for row, weightIcon in self.weightIcons.items():
      if self.preferences.get(PrefFields.ENABLE_CUSTOM_WEIGHTS):
        weightIcon.grid(row=row, column=0)
      else:
        weightIcon.grid_forget()

    for counter in self.choiceToUpgradeCounter.values():
      row = counter.gridRow
      counter.nameLabel.grid(row=row, column=1)
      counter.choiceCounter.grid(row=row, column=2)
      counter.valueLabel.grid(row=row, column=3)
      if self.preferences.get(PrefFields.ENABLE_CUSTOM_WEIGHTS):
        counter.valueLabel.configure(width=10)
        counter.weightCounter.grid(row=row, column=0)
      else:
        counter.valueLabel.configure(width=8)
        counter.weightCounter.grid_forget()

  
  def applyUpgrades(self, upgradeResults):
    """Updates the Chooser UI to reflect the given selected upgrades."""
    upgradedColor = self.preferences.get(PrefFields.UPGRADE_HIGHLIGHT_COLOR)
    for choice, counter in self.choiceToUpgradeCounter.items():
      oldVal = counter.get()
      newVal = upgradeResults.get(choice.upgradeResult, 0)
      counterColor = (upgradedColor
                          if oldVal != newVal and newVal > 0
                          else Colors.UPGRADE_DEFAULT)

      counter.set(newVal)
      counter.setColor(counterColor)
      counter.refresh()

  
  def getUpgradeResults(self):
    """Returns a dict counting how many times each choice is selected."""
    upgradeResults = {}

    for counter in self.choiceToUpgradeCounter.values():
      upgradeCount = int(counter.get() or 0)
      if upgradeCount > 0:
        upgradeResults[counter.choice.upgradeResult] = upgradeCount

    return upgradeResults


  def getChoiceWeights(self):
    """Returns a dict of Choice to integer weight as set by chooser weight
    counters. If weight counters are not enabled, returns None.
    """
    if not self.preferences.get(PrefFields.ENABLE_CUSTOM_WEIGHTS):
      return None

    return {
      choice: int(counter.weightCounter.counter.get() or 0)
          for choice, counter in self.choiceToUpgradeCounter.items()
    }
