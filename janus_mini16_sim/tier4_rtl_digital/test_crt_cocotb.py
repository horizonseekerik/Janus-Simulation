"""
ALGORITHM 4C: COCOTB TESTBENCH (JANUS TIER 4 TOP INTEGRATION)
============================================================
Cycle-accurate Co-Simulation of the JANUS Mini 16-Tile RTL Top:
  - DUT: janus_tier4_top (RNS Encoder + CRT Tree + Delay Lines + JIR Monitor)
  - Directly addresses Red-Team Findings #4, #5, #9, #45, #46, #47.
  - Generates 1000 randomized 64-bit vectors with fixed reproducible seed.
  - Verifies exact 12-clock-cycle pipeline latency (no loose polling).
  - Asserts bit-exact 64-bit reconstruction and healthy JIR status.
"""

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer, ReadOnly
import random
import sys
import os
from collections import deque

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


@cocotb.test()
async def test_pipelined_crt_reconstruction(dut):
    """Verifies 1000 randomized 64-bit vectors through janus_tier4_top with exact latency."""

    # Set and log deterministic seed for reproducibility
    seed = 0x1A2B3C4D
    random.seed(seed)
    dut._log.info(f"[SEED] Using reproducible PRNG seed: 0x{seed:08X}")

    # Generate 100 GHz simulation clock (period = 10 ps => 5 ps high, 5 ps low)
    clock = Clock(dut.clk, 10, unit="ps")
    cocotb.start_soon(clock.start())

    # Reset sequence
    dut.rst_n.value = 0
    dut.in_valid.value = 0
    dut.in_X.value = 0
    await Timer(20, unit="ps")
    dut.rst_n.value = 1
    await RisingEdge(dut.clk)

    num_vectors = 1000
    dut._log.info(f"[START] Streaming {num_vectors} randomized 64-bit test vectors...")

    # Cycle-exact transaction queue (12-cycle pipeline latency)
    # Each entry is (expected_valid, expected_value)
    pipeline_q = deque([(0, 0)] * 12, maxlen=12)

    passed_count = 0
    errors = 0

    # Test stimulus: 1000 vectors followed by 15 drain cycles
    total_cycles = num_vectors + 15

    for cycle in range(total_cycles):
        if cycle < num_vectors:
            val = random.randint(0, 2**64 - 1)
            dut.in_valid.value = 1
            dut.in_X.value = val
            pipeline_q.append((1, val))
        else:
            dut.in_valid.value = 0
            dut.in_X.value = 0
            pipeline_q.append((0, 0))

        await RisingEdge(dut.clk)
        await Timer(1, unit="ps")

        # The item emerging after exactly 12 cycles
        exp_valid, exp_val = pipeline_q[0]

        # Verify exact cycle latency and validity
        actual_valid = int(dut.out_valid.value)
        assert actual_valid == exp_valid, (
            f"Latency/valid error at cycle {cycle}: expected out_valid={exp_valid}, got {actual_valid}"
        )

        if exp_valid:
            actual_val = int(dut.out_X.value)
            if actual_val != exp_val:
                dut._log.error(f"Mismatch at cycle {cycle}: Expected 0x{exp_val:016X}, Got 0x{actual_val:016X}")
                errors += 1
            else:
                passed_count += 1

            # Under healthy traffic, JIR fault_detected must remain 0
            assert int(dut.fault_detected.value) == 0, (
                f"Spurious fault detected on healthy traffic at cycle {cycle}!"
            )

    assert errors == 0, f"Encountered {errors} mismatches!"
    assert passed_count == num_vectors, f"Checked {passed_count}/{num_vectors} vectors!"
    dut._log.info(f"[PASS] Successfully verified {passed_count}/{num_vectors} vectors with exact 12-cycle latency.")
