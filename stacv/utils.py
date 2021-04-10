
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


letter_mapping_table = [None, 'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z']


def conv_letter_to_number(letter):
    return letter_mapping_table.index(letter)


def conv_number_to_letter(number):
    return letter_mapping_table[number]
