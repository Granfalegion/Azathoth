import tkinter as tk
from tkinter.simpledialog import Dialog

REMEMBER_SELECTION_TEXT = "Remember my selection"

class MemoryModal(Dialog):

  def __init__(self, parent, title, message, buttonDict):
    self.parent = parent
    self.message = message
    self.buttonClicked = None
    self.buttonDict = buttonDict

    # Super-constructor goes last; it needs init'd variables for other methods.
    super().__init__(parent, title=title)


  def body(self, master):
    '''Constructs body of Dialog with dynamically-populated buttons and option
    to remember the selected result.
    '''

    # TODO: Add icon support
    tk.Label(master, text=self.message, anchor="w").pack(fill='x')

    memoryFrame = tk.Frame(master)
    self.rememberVar = tk.BooleanVar(value=False)
    tk.Checkbutton(memoryFrame, variable=self.rememberVar).pack(side='left')
    rememberLabel = tk.Label(memoryFrame, text=REMEMBER_SELECTION_TEXT)
    rememberLabel.bind("<Button-1>",
                       lambda _:
                           self.rememberVar.set(not self.rememberVar.get()))
    rememberLabel.pack(side='right')
    memoryFrame.pack()

    return memoryFrame


  def click(self, clickValue):
    '''Helper function for final OK call, storing which button was clicked.'''
    self.buttonClicked = clickValue
    self.ok()


  def buttonbox(self):
    '''Overrides Dialog method to dynamically construct buttons.'''
    box = tk.Frame(self)

    for button, result in self.buttonDict.items():
      if result == "cancel":
        raise ValueError(f"Received explicit `cancel` command in MemoryModal."
                          "This is handled automatically; do not provide it.")

      button = tk.Button(box, text=button, width=10,
                         command= lambda clickVal=result: self.click(clickVal))
      button.pack(side=tk.LEFT, padx=5, pady=5)

    cancelButton = tk.Button(box, text="Cancel", width=10, command=self.cancel)
    cancelButton.pack(side=tk.LEFT, padx=5, pady=5)
    box.pack()


  def apply(self):
    '''Overrides Dialog method to return tuple of selection and memory.'''
    self.result = (self.buttonClicked, self.rememberVar.get())