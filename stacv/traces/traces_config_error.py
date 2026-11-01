'''
Provides error reporting for traces file issues.
'''

from stacv.config import config_error


class TracesConfigError(config_error.ConfigError):
    pass
