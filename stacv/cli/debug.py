
from stacv import utils
from stacv.intent import part
from stacv.intent import board
from stacv.intent import device
from stacv.intent import timing_model

from stacv.output.diagram.block_diagram import text_diagram as text_block_diagram
from stacv.output.diagram.clock import text_diagram as text_clock_diagram


def execute(cmd_line_args):

    if cmd_line_args.output == 'text_block_diagram':
        print_text_block_diagram(cmd_line_args)
    if cmd_line_args.output == 'text_clock_diagram':
        print_text_clock_diagram(cmd_line_args)


def print_text_block_diagram(cmd_line_args):
    config = utils.read_config_file(cmd_line_args.config_file)
    my_part = part.new(config['part'])
    my_board = board.new(config)
    my_device = device.new(config['device'])

    my_tm = timing_model.new('DAC_DATA', my_device, my_board, my_part)

    block_diagram = text_block_diagram.render(my_tm)
    for line in block_diagram:
        print(line)


def print_text_clock_diagram(cmd_line_args):
    config = utils.read_config_file(cmd_line_args.config_file)
    my_part = part.new(config['part'])
    my_board = board.new(config)
    my_device = device.new(config['device'])

    my_tm = timing_model.new('DAC_DATA', my_device, my_board, my_part)

    for my_pin in my_tm.device_interface.data_pins:
        print('#'*80)
        print(my_pin.name)
        print('-'*80)
        clock_diagram = text_clock_diagram.render(my_tm, my_pin.name)
        for line in clock_diagram:
            print(line)

