-- A minimal design that drives a VSC8540ET in every MAC mode, so stacv's constraints can be run through Vivado.
-- Each interface has its own ports, as if the board had one PHY for each mode.
-- The registers only move test patterns: the design exists to be timed, not to pass Ethernet frames.
--
-- The edges each process uses match the interface files:
--   MDIO      : MDC is clk_100mhz / 40 (2.5 MHz).  MDIO is written when MDC falls and read 20 ns before MDC rises.
--   MII       : TXD is launched on the PHY's MII_TXCLK; RXD is captured on the PHY's RX_CLK.
--   RMII      : both directions use the 50 MHz clock from RMII_CLKOUT.
--   RGMII     : TXC is clk_100mhz / 4 (25 MHz); TXD changes 10 ns after each TXC edge, centred between edges.
--               RXD launched on an RXC edge is captured on the next RXC edge, by a register of the other edge.

library ieee;
  use ieee.std_logic_1164.all;
  use ieee.numeric_std.all;

entity vsc8540et_mac is
  port (
    I_CLK               : in    std_logic;
    -- Serial management interface
    O_MDC               : out   std_logic;
    IO_MDIO             : inout std_logic;
    -- MII
    I_MII_TX_CLK        : in    std_logic;
    O_MII_TXD           : out   std_logic_vector(3 downto 0);
    O_MII_TX_EN         : out   std_logic;
    O_MII_TX_ER         : out   std_logic;
    I_MII_RX_CLK        : in    std_logic;
    I_MII_RXD           : in    std_logic_vector(3 downto 0);
    I_MII_RX_DV         : in    std_logic;
    I_MII_RX_ER         : in    std_logic;
    -- RMII
    I_RMII_REF_CLK      : in    std_logic;
    O_RMII_TXD          : out   std_logic_vector(1 downto 0);
    O_RMII_TX_EN        : out   std_logic;
    O_RMII_TX_ER        : out   std_logic;
    I_RMII_RXD          : in    std_logic_vector(1 downto 0);
    I_RMII_CRS_DV       : in    std_logic;
    I_RMII_RX_ER        : in    std_logic;
    -- Uncompensated RGMII
    O_RGMII_TXC         : out   std_logic;
    O_RGMII_TXD         : out   std_logic_vector(3 downto 0);
    O_RGMII_TX_CTL      : out   std_logic;
    I_RGMII_RXC         : in    std_logic;
    I_RGMII_RXD         : in    std_logic_vector(3 downto 0);
    I_RGMII_RX_CTL      : in    std_logic;
    -- Compensated RGMII
    O_RGMII_ID_TXC      : out   std_logic;
    O_RGMII_ID_TXD      : out   std_logic_vector(3 downto 0);
    O_RGMII_ID_TX_CTL   : out   std_logic;
    I_RGMII_ID_RXC      : in    std_logic;
    I_RGMII_ID_RXD      : in    std_logic_vector(3 downto 0);
    I_RGMII_ID_RX_CTL   : in    std_logic
  );
end entity vsc8540et_mac;

