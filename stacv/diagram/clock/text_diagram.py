
from stacv import clock


def render(timing_model, pin):

    diagram = []

    if pin == 'O_DAC_DATA':
        device_pin = timing_model.get_device_pin(pin)
        print(device_pin)
        launch_pin = timing_model.get_device_clock_named(device_pin.nch_clock)
        print(launch_pin)
        capture_pin = timing_model.get_device_pin('O_DAC_SCLK')
        launch_clock = clock.new(launch_pin.max_freq)
        capture_clock = clock.new(capture_pin.max_freq)
        if launch_clock.period < capture_clock.period:
            clock.expand(capture_clock, 2)
            clock.expand(launch_clock, 10)
        dwell_time = 2

        line = '   '
        for edge in launch_clock.edges[:-1]:
           if edge.direction == 'rising':
               line += '__ '
           else:
               line += '   '
        diagram.append(line)

        line = '__'
        for edge in launch_clock.edges[:-1]:
           if edge.direction == 'rising':
               line += '|  '
           else:
               line += '|__'
        line += '|'

        diagram.append(line)

        line = ''
        diagram.append(line)

        line = '   '
        for edge in capture_clock.edges[:-1]:
            if edge.direction == 'rising':
                line += '_'*(dwell_time*3 + dwell_time*2 + 4) + ' '
            else:
                line += ' '*(dwell_time*3 + dwell_time*2 + 4) + ' '
        diagram.append(line)

        line = '__'
        for edge in capture_clock.edges[:-1]:
            if edge.direction == 'rising':
                line += '|' + ' '*(dwell_time*3 + dwell_time*2 + 4)
            else:
                line += '|' + '_'*(dwell_time*3 + dwell_time*2 + 4)
        line += '|'
        diagram.append(line)
    elif pin == 'I_DAC_DATA':
        diagram.append('   ______________                ______________                ')
        diagram.append('__|              |______________|              |______________|')
        diagram.append('')
        diagram.append('   __    __    __    __    __    __    __    __    __    __    ')
        diagram.append('__|  |__|  |__|  |__|  |__|  |__|  |__|  |__|  |__|  |__|  |__|')
    else:
        diagram.append('   __    __    __    __    ')
        diagram.append('__|  |__|  |__|  |__|  |__|')
        diagram.append('')
        diagram.append('   _____       _____       ')
        diagram.append('__|     |_____|     |_____|')


    return diagram
