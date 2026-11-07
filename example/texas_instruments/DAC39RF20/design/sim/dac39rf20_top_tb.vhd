--------------------------------------------------------------------------------
-- dac39rf20_top_tb
--
-- Runs dac39rf20_top against a behavioural model of the DAC39RF20 standard
-- SPI interface.  The model holds the identification registers, drives SDO
-- with the worst-case output delay (tOD = 6.4 ns) after the falling edge of
-- SCLK, and checks the SDI and SCS setup and hold times from the datasheet.
--------------------------------------------------------------------------------
library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity dac39rf20_top_tb is
end entity dac39rf20_top_tb;

architecture sim of dac39rf20_top_tb is

    constant CLK_PERIOD : time := 10 ns;

    -- SBASAO8A, section 6.9
    constant T_P   : time := 66 ns;    -- min SCLK period
    constant T_SU  : time := 3.2 ns;   -- SDI setup to SCLK rising
    constant T_H   : time := 1.0 ns;   -- SDI hold from SCLK rising
    constant T_OD  : time := 6.4 ns;   -- SDO output delay from SCLK falling (max)
    constant T_CSS : time := 3.2 ns;   -- SCS setup to SCLK rising

    signal clk_100m   : std_logic := '0';
    signal btn_reset  : std_logic := '1';
    signal dac_sclk   : std_logic;
    signal dac_sdi    : std_logic;
    signal dac_sdo    : std_logic := 'Z';
    signal dac_scs_n  : std_logic;
    signal dac_resetn : std_logic;
    signal led_done   : std_logic;
    signal led_id_ok  : std_logic;

    signal finished   : boolean := false;

begin

    clk_100m <= not clk_100m after CLK_PERIOD / 2 when not finished;

    dut : entity work.dac39rf20_top
        port map (
            clk_100m   => clk_100m,
            btn_reset  => btn_reset,
            dac_sclk   => dac_sclk,
            dac_sdi    => dac_sdi,
            dac_sdo    => dac_sdo,
            dac_scs_n  => dac_scs_n,
            dac_resetn => dac_resetn,
            led_done   => led_done,
            led_id_ok  => led_id_ok
        );

    ----------------------------------------------------------------------------
    -- DAC39RF20 SPI model
    ----------------------------------------------------------------------------
    dac_model : process
        type reg_map_t is array (0 to 15) of std_logic_vector(7 downto 0);
        variable regs       : reg_map_t := (
            16#0# => x"30", 16#2# => x"00", 16#3# => x"04", 16#4# => x"3C",
            16#5# => x"00", 16#6# => x"01", 16#C# => x"51", 16#D# => x"04",
            others => x"00");
        variable frame      : std_logic_vector(23 downto 0);
        variable bit_count  : natural;
        variable read_value : std_logic_vector(7 downto 0);
        variable address    : natural;
        variable is_read    : boolean;
        variable last_rise  : time := 0 ns;
        variable scs_fall   : time;
    begin
        dac_sdo <= 'Z';
        wait until falling_edge(dac_scs_n);
        scs_fall  := now;
        bit_count := 0;
        assert dac_resetn = '1' report "SPI access while the DAC is in reset" severity error;

        while dac_scs_n = '0' loop
            wait until rising_edge(dac_sclk) or rising_edge(dac_scs_n);
            exit when dac_scs_n = '1';

            -- SCLK rising edge: check timing, sample SDI
            if bit_count = 0 then
                assert now - scs_fall >= T_CSS report "tCSS violated" severity error;
            else
                assert now - last_rise >= T_P report "SCLK period below tP" severity error;
            end if;
            assert dac_sdi'stable(T_SU) report "SDI setup (tSU) violated" severity error;
            last_rise := now;
            frame     := frame(22 downto 0) & dac_sdi;
            bit_count := bit_count + 1;

            wait for T_H;
            assert dac_sdi'stable(T_H) report "SDI hold (tH) violated" severity error;

            -- after the address field of a read, drive data on each falling edge
            if bit_count = 16 then
                is_read    := frame(15) = '1';
                address    := to_integer(unsigned(frame(14 downto 0)));
                read_value := regs(address mod 16);
            end if;
            if bit_count >= 16 and bit_count < 24 and is_read then
                wait until falling_edge(dac_sclk);
                dac_sdo    <= 'X', read_value(7) after T_OD;
                read_value := read_value(6 downto 0) & '0';
            end if;
        end loop;

        if bit_count = 24 and frame(23) = '0' then
            regs(to_integer(unsigned(frame(22 downto 8))) mod 16) := frame(7 downto 0);
        end if;
        assert bit_count = 24 report "access was not 24 bits" severity error;
    end process dac_model;

    ----------------------------------------------------------------------------
    -- Stimulus
    ----------------------------------------------------------------------------
    stimulus : process
    begin
        btn_reset <= '1';
        wait for 100 ns;
        btn_reset <= '0';
        wait until led_done = '1' for 100 us;
        assert led_done = '1'  report "start-up did not finish"          severity failure;
        assert led_id_ok = '1' report "identification registers wrong"  severity failure;
        report "PASS: DAC39RF20 start-up finished and the ID matched";
        finished <= true;
        wait;
    end process stimulus;

end architecture sim;
