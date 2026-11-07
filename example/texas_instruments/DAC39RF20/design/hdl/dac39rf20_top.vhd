--------------------------------------------------------------------------------
-- dac39rf20_top
--
-- Brings up a TI DAC39RF20 over its standard SPI interface and shows the
-- result on two LEDs.  Target: Xilinx xc7a12tcpg238-2, 100 MHz board clock,
-- SPI at 12.5 MHz (the DAC39RF20 allows up to 15 MHz), 1.8 V I/O.
--------------------------------------------------------------------------------
library ieee;
use ieee.std_logic_1164.all;

entity dac39rf20_top is
    port (
        clk_100m     : in  std_logic;
        btn_reset    : in  std_logic;   -- active high push button

        dac_sclk     : out std_logic;
        dac_sdi      : out std_logic;
        dac_sdo      : in  std_logic;
        dac_scs_n    : out std_logic;
        dac_resetn   : out std_logic;

        led_done     : out std_logic;
        led_id_ok    : out std_logic
    );
end entity dac39rf20_top;

architecture rtl of dac39rf20_top is

    signal reset_sync  : std_logic_vector(2 downto 0) := (others => '1');
    signal rst         : std_logic;

    signal spi_start   : std_logic;
    signal spi_read    : std_logic;
    signal spi_address : std_logic_vector(14 downto 0);
    signal spi_wdata   : std_logic_vector(7 downto 0);
    signal spi_busy    : std_logic;
    signal spi_done    : std_logic;
    signal spi_rdata   : std_logic_vector(7 downto 0);

begin

    -- The push button is asynchronous: bring it into the clock domain.
    process (clk_100m)
    begin
        if rising_edge(clk_100m) then
            reset_sync <= reset_sync(1 downto 0) & btn_reset;
        end if;
    end process;
    rst <= reset_sync(2);

    u_init : entity work.dac39rf20_init
        port map (
            clk         => clk_100m,
            rst         => rst,
            dac_resetn  => dac_resetn,
            spi_start   => spi_start,
            spi_read    => spi_read,
            spi_address => spi_address,
            spi_wdata   => spi_wdata,
            spi_busy    => spi_busy,
            spi_done    => spi_done,
            spi_rdata   => spi_rdata,
            init_done   => led_done,
            id_ok       => led_id_ok
        );

    u_spi : entity work.spi_master
        generic map (
            HALF_PERIOD => 4    -- 100 MHz / 8 = 12.5 MHz sclk
        )
        port map (
            clk         => clk_100m,
            rst         => rst,
            start       => spi_start,
            read_not_wr => spi_read,
            address     => spi_address,
            write_data  => spi_wdata,
            busy        => spi_busy,
            done        => spi_done,
            read_data   => spi_rdata,
            sclk        => dac_sclk,
            sdi         => dac_sdi,
            sdo         => dac_sdo,
            scs_n       => dac_scs_n
        );

end architecture rtl;
