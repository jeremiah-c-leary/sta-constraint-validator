--------------------------------------------------------------------------------
-- spi_master
--
-- SPI mode 0 controller for 24-bit register accesses (R/W bit, 15-bit address,
-- 8-bit data, MSB first), as used by the TI DAC39RF20 standard SPI interface.
--
--   * sclk idles low.  Data is driven on the falling edge of sclk and sampled
--     by the peripheral on the rising edge.
--   * sclk is a register output: it toggles every HALF_PERIOD system clocks,
--     so f_sclk = f_clk / (2 * HALF_PERIOD).
--   * The read data (sdo) is sampled at the same system clock edge that drives
--     sclk high, half an sclk period after the peripheral launched it.
--   * scs_n falls half an sclk period before the first rising edge of sclk and
--     rises half an sclk period after the last falling edge.  It then stays
--     high for at least half an sclk period before the next access.
--
-- All four interface signals come straight from, or go straight into, a
-- register so that the board-level timing is set by the I/O path only.
--------------------------------------------------------------------------------
library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity spi_master is
    generic (
        HALF_PERIOD : positive := 4    -- system clocks per half sclk period
    );
    port (
        clk         : in  std_logic;
        rst         : in  std_logic;   -- synchronous, active high

        -- access request
        start       : in  std_logic;
        read_not_wr : in  std_logic;
        address     : in  std_logic_vector(14 downto 0);
        write_data  : in  std_logic_vector(7 downto 0);
        busy        : out std_logic;
        done        : out std_logic;   -- one clock pulse at the end of an access
        read_data   : out std_logic_vector(7 downto 0);

        -- SPI pins
        sclk        : out std_logic;
        sdi         : out std_logic;   -- controller out, peripheral in
        sdo         : in  std_logic;   -- peripheral out, controller in
        scs_n       : out std_logic
    );
end entity spi_master;

architecture rtl of spi_master is

    constant FRAME_BITS : natural := 24;

    type state_t is (IDLE, SCLK_LOW, SCLK_HIGH, TRAIL, GAP);
    signal state : state_t := IDLE;

    signal half_count : natural range 0 to HALF_PERIOD - 1 := 0;
    signal bit_count  : natural range 0 to FRAME_BITS - 1 := 0;

    signal tx_shift   : std_logic_vector(FRAME_BITS - 1 downto 0) := (others => '0');
    signal rx_shift   : std_logic_vector(7 downto 0) := (others => '0');   -- the data field only

    signal sclk_q     : std_logic := '0';
    signal sdi_q      : std_logic := '0';
    signal scs_n_q    : std_logic := '1';
    signal done_q     : std_logic := '0';
    signal rdata_q    : std_logic_vector(7 downto 0) := (others => '0');

begin

    sclk      <= sclk_q;
    sdi       <= sdi_q;
    scs_n     <= scs_n_q;
    done      <= done_q;
    read_data <= rdata_q;
    busy      <= '0' when state = IDLE else '1';

    process (clk)
        variable half_done : boolean;
    begin
        if rising_edge(clk) then
            done_q    <= '0';
            half_done := (half_count = HALF_PERIOD - 1);

            if half_done then
                half_count <= 0;
            else
                half_count <= half_count + 1;
            end if;

            if rst = '1' then
                state      <= IDLE;
                half_count <= 0;
                bit_count  <= 0;
                sclk_q     <= '0';
                sdi_q      <= '0';
                scs_n_q    <= '1';
            else
                case state is

                    when IDLE =>
                        half_count <= 0;
                        if start = '1' then
                            tx_shift   <= read_not_wr & address & write_data;
                            sdi_q      <= read_not_wr;   -- first bit, MSB
                            scs_n_q    <= '0';
                            bit_count  <= 0;
                            state      <= SCLK_LOW;
                        end if;

                    when SCLK_LOW =>
                        if half_done then
                            sclk_q   <= '1';
                            rx_shift <= rx_shift(6 downto 0) & sdo;
                            state    <= SCLK_HIGH;
                        end if;

                    when SCLK_HIGH =>
                        if half_done then
                            sclk_q <= '0';
                            if bit_count = FRAME_BITS - 1 then
                                state <= TRAIL;
                            else
                                bit_count <= bit_count + 1;
                                tx_shift  <= tx_shift(FRAME_BITS - 2 downto 0) & '0';
                                sdi_q     <= tx_shift(FRAME_BITS - 2);
                                state     <= SCLK_LOW;
                            end if;
                        end if;

                    when TRAIL =>
                        if half_done then
                            scs_n_q <= '1';
                            rdata_q <= rx_shift;
                            done_q  <= '1';
                            state   <= GAP;
                        end if;

                    when GAP =>
                        if half_done then
                            state <= IDLE;
                        end if;

                end case;
            end if;
        end if;
    end process;

end architecture rtl;
