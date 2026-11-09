'''
Provides error reporting for RMII configuration file issues.
'''

from stacv.config import config_error


class RmiiConfigError(config_error.ConfigError):
    pass
