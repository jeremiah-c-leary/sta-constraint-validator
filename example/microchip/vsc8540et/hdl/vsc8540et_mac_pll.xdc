# Read after the interface constraints, so rgmii_id_rxc exists.
# Vivado derives the PLL's output clock from rgmii_id_rxc; this names it as rgmii_id.toml does.
create_generated_clock -name rgmii_id_rxc_shifted [get_pins U_RGMII_ID_PLL/CLKOUT0]
