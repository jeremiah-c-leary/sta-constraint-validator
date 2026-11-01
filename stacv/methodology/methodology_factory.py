
from stacv.methodology import sdr_source_synchronous_output
from stacv.methodology import sdr_source_synchronous_output_first_last_clock


SUPPORTED_METHODOLOGIES = ['SDR-SS-O', 'SDR-SS-O-FLC']


def is_supported(sName):
    return sName in SUPPORTED_METHODOLOGIES


def create_methodology(sName):
    if sName == 'SDR-SS-O':
        return sdr_source_synchronous_output.SdrSourceSynchronousOutput()
    if sName == 'SDR-SS-O-FLC':
        return sdr_source_synchronous_output_first_last_clock.SdrSourceSynchronousOutputFirstLastClock()
