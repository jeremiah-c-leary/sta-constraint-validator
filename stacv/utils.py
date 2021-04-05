
import yaml


def read_config_file(config_files):
    '''
    Attempts to read the suppression file and return an list of rules.
    Parameters:
       config_files : (String)
    Returns:  dictionary
    '''

    with open(config_files) as yaml_file:
        dReturn = yaml.full_load(yaml_file)

    if dReturn is None:
        dReturn = {}

    return dReturn
