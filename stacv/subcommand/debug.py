
from stacv import utils
from stacv import part
from stacv import board
from stacv import device
from stacv import timing_model

from stacv.diagram.block_diagram import text_diagram


def execute(cmd_line_args):

    config = utils.read_config_file(cmd_line_args.config_file)

    my_part = part.new(config['part'])
    my_board = board.new(config)
    my_device = device.new(config['device'])

    my_tm = timing_model.new('DAC_DATA', my_device, my_board, my_part)

    block_diagram = text_diagram.render(my_tm)
    for line in block_diagram:
        print(line)
