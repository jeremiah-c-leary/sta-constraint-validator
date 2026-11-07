--------------------------------------------------------------------------------
-- dac39rf20_init
--
-- Start-up sequencer for the TI DAC39RF20.
--
--   1. Holds the DAC in reset (resetn low) for RESET_CLOCKS system clocks.
--      The datasheet asks for at least 100 ns (tRESET).
--   2. Waits WAKE_CLOCKS system clocks after releasing reset.
--   3. Runs a short list of SPI accesses: puts the device in normal power
--      mode, then reads back the identification registers and compares them
--      with the values the datasheet gives.
--
-- id_ok is set when every read returned its expected value; init_done is set
-- when the list has been run, whatever the result.
--------------------------------------------------------------------------------
library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity dac39rf20_init is
    generic (
        RESET_CLOCKS : positive := 16;    -- 160 ns at 100 MHz
        WAKE_CLOCKS  : positive := 1000   -- 10 us at 100 MHz
    );
    port (
        clk         : in  std_logic;
        rst         : in  std_logic;

        dac_resetn  : out std_logic;

        -- to spi_master
        spi_start   : out std_logic;
        spi_read    : out std_logic;
        spi_address : out std_logic_vector(14 downto 0);
        spi_wdata   : out std_logic_vector(7 downto 0);
        spi_busy    : in  std_logic;
        spi_done    : in  std_logic;
        spi_rdata   : in  std_logic_vector(7 downto 0);

        init_done   : out std_logic;
        id_ok       : out std_logic
    );
end entity dac39rf20_init;

architecture rtl of dac39rf20_init is

    type access_t is record
        read_not_wr : std_logic;
        address     : std_logic_vector(14 downto 0);
        data        : std_logic_vector(7 downto 0);   -- write data, or expected read data
    end record;

    type access_list_t is array (natural range <>) of access_t;

    -- Register addresses and values from SBASAO8A, section 8.1.
    constant ACCESSES : access_list_t := (
        ('0', 15x"0002", x"00"),   -- DEVICE_CONFIG: MODE = normal operation
        ('1', 15x"0003", x"04"),   -- CHIP_TYPE   reads 0x04 (high-speed DAC)
        ('1', 15x"0004", x"3C"),   -- CHIP_ID     low byte reads 0x3C
        ('1', 15x"000C", x"51"),   -- VENDOR_ID   low byte reads 0x51
        ('1', 15x"000D", x"04")    -- VENDOR_ID   high byte reads 0x04
    );

    type state_t is (HOLD_RESET, WAKE, ISSUE, WAIT_DONE, FINISHED);
    signal state : state_t := HOLD_RESET;

    signal wait_count  : natural range 0 to WAKE_CLOCKS := 0;
    signal index       : natural range 0 to ACCESSES'length - 1 := 0;

    signal resetn_q    : std_logic := '0';
    signal start_q     : std_logic := '0';
    signal all_match_q : std_logic := '1';
    signal done_q      : std_logic := '0';

begin

    dac_resetn  <= resetn_q;
    spi_start   <= start_q;
    spi_read    <= ACCESSES(index).read_not_wr;
    spi_address <= ACCESSES(index).address;
    spi_wdata   <= ACCESSES(index).data;
    init_done   <= done_q;
    id_ok       <= done_q and all_match_q;

    process (clk)
    begin
        if rising_edge(clk) then
            start_q <= '0';

            if rst = '1' then
                state       <= HOLD_RESET;
                wait_count  <= 0;
                index       <= 0;
                resetn_q    <= '0';
                all_match_q <= '1';
                done_q      <= '0';
            else
                case state is

                    when HOLD_RESET =>
                        resetn_q <= '0';
                        if wait_count = RESET_CLOCKS - 1 then
                            wait_count <= 0;
                            resetn_q   <= '1';
                            state      <= WAKE;
                        else
                            wait_count <= wait_count + 1;
                        end if;

                    when WAKE =>
                        if wait_count = WAKE_CLOCKS - 1 then
                            wait_count <= 0;
                            state      <= ISSUE;
                        else
                            wait_count <= wait_count + 1;
                        end if;

                    when ISSUE =>
                        if spi_busy = '0' then
                            start_q <= '1';
                            state   <= WAIT_DONE;
                        end if;

                    when WAIT_DONE =>
                        if spi_done = '1' then
                            if ACCESSES(index).read_not_wr = '1' and spi_rdata /= ACCESSES(index).data then
                                all_match_q <= '0';
                            end if;
                            if index = ACCESSES'length - 1 then
                                state <= FINISHED;
                            else
                                index <= index + 1;
                                state <= ISSUE;
                            end if;
                        end if;

                    when FINISHED =>
                        done_q <= '1';

                end case;
            end if;
        end if;
    end process;

end architecture rtl;