architecture rtl of vsc8540et_mac is

  -- The capture registers drive nothing, so they are kept for the timing reports.
  attribute dont_touch : string;

  signal q_mdc_count      : unsigned(5 downto 0) := (others => '0');
  signal q_mdc            : std_logic := '0';
  signal q_mdio_pattern   : std_logic_vector(7 downto 0) := "10110010";
  signal q_mdio_out       : std_logic := '0';
  signal q_mdio_oe        : std_logic := '0';
  signal q_mdio_in        : std_logic := '0';
  attribute dont_touch of q_mdio_in : signal is "true";

  signal q_mii_txd        : unsigned(3 downto 0) := (others => '0');
  signal q_mii_tx_en      : std_logic := '0';
  signal q_mii_tx_er      : std_logic := '0';
  signal q_mii_rxd        : std_logic_vector(3 downto 0) := (others => '0');
  signal q_mii_rx_dv      : std_logic := '0';
  signal q_mii_rx_er      : std_logic := '0';
  attribute dont_touch of q_mii_rxd   : signal is "true";
  attribute dont_touch of q_mii_rx_dv : signal is "true";
  attribute dont_touch of q_mii_rx_er : signal is "true";

  signal q_rmii_txd       : unsigned(1 downto 0) := (others => '0');
  signal q_rmii_tx_en     : std_logic := '0';
  signal q_rmii_tx_er     : std_logic := '0';
  signal q_rmii_rxd       : std_logic_vector(1 downto 0) := (others => '0');
  signal q_rmii_crs_dv    : std_logic := '0';
  signal q_rmii_rx_er     : std_logic := '0';
  attribute dont_touch of q_rmii_rxd    : signal is "true";
  attribute dont_touch of q_rmii_crs_dv : signal is "true";
  attribute dont_touch of q_rmii_rx_er  : signal is "true";

  signal q_rgmii_count       : unsigned(1 downto 0) := (others => '0');
  signal q_rgmii_txc         : std_logic := '0';
  signal q_rgmii_id_txc      : std_logic := '0';
  -- The forwarded clock registers are the generators the interface files name, so synthesis must not merge them.
  attribute dont_touch of q_mdc          : signal is "true";
  attribute dont_touch of q_rgmii_txc    : signal is "true";
  attribute dont_touch of q_rgmii_id_txc : signal is "true";
  signal q_rgmii_txd         : unsigned(3 downto 0) := (others => '0');
  signal q_rgmii_tx_ctl      : std_logic := '0';
  signal q_rgmii_id_txd      : unsigned(3 downto 0) := (others => '0');
  signal q_rgmii_id_tx_ctl   : std_logic := '0';
  signal q_rgmii_rxd_rise    : std_logic_vector(3 downto 0) := (others => '0');
  signal q_rgmii_rxd_fall    : std_logic_vector(3 downto 0) := (others => '0');
  signal q_rgmii_rx_ctl_rise : std_logic := '0';
  signal q_rgmii_rx_ctl_fall : std_logic := '0';
  signal q_rgmii_id_rxd_rise    : std_logic_vector(3 downto 0) := (others => '0');
  signal q_rgmii_id_rxd_fall    : std_logic_vector(3 downto 0) := (others => '0');
  signal q_rgmii_id_rx_ctl_rise : std_logic := '0';
  signal q_rgmii_id_rx_ctl_fall : std_logic := '0';
  attribute dont_touch of q_rgmii_rxd_rise       : signal is "true";
  attribute dont_touch of q_rgmii_rxd_fall       : signal is "true";
  attribute dont_touch of q_rgmii_rx_ctl_rise    : signal is "true";
  attribute dont_touch of q_rgmii_rx_ctl_fall    : signal is "true";
  attribute dont_touch of q_rgmii_id_rxd_rise    : signal is "true";
  attribute dont_touch of q_rgmii_id_rxd_fall    : signal is "true";
  attribute dont_touch of q_rgmii_id_rx_ctl_rise : signal is "true";
  attribute dont_touch of q_rgmii_id_rx_ctl_fall : signal is "true";

