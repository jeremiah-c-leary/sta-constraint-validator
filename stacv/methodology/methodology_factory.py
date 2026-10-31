
from stacv.methodology import sdr_source_synchronous_output


SUPPORTED_METHODOLOGIES = ['SDR-SS-O']


def is_supported(sName):
    return sName in SUPPORTED_METHODOLOGIES


def create_methodology(sName):
    if sName == 'SDR-SS-O':
        return sdr_source_synchronous_output.SdrSourceSynchronousOutput()
