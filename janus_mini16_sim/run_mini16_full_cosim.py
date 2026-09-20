#!/usr/bin/env python3
"""
PROJECT JANUS MINI (16-TILE): MASTER CO-SIMULATION RUNNER
==========================================================
Top-level entrypoint script to execute the full multi-physics co-simulation pipeline,
individual simulation tiers, or evaluate custom numbers & multiplications through the
16-tile spatial RNS optical/CMOS pipeline.

Usage:
    python run_mini16_full_cosim.py --verbose
    python run_mini16_full_cosim.py --tier 1
    python run_mini16_full_cosim.py --val 123456789012345678
    python run_mini16_full_cosim.py --val 0xDEADBEEFCAFEBABE
    python run_mini16_full_cosim.py --mult 123456789 987654321
    python run_mini16_full_cosim.py --interactive
"""

import sys
import os
import argparse

# Ensure project root is in sys.path
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# Master Orchestrator import (Interface updated to handle computed results)
from orchestrator.master_orchestrator import JanusMasterOrchestrator


def parse_custom_int(val_str: str) -> int:
    """Parses integer in decimal or hexadecimal format."""
    val_str = val_str.strip()
    if val_str.lower().startswith("0x"):
        return int(val_str, 16)
    return int(val_str)


def run_interactive_mode(orchestrator: JanusMasterOrchestrator):
    """Interactive CLI to evaluate custom numbers through the RNS/CRT pipeline."""
    print("\n" + "=" * 80)
    print("  PROJECT JANUS MINI (16-TILE): INTERACTIVE CUSTOM INPUT EVALUATOR")
    print("=" * 80)
    print("  Commands:")
    print("    eval <int or hex>       : Decompose into 16 RNS channels & reconstruct via CRT")
    print("    mult <int_a> <int_b>    : Multiply two integers across 16 optical residue tiles")
    print("    exit / quit             : Exit interactive mode")
    print("=" * 80 + "\n")

    while True:
        try:
            line = input("JANUS-RNS> ").strip()
            if not line:
                continue
            if line.lower() in ["exit", "quit", "q"]:
                print("Exiting interactive mode.")
                break

            parts = line.split()
            cmd = parts[0].lower()

            if cmd == "eval" and len(parts) >= 2:
                val = parse_custom_int(parts[1])
                orchestrator.evaluate_custom_integer(val, print_output=True)
            elif cmd == "mult" and len(parts) >= 3:
                a = parse_custom_int(parts[1])
                b = parse_custom_int(parts[2])
                orchestrator.evaluate_custom_multiply(a, b, print_output=True)
            elif cmd.isdigit() or (cmd.startswith("0x") and len(parts) == 1):
                val = parse_custom_int(cmd)
                orchestrator.evaluate_custom_integer(val, print_output=True)
            else:
                print(f"Unknown command: '{line}'. Usage: 'eval <val>' or 'mult <a> <b>'")
        except KeyboardInterrupt:
            print("\nExiting interactive mode.")
            break
        except Exception as e:
            print(f"Error: {e}")


