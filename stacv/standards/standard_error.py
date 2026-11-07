'''
Provides error reporting for an interface that does not follow the interface standard it names.
'''

from stacv.config import config_error


class StandardError(config_error.ConfigError):
    pass
