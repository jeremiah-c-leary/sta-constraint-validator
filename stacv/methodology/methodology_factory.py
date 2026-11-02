from stacv.methodology import clock_crossing_methodologies
from stacv.methodology import sdr_source_synchronous_output
from stacv.methodology import sdr_source_synchronous_output_first_last_clock
from stacv.methodology import sdr_source_synchronous_round_trip


METHODOLOGIES = {}
METHODOLOGIES['SDR-SS-O'] = sdr_source_synchronous_output.SdrSourceSynchronousOutput
METHODOLOGIES['SDR-SS-O-FLC'] = sdr_source_synchronous_output_first_last_clock.SdrSourceSynchronousOutputFirstLastClock
METHODOLOGIES['SDR-SS-RT-DI'] = sdr_source_synchronous_round_trip.SdrSourceSynchronousRoundTrip
METHODOLOGIES['SDR-SS-I'] = clock_crossing_methodologies.SdrSourceSynchronousInput
METHODOLOGIES['SDR-SS-RT-DO'] = clock_crossing_methodologies.SdrSourceSynchronousRoundTripDataOut
METHODOLOGIES['SDR-SYS-O'] = clock_crossing_methodologies.SdrSystemSynchronousOutput
METHODOLOGIES['SDR-SYS-I'] = clock_crossing_methodologies.SdrSystemSynchronousInput
METHODOLOGIES['DDR-SS-O'] = clock_crossing_methodologies.DdrSourceSynchronousOutput
METHODOLOGIES['DDR-SS-I'] = clock_crossing_methodologies.DdrSourceSynchronousInput
SUPPORTED_METHODOLOGIES = list(METHODOLOGIES)


def is_supported(sName):
    return sName in METHODOLOGIES


def create_methodology(sName):
    if sName not in METHODOLOGIES:
        return None
    return METHODOLOGIES[sName]()
