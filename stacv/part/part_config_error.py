'''
Provides error reporting for part file issues.
'''

from stacv.config import config_error


class PartConfigError(config_error.ConfigError):
    pass
