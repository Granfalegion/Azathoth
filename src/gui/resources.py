import os, sys

def getPath(*relativePathSteps):
    """Creates and returns absolute path to resource. Works both in a
    PyInstaller-created executable and in a development environment.
    """

    relativePath = os.path.join(*relativePathSteps)

    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        # Attempt to load resources from PyInstaller's temp folder, if present.
        base_path = getattr(sys, '_MEIPASS')
    else:
        # If temp folder is undefined, then use OS path instead.
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relativePath)
