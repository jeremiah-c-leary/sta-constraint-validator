
from stacv import pin


def extract_data_structure(timing_model):

    diagram = {}
    diagram['device'] = extract_device_name(timing_model)
    diagram['part'] = extract_part_name(timing_model)
    diagram['traces'] = extract_traces(timing_model)

    return diagram


def extract_device_name(timing_model):

    device = {}

    device['name'] = timing_model.device_name

    return device


def extract_part_name(timing_model):

    part = {}

    part['name'] = timing_model.part_name

    return part


def extract_traces(timing_model):

    traces = []

    traces.extend(extract_input_traces(timing_model))
    traces.extend(extract_output_traces(timing_model))
    traces.extend(extract_clock_traces(timing_model))

    return traces


def extract_input_traces(timing_model):

    traces = []

    input_device_pins = extract_input_pins(timing_model)

    for input_pin in input_device_pins:
        trace = {}
        trace['name'] = timing_model.traces.get_trace_name_connected_to_device_pin(input_pin.name)
        trace['clock'] = False
        trace['device_pin'] = input_pin.name
        trace['part_pin'] = timing_model.traces.get_part_pin_name_connected_to(input_pin.name)
        trace['direction'] = 'left'
        traces.append(trace)

    return traces


def extract_input_pins(timing_model):
    input_device_pins = []
    for device_pin in timing_model.device_interface.data_pins:
        if isinstance(device_pin, pin.DeviceInputPin):
            input_device_pins.append(device_pin)
    return input_device_pins


def extract_output_traces(timing_model):

    traces = []

    output_device_pins = extract_output_pins(timing_model)

    for output_pin in output_device_pins:
        trace = {}
        trace['name'] = timing_model.traces.get_trace_name_connected_to_device_pin(output_pin.name)
        trace['clock'] = False
        trace['device_pin'] = output_pin.name
        trace['part_pin'] = timing_model.traces.get_part_pin_name_connected_to(output_pin.name)
        trace['direction'] = 'right'
        traces.append(trace)

    return traces


def extract_output_pins(timing_model):
    output_device_pins = []
    for device_pin in timing_model.device_interface.data_pins:
        if isinstance(device_pin, pin.DeviceOutputPin):
            output_device_pins.append(device_pin)
    return output_device_pins


def extract_clock_traces(timing_model):

    clock_device_pin = timing_model.device_interface.external_clock

    traces = []

    trace = {}
    trace['name'] = timing_model.traces.get_trace_name_connected_to_device_pin(clock_device_pin.name)
    trace['clock'] = True
    trace['device_pin'] = clock_device_pin.name
    trace['part_pin'] = timing_model.traces.get_part_pin_name_connected_to(clock_device_pin.name)
    trace['direction'] = 'right'
    traces.append(trace)

    return traces
