
import yaml


def read_config_file(config_files):
    '''
    Attempts to read the suppression file and return an list of rules.
    Parameters:
       config_files : (String)
    Returns:  dictionary
    '''

    with open(config_files) as yaml_file:
        my_file = yaml.full_load(yaml_file)

    if my_file is None:
        my_file = {}

    return my_file
