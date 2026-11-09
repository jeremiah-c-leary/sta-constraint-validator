'''
Provides error reporting for RMII and MII configuration file issues.
'''

from stacv.config import config_error


class MacPhyConfigError(config_error.ConfigError):
    pass
