
from stacv import utils
from stacv import part
from stacv import board
from stacv import device
from stacv import timing_model

from stacv.diagram.block_diagram import text_diagram


def execute(cmd_line_args):

    config = utils.read_config_file(cmd_line_args.config_file) 

    oPart = part.new(config['part'])
    oBoard = board.new(config)
    oDevice = device.new(config['device'])



    oTM = timing_model.new('DAC_DATA', oDevice, oBoard, oPart) 

    block_diagram = text_diagram.render(oTM)
    for line in block_diagram:
        print(line)
