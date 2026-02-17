from file import upgrader
from spin import spinner
import tkinter as tk

class UpDownCounter(tk.Frame):
  """Frame comprising a numeric label flanked by up and down increment
  buttons.
  """
  def __init__(self, parent, limit, *args, **kwargs):
    super().__init__(parent, *args, **kwargs)
    self.parent = parent
    self.limit = limit

    self.counter = tk.IntVar(self, 0)
    self.downButton = tk.Button(self, text="-",
                                command=lambda: self.increment(-1))
    self.counterLabel = tk.Label(self, textvariable=self.counter)
    self.upButton = tk.Button(self, text="+",
                              command = lambda: self.increment(1))
    
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
      state=tk.DISABLED if currentVal == 0 else tk.NORMAL)
    self.upButton.configure(
      state=tk.DISABLED if currentVal == self.limit else tk.NORMAL)


class UpgradeCounter():
  """Representation of a particular Upgrade and its corresponding widgets in
  the upgrading counting interface.
  """
  def __init__(self, upgrade, label: tk.Label, upDownCounter: UpDownCounter, upgradeValue: tk.Label):
    self.upgrade = upgrade
    self.label = label
    self.upDownCounter = upDownCounter
    self.upgradeValue = upgradeValue

    self.upDownCounter.counter.trace_add('write', self.refresh)


  def refresh(self, *args):
    """Called whenever the spinbox values change."""
    numUpgrades = self.get()

    if not numUpgrades:
      # Make invisible
      self.upgradeValue.configure(text="")
    else:
      upgradedValue = upgrader.getValue(self.upgrade, numUpgrades)
      upgradedText = str(upgradedValue)

      if upgradedText.isnumeric():
        # Numeric upgrades use an arrow to differentiate between count and value.
        upgradedText = f"=> {upgradedText}"
      self.upgradeValue.configure(text=upgradedText)

    self.upDownCounter.refresh()

  def destroy(self):
    """Destroys all objects contained by the counter."""
    self.label.destroy()
    self.upDownCounter.destroy()
    self.upgradeValue.destroy()

  def get(self):
    """Gets the internal counter variable."""
    return self.upDownCounter.get()

  def set(self, value):
    """Sets the internal counter variable to the given value."""
    self.upDownCounter.set(value)



class UpgradeChooser(tk.Frame):
  """Class containing subframe listing upgrades all at once."""

  def __init__(self, parent, *args, **kwargs):
    super().__init__(parent, *args, **kwargs)
    self.parent = parent

    # Dict mapping upgrade to corresponding UpgradeCounter widget collection.
    self.upgradeCountersByUpgrade = {}
    self.gameLabels = []

  def clearObjects(self):
    """Clears all widgets that may already be contained in the chooser."""
    for upgradeCounter in self.upgradeCountersByUpgrade.values():
      upgradeCounter.destroy()
    for gameLabel in self.gameLabels:
      gameLabel.destroy()

    self.upgradeCountersByUpgrade = {}
    self.gameLabels = []


  def zeroCounters(self):
    """Zeroes out all upgrade counters."""
    for upgradeCounter in self.upgradeCountersByUpgrade.values():
      upgradeCounter.set(0)
      upgradeCounter.refresh()

  
  def hasAnyUpgrades(self):
    """Returns whether any of the given upgrade counters have a positive count."""
    for upgradeCounter in self.upgradeCountersByUpgrade.values():
      if upgradeCounter.get() > 0:
        return True
    return False

  
  def loadUpgrades(self, allUpgrades):
    """Loads in a set of possible upgrades, creating widgets to represent them."""
    canvas = tk.Canvas(self, borderwidth=0, highlightthickness=0)
    scrollbar = tk.Scrollbar(self, command=canvas.yview)

    upgradeLayout = tk.Frame(canvas, borderwidth=0, highlightthickness=0)
    upgradeLayout.grid_columnconfigure(2, minsize=50)   # Forces value column to have min width to minimize UI-thrashing on value-load.
    upgradeLayout.pack()
    
    if allUpgrades:

      # Track these conditions as we iterate through the upgrade list.
      # Exact row may differ depending on inserted headers.
      currentRow = 0
      currentGame = ""

      for upgrade in allUpgrades:
        game = upgrade.yamlPath[0]

        if currentGame != game:
          # TODO: Consider adding an icon here to indicate whether this game is loaded or not.
          gameLabel = tk.Label(upgradeLayout, text=game, font="Hultog")
          self.gameLabels.append(gameLabel)
          gameLabel.grid(row=currentRow, column=0, columnspan=2)
          currentRow = currentRow + 1
          currentGame = game

        # Create representative widgets for each upgrade.
        upgradeLabel = tk.Label(upgradeLayout, text=upgrade.name)
        upgradeLabel.grid(row=currentRow, column=0)

        upperLimit = spinner.getLimitForUpgrade(upgrade, {})
        upDownCounter = UpDownCounter(upgradeLayout, upperLimit if upperLimit >= 0 else None)
        upDownCounter.grid(row=currentRow, column=1)

        upgradeValue = tk.Label(upgradeLayout, text="")
        upgradeValue.grid(row=currentRow, column=2)

        upgradeCounter = UpgradeCounter(upgrade, upgradeLabel, upDownCounter, upgradeValue)

        self.upgradeCountersByUpgrade[upgrade] = upgradeCounter

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


  
  def applyUpgrades(self, upgradeResults):
    """Updates the Chooser UI's selection count."""
    for upgrade, counter in self.upgradeCountersByUpgrade.items():
      newVal = upgradeResults.get(upgrade, 0)
      counter.set(newVal)
      counter.refresh()


  
  def getUpgradeResults(self):
    """Returns an UpgradeResults dict reflecting the values set in this widget."""
    upgradeResults = {}

    for counter in self.upgradeCountersByUpgrade.values():
      upgradeCount = int(counter.get() or 0)
      if upgradeCount > 0:
        upgradeResults[counter.upgrade] = upgradeCount

    return upgradeResults