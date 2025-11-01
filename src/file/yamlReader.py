import re
import yaml as pyyaml


def _sanitize(fileContents):
  '''Returns copy of the given file contents with troublesome contents removed.
  '''

  # Remove BOM for UTF-8, if present.
  # Added by some text editors and interferes with YAML ingestion.
  return re.sub("^\xEF\xBB\xBF", "", fileContents)


def _readToYamlFromInput(input):
  '''Reads in a written YAML file contents are returns it as a YAML object.'''
  sanitizedInput = _sanitize(input)
  return pyyaml.safe_load(sanitizedInput)


def readToYaml(inputYamlFileName):
  '''Reads in a YAML file at the given file address and returns it as a YAML
  object.
  '''
  
  with (open(inputYamlFileName)) as input:
    return _readToYamlFromInput(input.read())
