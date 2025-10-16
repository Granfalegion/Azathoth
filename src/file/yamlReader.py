import re
import yaml as pyyaml


def _sanitize(fileContents):
  '''Returns copy of the given file contents with troublesome contents removed.
  '''

  # Remove BOM for UTF-8, if present.
  # Added by some text editors and interferes with YAML ingestion.
  return re.sub("^\xEF\xBB\xBF", "", fileContents)


def readToYaml(inputYamlFileName):
  '''Reads in a YAML file at the given file address and returns it as a YAML
  object.
  '''
  
  with (open(inputYamlFileName)) as input:
    fileContents = _sanitize(input.read())
    return pyyaml.safe_load(fileContents)