def main():
    parser = argparse.ArgumentParser(
        description="Project JANUS Mini 16-Tile: End-to-End Co-Simulation Master Runner"
    )
    parser.add_argument(
        "--tier",
        type=str,
        default=None,
        choices=["1", "2", "3", "4", "5", "all"],
        help="Simulation tier to execute (1-5 or 'all' for full co-simulation)",
    )
    parser.add_argument(
        "--val",
        type=str,
        default=None,
        help="Evaluate a custom 64-bit integer (decimal or hex e.g. 0x123456789ABCDEF0)",
    )
    parser.add_argument(
        "--mult",
        nargs=2,
        type=str,
        default=None,
        metavar=("A", "B"),
        help="Multiply two custom numbers A and B across the 16-tile spatial RNS engine",
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        default=False,
        help="Launch interactive REPL mode for custom number evaluation",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        default=False,
        help="Enable detailed verbose output for all simulation steps",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Directory to save generated artifacts and reports",
    )
    parser.add_argument(
        "--report",
        type=str,
        default=None,
        help="Custom destination filepath for the markdown verification report",
    )
    parser.add_argument(
        "--switch-topology",
        type=str,
        default="mzi",
        choices=["mzi", "directional_coupler"],
        help="Switch cell topology for Tier 1 ('mzi' [default] or 'directional_coupler')",
    )

    parser.add_argument(
        "--monolithic",
        action="store_true",
        default=False,
        help="Execute the Monolithic Dynamic Multi-Physics Co-Simulation (coupled optical-thermal-electrical DAEs)",
    )
    parser.add_argument(
        "--sim-time-ps",
        type=float,
        default=200.0,
        help="Simulation window in picoseconds for monolithic dynamic co-simulation (default: 200.0 ps)",
    )
    parser.add_argument(
        "--power-area",
        action="store_true",
        default=False,
        help="Execute First-Principles Power Draw and Physical Die Area Audit (100%% component activity)",
    )
    parser.add_argument(
        "--activity-factor",
        type=float,
        default=1.0,
        help="Component switching activity factor for dynamic power calculation (0.0 to 1.0, default: 1.0)",
    )

    args = parser.parse_args()

    orchestrator = JanusMasterOrchestrator(
        verbose=args.verbose,
        output_dir=args.output_dir,
        switch_topology=args.switch_topology,
    )

    # 0. First-Principles Power & Area Audit
    if args.power_area:
        from benchmarks.first_principles_power_and_area import run_first_principles_audit
        print(f"Executing First-Principles Power and Area Audit (Activity Factor: {args.activity_factor * 100:.1f}%)...")
        res = run_first_principles_audit(activity_factor=args.activity_factor)
        p = res["power"]
        a = res["area"]
        print("\n" + "=" * 80)
        print("  PROJECT JANUS MINI-16: FIRST-PRINCIPLES POWER & AREA SUMMARY")
        print("=" * 80)
        print(f"  Die Footprint:                {a['die_dimensions_mm']} mm ({a['total_die_area_mm2']} mm^2)")
        print(f"  Total Power Draw:             {p['total_power_W']} W ({p['total_power_mW']} mW)")
        print(f"    - Laser Electrical Power:   {p['subsystems_mW']['Optical Source']} mW")
        print(f"    - 100-GHz RF Modulators:    {p['subsystems_mW']['Electro-Optics']} mW")
        print(f"    - SAC2M Ge/Si APD Array:    {p['subsystems_mW']['Optoelectronics']} mW")
        print(f"    - 65nm CMOS Base Logic:     {p['subsystems_mW']['65nm CMOS Digital']} mW")
        print(f"    - 1.5 MB SRAM & ROM:        {p['subsystems_mW']['65nm CMOS Memory']} mW")
        print(f"  Active Tile Array Core:       {a['tile_array_core_mm2']} mm^2 ({a['tile_array_core_pct']}% of die)")
        print(f"  Report exported to:           {res['reports']['md_path']}")
        print("=" * 80)
        sys.exit(0)

    # 1. Monolithic Dynamic Co-Simulation
    if args.monolithic:
        print("Starting Monolithic Dynamic Multi-Physics Co-Simulation...")
        res = orchestrator.run_monolithic_dynamic_cosim(sim_time_ps=args.sim_time_ps)
        m = res["metrics"]
        a = res["algorithmic"]
        print("\n" + "=" * 80)
        print("  PROJECT JANUS: MONOLITHIC DYNAMIC CO-SIMULATION SUMMARY")
        print("=" * 80)
        print(f"  Execution Time:               {res['elapsed_time_s']:.3f} s")
        print(f"  Transmitted Bits:             {m['transmitted_bits']}")
        print(f"  Dynamic Optical Margin:       {m['nominal_baseline_margin_dB']} dB (Target: >= +5.0 dB)")
        print(f"  Received Power (Mean ON):     {m['p_rx_mean_on_uW']} uW (Sensitivity: {m['p_sens_uW']} uW)")
        print(f"  Peak Operating Temp:          {m['t_peak_C']} C (Ceiling: <= 70.0 C)")
        print(f"  Max Optical H-Tree Skew:      {m['skew_max_fs']} fs (Budget: <= 100.0 fs)")
        print(f"  Dynamic Eye Opening:          {m['eye_opening_pct']} %")
        print(f"  Dynamic Measured BER:         {m['ber_measured']}")
        print(f"  64-Bit Product Match:         {a['product_match']} ({a['product_ref']} == {a['recovered_product']})")
        print(f"  RRNS Fault Self-Healing:      {a['rrns_healed']} (Corrected: {a['corrected_count']} channels)")
        print("=" * 80)
        sys.exit(0 if a["product_match"] and m["pass_link_margin"] else 1)

    # 1. Custom Single Value
    if args.val is not None:
        val = parse_custom_int(args.val)
        res = orchestrator.evaluate_custom_integer(val, print_output=True)
        sys.exit(0 if res["is_match"] else 1)

    # 2. Custom Multiplication
    if args.mult is not None:
        a = parse_custom_int(args.mult[0])
        b = parse_custom_int(args.mult[1])
        res = orchestrator.evaluate_custom_multiply(a, b, print_output=True)
        sys.exit(0 if res["is_match"] else 1)

    # 3. Interactive Mode
    if args.interactive:
        run_interactive_mode(orchestrator)
        sys.exit(0)

    # 4. Standard Tier / Full Co-Sim Execution
    tier_choice = args.tier or "all"
    if tier_choice == "all":
        results = orchestrator.run_full_cosim()
        if args.report and os.path.exists(results["report_path"]):
            import shutil

            shutil.copy(results["report_path"], args.report)
            print(f"Report copied to: {args.report}")
        sys.exit(0 if results["overall_pass"] else 1)
    else:
        tier_num = int(tier_choice)
        print(f"Running individual Tier {tier_num} simulation...")
        orchestrator.validate_global_constants()
        tier_res = orchestrator.run_tier(tier_num)
        print("\n" + "=" * 80)
        print(f"  TIER {tier_num} VERIFICATION SUMMARY")
        print("=" * 80)
        for c in tier_res["checks"]:
            status_sym = "[PASS]" if c["passed"] else "[FAIL]"
            print(f"  {status_sym} Check {c['id']:02d}: {c['name']}")
            print(f"         Target:   {c['target_spec']} ({c['threshold']})")
            print(f"         Measured: {c['measured_value']}")
            print(f"         Details:  {c['details']}\n")
        print(f"Tier {tier_num} execution completed in {tier_res['execution_time_s']}s.")
        sys.exit(0)


if __name__ == "__main__":
    main()
