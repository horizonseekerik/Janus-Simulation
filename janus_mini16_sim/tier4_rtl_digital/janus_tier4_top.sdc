# ==============================================================================
# PROJECT JANUS MINI (16-TILE): SYNOPSYS DESIGN CONSTRAINTS (SDC)
# ==============================================================================
# Target Top-Level Module: janus_tier4_top
# Baseline Standard-Cell Target Frequency: 1.0 GHz (1000.0 ps period)
# High-Performance Target Corner: 2.0 GHz (500.0 ps period) / 3.0 GHz (333.3 ps)
# Addresses Red-Team Audit Findings #10, #19, #51.
# ==============================================================================

# 1. Primary Clock Definition (Baseline 1.0 GHz)
create_clock -name clk -period 1.000 [get_ports clk]

# Clock Characterization: 30 ps skew/jitter uncertainty, 20 ps slew
set_clock_uncertainty 0.030 [get_clocks clk]
set_clock_transition  0.020 [get_clocks clk]

# 2. Asynchronous Active-Low Reset
set_false_path -from [get_ports rst_n]

# 3. Input Port Constraints
# External inputs arrive with <= 100 ps delay from upstream optoelectronic StrongARM latch
set_input_delay -clock clk -max 0.100 [get_ports {in_valid in_X[*]}]
set_input_delay -clock clk -min 0.020 [get_ports {in_valid in_X[*]}]

# Standard CMOS input driving buffer
set_driving_cell -lib_cell BUFX4 [get_ports {in_valid in_X[*]}]

# 4. Output Port Constraints
# Outputs must meet 100 ps external setup time to downstream routing/host interface
set_output_delay -clock clk -max 0.100 [get_ports {out_valid out_X[*] fault_detected fault_channel_id[*]}]
set_output_delay -clock clk -min 0.010 [get_ports {out_valid out_X[*] fault_detected fault_channel_id[*]}]

# Standard cell capacitive load (10 fF per output pad/trace)
set_load 0.010 [get_ports {out_valid out_X[*] fault_detected fault_channel_id[*]}]

# 5. Design Rule Constraints
set_max_fanout 16 [current_design]
set_max_transition 0.050 [current_design]

# 6. Operating Corner Annotations
# TSMC 7nm FinFET (Typical-Typical, VDD=0.75V, T=25C):
#   - Expected Stage Propagation Delay: t_prop <= 280 ps
#   - Worst Setup Slack @ 1.0 GHz (1000 ps): +690 ps
#   - Worst Setup Slack @ 2.0 GHz (500 ps) : +190 ps
#   - Estimated Maximum Frequency F_max    : ~3.2 GHz
