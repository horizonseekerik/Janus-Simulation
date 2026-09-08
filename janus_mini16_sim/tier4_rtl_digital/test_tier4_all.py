"""
Automated Pytest & Icarus Verilog Runner for Tier 4 Digital RTL.
Directly addresses Red-Team Findings #8, #33, #36, #37, #41, #43, #44.

Executes 5 Independent Verification Testbenches:
  1. tb_crt_adder_tree: 12-cycle pipeline latency, corner cases, bubble stress, and mid-stream reset.
  2. tb_audit_stress: 1000 randomized 64-bit vectors with fixed reproducible seed.
  3. tb_rns_standalone: Standalone 16-channel modulo encoder verification.
  4. tb_crt_standalone: Standalone 140-bit CRT tree verification from external residues.
  5. tb_jir_fault_injection: Systematic fault injection campaign (Compute, Red0, Red1, Recovery).
"""

import subprocess
import os
import shutil
try:
    import pytest
except ImportError:
    class MockPytest:
        @staticmethod
        def skip(msg):
            print(f"SKIPPED: {msg}")
    pytest = MockPytest()

TIER4_DIR = os.path.dirname(os.path.abspath(__file__))
IVERILOG = shutil.which("iverilog") or (
    "/mnt/c/iverilog/bin/iverilog.exe" if os.path.exists("/mnt/c/iverilog/bin/iverilog.exe") else r"C:\iverilog\bin\iverilog.exe"
)
VVP = shutil.which("vvp") or (
    "/mnt/c/iverilog/bin/vvp.exe" if os.path.exists("/mnt/c/iverilog/bin/vvp.exe") else r"C:\iverilog\bin\vvp.exe"
)


def _run_tb(testbench_name: str, src_filenames: list, pass_token: str, expected_error_token: str = "Errors=0"):
    if not os.path.exists(IVERILOG) or not os.path.exists(VVP):
        pytest.skip("Icarus Verilog toolchain is missing")

    is_windows_exe = IVERILOG.endswith(".exe")

    def to_tool_path(p: str) -> str:
        if is_windows_exe and p.startswith("/mnt/c/"):
            return "C:\\" + p[7:].replace("/", "\\")
        return p

    vvp_out = os.path.join(TIER4_DIR, f"{testbench_name}.vvp")
    src_paths = [os.path.join(TIER4_DIR, f) for f in src_filenames]

    # Step 1: Compile with iverilog (including TIER4_DIR for `include resolution)
    compile_cmd = [
        IVERILOG, "-g2012", "-I", to_tool_path(TIER4_DIR), "-o", to_tool_path(vvp_out)
    ] + [to_tool_path(f) for f in src_paths]
    comp_res = subprocess.run(compile_cmd, capture_output=True, text=True)
    assert comp_res.returncode == 0, f"Compilation failed for {testbench_name}:\n{comp_res.stderr}"

    # Step 2: Execute with vvp
    sim_res = subprocess.run([VVP, to_tool_path(vvp_out)], capture_output=True, text=True)
    assert sim_res.returncode == 0, f"Simulation runtime error in {testbench_name}:\n{sim_res.stderr}\n{sim_res.stdout}"
    assert pass_token in sim_res.stdout, f"Verification pass token '{pass_token}' missing from stdout:\n{sim_res.stdout}"
    assert expected_error_token in sim_res.stdout, f"Error token check failed in stdout:\n{sim_res.stdout}"
    print(f"\n[PASS] {testbench_name} completed successfully.")


def test_tb_crt_adder_tree():
    """12-cycle pipeline, non-circular JIR, bubbles, and mid-stream reset."""
    _run_tb(
        "tb_crt",
        ["rns_encoder.v", "crt_adder_tree.v", "jir_fault_monitor.v", "tb_crt_adder_tree.v"],
        "[PASS] 100% Bit-Exact 64-Bit RTL Reconstruction",
        "Errors=0"
    )


def test_tb_audit_stress_1000_vectors():
    """1000 random vectors stress audit with non-circular delay-matched redundant residues."""
    _run_tb(
        "tb_audit_stress",
        ["rns_encoder.v", "crt_adder_tree.v", "jir_fault_monitor.v", "tb_audit_stress.v"],
        "[AUDIT_PASS] 1000/1000 random vectors passed",
        "Errors=0"
    )


def test_tb_rns_standalone():
    """Standalone 16-channel RNS encoder bit-exact modulo reduction."""
    _run_tb(
        "tb_rns_standalone",
        ["rns_encoder.v", "tb_rns_standalone.v"],
        "[PASS] 100% Bit-Exact Modulo Reduction",
        "Errors=0"
    )


def test_tb_crt_standalone():
    """Standalone 8-stage CRT tree reconstruction from external residues."""
    _run_tb(
        "tb_crt_standalone",
        ["crt_adder_tree.v", "tb_crt_standalone.v"],
        "[PASS] 100% Bit-Exact 64-Bit CRT Reconstruction",
        "Errors=0"
    )


def test_tb_jir_fault_injection_campaign():
    """Comprehensive fault matrix: Compute fault, Red0 fault, Red1 fault, Recovery."""
    _run_tb(
        "tb_jir_fault_injection",
        ["rns_encoder.v", "crt_adder_tree.v", "jir_fault_monitor.v", "tb_jir_fault_injection.v"],
        "[PASS] 100% Fault Matrix Coverage under Single-Fault Assumption (SFA).",
        "Errors=0"
    )


def test_cocotb_top_simulation():
    """Runs the 1000-vector cocotb co-simulation against janus_tier4_top."""
    try:
        from cocotb_tools.runner import get_runner
    except ImportError:
        pytest.skip("cocotb_tools runner not available")

    if not os.path.exists(IVERILOG):
        pytest.skip("Icarus Verilog compiler not found")

    runner = get_runner("icarus")
    sources = [
        os.path.join(TIER4_DIR, f) for f in [
            "rns_encoder.v", "crt_adder_tree.v", "jir_fault_monitor.v", "janus_tier4_top.v"
        ]
    ]
    sim_build_dir = os.path.join(TIER4_DIR, "sim_build")
    runner.build(
        sources=sources,
        hdl_toplevel="janus_tier4_top",
        build_args=["-g2012", f"-I{TIER4_DIR}"],
        always=False,
        build_dir=sim_build_dir
    )
    runner.test(
        hdl_toplevel="janus_tier4_top",
        test_module="test_crt_cocotb",
        test_dir=TIER4_DIR,
        build_dir=sim_build_dir
    )


if __name__ == "__main__":
    test_tb_crt_adder_tree()
    test_tb_audit_stress_1000_vectors()
    test_tb_rns_standalone()
    test_tb_crt_standalone()
    test_tb_jir_fault_injection_campaign()
    test_cocotb_top_simulation()
