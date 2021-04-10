
def create_part_dict():

    dPart = {}
    
    dPart['vendor'] = 'Texas Instruments'
    dPart['name'] = 'DAC81404'
    
    dPart['interface'] = []
    
    dInterface = {}
    dInterface['serial_data'] = {}

    dInterface['serial_data']['timing_model'] = 'source_synchronous_with_round_trip'
    
    dInterface['serial_data']['clock'] = {}
    dInterface['serial_data']['clock']['input'] = []

    dPin = {}
    dPin['SCLK'] = {}
    dPin['SCLK']['max_freq'] = '20 MHz'
    dInterface['serial_data']['clock']['input'].append(dPin)


    dInterface['serial_data']['data'] = {}
    dInterface['serial_data']['data']['input'] = []

    dPin = {}
    dPin['SDIN'] = {}
    dPin['SDIN']['clock'] = 'SCLK'
    dPin['SDIN']['rising'] = {}
    dPin['SDIN']['rising']['setup'] = {}
    dPin['SDIN']['rising']['setup']['id'] = 't1'
    dPin['SDIN']['rising']['setup']['value'] = 5.0
    dPin['SDIN']['rising']['hold'] = {}
    dPin['SDIN']['rising']['hold']['id'] = 't2'
    dPin['SDIN']['rising']['hold']['value'] = 1.0

    dInterface['serial_data']['data']['input'].append(dPin)
    
    dInterface['serial_data']['data']['output'] = []

    dPin = {}
    dPin['SDO'] = {}
    dPin['SDO']['clock'] = 'SCLK'
    dPin['SDO']['falling'] = {}
    dPin['SDO']['falling']['clock_to_out_max'] = {}
    dPin['SDO']['falling']['clock_to_out_max']['id'] = 't3'
    dPin['SDO']['falling']['clock_to_out_max']['value'] = 20
    dPin['SDO']['falling']['clock_to_out_min'] = {}
    dPin['SDO']['falling']['clock_to_out_min']['id'] = 't3'
    dPin['SDO']['falling']['clock_to_out_min']['value'] = 0

    dPart['interface'].append(dInterface)
 
    return dPart


def create_board_dict():

    dBoardConfig = {}
    dBoardConfig['board'] = {}
    dBoardConfig['board']['trace'] = []
    
    dTrace = {}
    dTrace['clock'] = {}
    dTrace['clock']['device_pin'] = 'O_DAC_SCLK'
    dTrace['clock']['part_pin'] = 'SCLK'
    dTrace['clock']['delay'] = {}
    dTrace['clock']['delay']['max'] = 2.0
    dTrace['clock']['delay']['min'] = 1.0
    
    dBoardConfig['board']['trace'].append(dTrace)
    
    dTrace = {}
    dTrace['data_out'] = {}
    dTrace['data_out']['device_pin'] = 'O_DAC_DATA'
    dTrace['data_out']['part_pin'] = 'SDIN'
    dTrace['data_out']['delay'] = {}
    dTrace['data_out']['delay']['max'] = 2.5
    dTrace['data_out']['delay']['min'] = 1.5
    
    dBoardConfig['board']['trace'].append(dTrace)
    
    dTrace = {}
    dTrace['data_in'] = {}
    dTrace['data_in']['device_pin'] = 'I_DAC_DATA'
    dTrace['data_in']['part_pin'] = 'SDO'
    dTrace['data_in']['delay'] = {}
    dTrace['data_in']['delay']['max'] = 1.5
    dTrace['data_in']['delay']['min'] = 0.5
    
    dBoardConfig['board']['trace'].append(dTrace)

    return dBoardConfig


def create_device_dict():

    dDevice = {}
    
    dDevice['vendor'] = 'Intel'
    dDevice['name'] = 'Arria10'
    
    dDevice['interface'] = []
    
    dInterface = {}
    dInterface['DAC_DATA'] = {}
    ############################################################################
    dInterface['DAC_DATA']['clock'] = {}
    ############################################################################
    dInterface['DAC_DATA']['clock']['internal'] = []
 
    dClock = {}
    dClock['int_clock'] = {}
    dClock['int_clock']['frequency'] = '100 MHz'

    dInterface['DAC_DATA']['clock']['internal'].append(dClock)

    ############################################################################
    dInterface['DAC_DATA']['clock']['output'] = []
 
    dClock = {}
    dClock['O_DAC_SCLK'] = {}
    dClock['O_DAC_SCLK']['frequency'] = '20 MHz'

    dInterface['DAC_DATA']['clock']['output'].append(dClock)
    ############################################################################
    dInterface['DAC_DATA']['data'] = {}
    ############################################################################
    dInterface['DAC_DATA']['data']['output'] = []
    
    dPin = {} 
    dPin['O_DAC_DATA'] = {}
    dPin['O_DAC_DATA']['launch_clock'] = {}
    dPin['O_DAC_DATA']['launch_clock']['name'] = 'int_clock'
    dPin['O_DAC_DATA']['launch_clock']['edge'] = 3

    dPin['O_DAC_DATA']['capture_clock'] = {}
    dPin['O_DAC_DATA']['capture_clock']['name'] = 'O_DAC_SCLK'
    dPin['O_DAC_DATA']['capture_clock']['edge'] = {}
    dPin['O_DAC_DATA']['capture_clock']['edge']['setup'] = 'f'
    dPin['O_DAC_DATA']['capture_clock']['edge']['hold'] = 'q'

    dInterface['DAC_DATA']['data']['output'].append(dPin)
    ############################################################################
    dInterface['DAC_DATA']['data']['input'] = []

    dPin = {} 
    dPin['I_DAC_DATA'] = {}
    dPin['I_DAC_DATA']['launch_clock'] = {}
    dPin['I_DAC_DATA']['launch_clock']['name'] = 'O_DAC_SCLK'
    dPin['I_DAC_DATA']['launch_clock']['edge'] = 11

    dPin['I_DAC_DATA']['capture_clock'] = {}
    dPin['I_DAC_DATA']['capture_clock']['name'] = 'int_clock'
    dPin['I_DAC_DATA']['capture_clock']['edge'] = {}
    dPin['I_DAC_DATA']['capture_clock']['edge']['setup'] = 'c'
    dPin['I_DAC_DATA']['capture_clock']['edge']['hold'] = 'd'

    dInterface['DAC_DATA']['data']['input'].append(dPin)
    ############################################################################

    dDevice['interface'].append(dInterface)    

    return dDevice

