import yaml as pyyaml

def writeYamlToFile(yaml, path):
  '''Writes the given YAML object to a file at the given path.'''
  with (open(path, "w")) as output:
      output.write(pyyaml.safe_dump(yaml, sort_keys=False))

def writeToFile(contents, path):
   '''Writes the given string to a file at the given path.
   
   Useful for constructed YAML contents (e.g. with comments).
   '''
   with(open(path, "w")) as output:
      output.write(contents)
