
from stacv.methodology import sdr_source_synchronous_output


def create_methodology(sName):
    if sName == 'SDR-SS-O':
        return sdr_source_synchronous_output.SdrSourceSynchronousOutput()
