
from stacv import pin


def extract_data_structure(timing_model):

    diagram = {}
    diagram['device'] = {}
    diagram['device']['name'] = timing_model.device_name
    diagram['part'] = {}
    diagram['part']['name'] = timing_model.part_name
    diagram['traces'] = []

    clock_device_pin = timing_model.device_interface.external_clock

    input_device_pins = []
    output_device_pins = []
    for device_pin in timing_model.device_interface.data_pins:
        if isinstance(device_pin, pin.DeviceInputPin):
            input_device_pins.append(device_pin)
        if isinstance(device_pin, pin.DeviceOutputPin):
            output_device_pins.append(device_pin)

    for input_pin in input_device_pins:
        trace = {}
        trace['name'] = timing_model.traces.get_trace_name_connected_to_device_pin(input_pin.name)
        trace['clock'] = False
        trace['device_pin'] = input_pin.name
        trace['part_pin'] = timing_model.traces.get_part_pin_name_connected_to(input_pin.name)
        trace['direction'] = 'left'
        diagram['traces'].append(trace)

    for output_pin in output_device_pins:
        trace = {}
        trace['name'] = timing_model.traces.get_trace_name_connected_to_device_pin(output_pin.name)
        trace['clock'] = False
        trace['device_pin'] = output_pin.name
        trace['part_pin'] = timing_model.traces.get_part_pin_name_connected_to(output_pin.name)
        trace['direction'] = 'right'
        diagram['traces'].append(trace)

    trace = {}
    trace['name'] = timing_model.traces.get_trace_name_connected_to_device_pin(clock_device_pin.name)
    trace['clock'] = True
    trace['device_pin'] = clock_device_pin.name
    trace['part_pin'] = timing_model.traces.get_part_pin_name_connected_to(clock_device_pin.name)
    trace['direction'] = 'right'
    diagram['traces'].append(trace)

    return diagram
