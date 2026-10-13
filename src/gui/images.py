from gui import resources
from tkinter import PhotoImage

class keys():
  bg = "backgroundImage"

  b1 = "backgroundBlink1Image"
  b2 = "backgroundBlink2Image"
  b3 = "backgroundBlink3Image"

  ok = "okImage"
  warn = "warnImage"
  no = "badImage"

  weight = "weightIcon"

  sidebarL = "sidebarL"
  sidebarR = "sidebarR"


def loadImage(*args):
  """Creates and returns a TK PhotoImage from the described path."""
  return PhotoImage(file = resources.getPath(*args))


class Images():
  """Collection of loaded images used throughout Azathoth's UI."""

  def __init__(self):
    self.images = {
      # Background image.
      keys.bg: loadImage("img", "thoth-w.png"),

      # Blinks.
      keys.b1: loadImage("img", "thothb1-w.png"),
      keys.b2: loadImage("img", "thothb2-w.png"),
      keys.b3: loadImage("img", "thothb3-w.png"),

      # Status Icons for buttons.
      keys.ok: loadImage("img", "ok-sm.png"),
      keys.warn: loadImage("img", "warn-sm.png"),
      keys.no: loadImage("img", "no-sm.png"),

      # Standalone Icons
      keys.weight: loadImage("img", "weight-sm.png"),

      # Sidebar panels
      keys.sidebarL: loadImage("img", "ThothSidebarL.png"),
      keys.sidebarR: loadImage("img", "ThothSidebarR.png"),
    }

  def get(self, key):
    """Returns the image stored under the given key or a blank string."""
    return self.images.get(key, '')