begin

  ---------------------------------------------------------------------------
  -- Serial management interface: MDC rises when the count wraps to 0 and falls when it reaches 20.
  ---------------------------------------------------------------------------
  PROC_MDIO : process (I_CLK) is
  begin
    if rising_edge(I_CLK) then
      if q_mdc_count = 39 then
        q_mdc_count <= (others => '0');
        q_mdc       <= '1';
      else
        q_mdc_count <= q_mdc_count + 1;
      end if;
      -- Written as MDC falls, 200 ns before the rising edge the PHY samples on.
      if q_mdc_count = 19 then
        q_mdc          <= '0';
        q_mdio_out     <= q_mdio_pattern(0);
        q_mdio_oe      <= q_mdio_pattern(7);
        q_mdio_pattern <= q_mdio_pattern(0) & q_mdio_pattern(7 downto 1);
      end if;
      -- Read 20 ns before MDC rises, 380 ns after the rising edge the PHY launched it on.
      if q_mdc_count = 37 then
        q_mdio_in <= IO_MDIO;
      end if;
    end if;
  end process PROC_MDIO;

  O_MDC   <= q_mdc;
  IO_MDIO <= q_mdio_out when q_mdio_oe = '1' else 'Z';

  ---------------------------------------------------------------------------
  -- MII: the PHY sends both clocks.
  ---------------------------------------------------------------------------
  PROC_MII_TX : process (I_MII_TX_CLK) is
  begin
    if rising_edge(I_MII_TX_CLK) then
      q_mii_txd   <= q_mii_txd + 1;
      q_mii_tx_en <= q_mii_txd(3);
      q_mii_tx_er <= q_mii_txd(2);
    end if;
  end process PROC_MII_TX;

  O_MII_TXD   <= std_logic_vector(q_mii_txd);
  O_MII_TX_EN <= q_mii_tx_en;
  O_MII_TX_ER <= q_mii_tx_er;

  PROC_MII_RX : process (I_MII_RX_CLK) is
  begin
    if rising_edge(I_MII_RX_CLK) then
      q_mii_rxd   <= I_MII_RXD;
      q_mii_rx_dv <= I_MII_RX_DV;
      q_mii_rx_er <= I_MII_RX_ER;
    end if;
  end process PROC_MII_RX;

  ---------------------------------------------------------------------------
  -- RMII: one 50 MHz clock for both directions.
  ---------------------------------------------------------------------------
  PROC_RMII : process (I_RMII_REF_CLK) is
  begin
    if rising_edge(I_RMII_REF_CLK) then
      q_rmii_txd    <= q_rmii_txd + 1;
      q_rmii_tx_en  <= q_rmii_txd(1);
      q_rmii_tx_er  <= q_rmii_txd(0);
      q_rmii_rxd    <= I_RMII_RXD;
      q_rmii_crs_dv <= I_RMII_CRS_DV;
      q_rmii_rx_er  <= I_RMII_RX_ER;
    end if;
  end process PROC_RMII;

  O_RMII_TXD   <= std_logic_vector(q_rmii_txd);
  O_RMII_TX_EN <= q_rmii_tx_en;
  O_RMII_TX_ER <= q_rmii_tx_er;

  ---------------------------------------------------------------------------
  -- RGMII transmit: TXC rises when the count wraps to 0 and falls at 2; the data changes at 1 and 3.
  ---------------------------------------------------------------------------
  PROC_RGMII_TX : process (I_CLK) is
  begin
    if rising_edge(I_CLK) then
      q_rgmii_count <= q_rgmii_count + 1;
      if q_rgmii_count = 3 then
        q_rgmii_txc    <= '1';
        q_rgmii_id_txc <= '1';
      elsif q_rgmii_count = 1 then
        q_rgmii_txc    <= '0';
        q_rgmii_id_txc <= '0';
      end if;
      if q_rgmii_count = 0 or q_rgmii_count = 2 then
        q_rgmii_txd       <= q_rgmii_txd + 1;
        q_rgmii_tx_ctl    <= q_rgmii_txd(3);
        q_rgmii_id_txd    <= q_rgmii_id_txd + 3;
        q_rgmii_id_tx_ctl <= q_rgmii_id_txd(3);
      end if;
    end if;
  end process PROC_RGMII_TX;

  O_RGMII_TXC       <= q_rgmii_txc;
  O_RGMII_TXD       <= std_logic_vector(q_rgmii_txd);
  O_RGMII_TX_CTL    <= q_rgmii_tx_ctl;
  O_RGMII_ID_TXC    <= q_rgmii_id_txc;
  O_RGMII_ID_TXD    <= std_logic_vector(q_rgmii_id_txd);
  O_RGMII_ID_TX_CTL <= q_rgmii_id_tx_ctl;

  ---------------------------------------------------------------------------
  -- RGMII receive: data launched on one RXC edge is captured on the next edge.
  ---------------------------------------------------------------------------
  PROC_RGMII_RX_RISE : process (I_RGMII_RXC) is
  begin
    if rising_edge(I_RGMII_RXC) then
      q_rgmii_rxd_rise    <= I_RGMII_RXD;
      q_rgmii_rx_ctl_rise <= I_RGMII_RX_CTL;
    end if;
  end process PROC_RGMII_RX_RISE;

  PROC_RGMII_RX_FALL : process (I_RGMII_RXC) is
  begin
    if falling_edge(I_RGMII_RXC) then
      q_rgmii_rxd_fall    <= I_RGMII_RXD;
      q_rgmii_rx_ctl_fall <= I_RGMII_RX_CTL;
    end if;
  end process PROC_RGMII_RX_FALL;

  PROC_RGMII_ID_RX_RISE : process (I_RGMII_ID_RXC) is
  begin
    if rising_edge(I_RGMII_ID_RXC) then
      q_rgmii_id_rxd_rise    <= I_RGMII_ID_RXD;
      q_rgmii_id_rx_ctl_rise <= I_RGMII_ID_RX_CTL;
    end if;
  end process PROC_RGMII_ID_RX_RISE;

  PROC_RGMII_ID_RX_FALL : process (I_RGMII_ID_RXC) is
  begin
    if falling_edge(I_RGMII_ID_RXC) then
      q_rgmii_id_rxd_fall    <= I_RGMII_ID_RXD;
      q_rgmii_id_rx_ctl_fall <= I_RGMII_ID_RX_CTL;
    end if;
  end process PROC_RGMII_ID_RX_FALL;

end architecture rtl;
