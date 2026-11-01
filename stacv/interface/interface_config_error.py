'''
Provides error reporting for interface file issues.
'''

from stacv.config import config_error


class InterfaceConfigError(config_error.ConfigError):
    pass
