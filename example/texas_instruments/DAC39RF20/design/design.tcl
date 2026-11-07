# Design description for bin/vivado_loop: the top, the part and the source
# files, relative to this file.
set design_top  dac39rf20_top
set design_part xc7a12tcpg238-2

set design_vhdl [list \
    hdl/spi_master.vhd \
    hdl/dac39rf20_init.vhd \
    hdl/dac39rf20_top.vhd \
]

set design_xdc [list \
    constraints/dac39rf20_board.xdc \
]
