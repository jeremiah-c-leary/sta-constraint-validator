'''
Provides error reporting for SPI configuration file issues.
'''

from stacv.config import config_error


class SpiConfigError(config_error.ConfigError):
    pass
