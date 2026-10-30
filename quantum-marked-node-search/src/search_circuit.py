"""
search_circuit.py  -  Part B: Qiskit circuit (with shots and noise)

What it is used for
  1. Builds the 2-qubit Grover circuit (4 nodes, marked node = 11):
     Hadamard -> oracle (CZ) -> diffusion -> measure.
  2. Runs it 1024 times on the Aer simulator and compares the result with
     the exact answer from Part A (total variation distance, TVD).
  3. Noise test: adds depolarizing gate errors at four levels and measures
     how often the marked node is still found.
  4. Runs the same circuit with the noise copied from a real IBM chip
     (FakeBrisbane), after fitting it onto that chip's native gates.

Run:  python src/search_circuit.py
"""
import csv
import os

import matplotlib
matplotlib.use("Agg")            # save the plots as files (no window needed)
import matplotlib.pyplot as plt
from qiskit import QuantumCircuit, transpile
from qiskit.quantum_info import Statevector
from qiskit.visualization import plot_histogram
from qiskit_aer import AerSimulator
from qiskit_aer.noise import NoiseModel, depolarizing_error

try:                              # needed only for the fake IBM chip part
    from qiskit_ibm_runtime.fake_provider import FakeBrisbane
except ImportError:
    FakeBrisbane = None

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
FIG = os.path.join(ROOT, "figures")
RES = os.path.join(ROOT, "results")
os.makedirs(FIG, exist_ok=True)
os.makedirs(RES, exist_ok=True)

SHOTS = 1024
SEED = 1                          # fixed seed so the run can be repeated exactly
STATES = ["00", "01", "10", "11"]


def build_grover_circuit(measure=True):
    """2-qubit Grover circuit: marked node is |11>."""
    qc = QuantumCircuit(2, 2)

    qc.h([0, 1])                  # equal start
    qc.barrier(label="start")

    qc.cz(0, 1)                   # oracle: marks node |11>
    qc.barrier(label="oracle")

    qc.h([0, 1])                  # diffusion (spreading step)
    qc.x([0, 1])
    qc.cz(0, 1)
    qc.x([0, 1])
    qc.h([0, 1])
    qc.barrier(label="diffusion")

    if measure:
        qc.measure([0, 1], [0, 1])
    return qc


def ideal_distribution():
    """Exact answer from the statevector (no shots)."""
    d = Statevector.from_instruction(build_grover_circuit(measure=False)).probabilities_dict()
    return {s: round(float(d.get(s, 0.0)), 6) for s in STATES}


def tvd(counts, shots, ideal):
    """Total variation distance: 0 = same as ideal, 1 = completely different."""
    return 0.5 * sum(abs(counts.get(s, 0) / shots - ideal[s]) for s in STATES)


def depolarizing_noise_model(p1, p2):
    noise = NoiseModel()
    noise.add_all_qubit_quantum_error(depolarizing_error(p1, 1), ["h", "x"])
    noise.add_all_qubit_quantum_error(depolarizing_error(p2, 2), ["cz"])
    return noise


def main():
    qc = build_grover_circuit()
    ideal = ideal_distribution()
    rows = []                     # saved to results/circuit_results.csv

    # ---- 1. Circuit diagram ----
    qc.draw("mpl").savefig(os.path.join(FIG, "fig5_grover_circuit.png"),
                           dpi=200, bbox_inches="tight")

    # ---- 2. Aer simulator, no noise ----
    sim = AerSimulator()
    counts = sim.run(transpile(qc, sim), shots=SHOTS, seed_simulator=SEED).result().get_counts()
    print(f"=== Circuit (AerSimulator, {SHOTS} shots, no noise) vs exact ===")
    print("counts       :", dict(sorted(counts.items())))
    print("exact answer :", ideal)
    print(f"success rate : {counts.get('11', 0) / SHOTS:.3f}   TVD vs exact: {tvd(counts, SHOTS, ideal):.4f}")
    rows.append(["Aer, no noise", "", counts.get("11", 0), SHOTS,
                 round(counts.get("11", 0) / SHOTS, 4), round(tvd(counts, SHOTS, ideal), 4)])
    plot_histogram(counts).savefig(os.path.join(FIG, "fig6_histogram.png"),
                                   dpi=200, bbox_inches="tight")

    # ---- 3. Noise test (depolarizing) ----
    levels = [("none", 0.0, 0.0), ("low", 0.001, 0.01),
              ("medium", 0.01, 0.05), ("high", 0.03, 0.10)]
    rates = []
    print("\n=== Noise test (depolarizing errors) ===")
    print(f"{'noise':<8}{'1q error':>9}{'2q error':>10}{'success':>14}{'rate':>9}{'TVD':>8}")
    for name, p1, p2 in levels:
        noisy = AerSimulator(noise_model=depolarizing_noise_model(p1, p2))
        c = noisy.run(transpile(qc, noisy), shots=SHOTS, seed_simulator=SEED).result().get_counts()
        ok = c.get("11", 0)
        rates.append(ok / SHOTS)
        print(f"{name:<8}{p1:>9.3f}{p2:>10.3f}{f'{ok}/{SHOTS}':>14}{ok / SHOTS:>9.3f}{tvd(c, SHOTS, ideal):>8.3f}")
        rows.append([f"Depolarizing noise: {name}", f"{p1}/{p2}", ok, SHOTS,
                     round(ok / SHOTS, 4), round(tvd(c, SHOTS, ideal), 4)])

    plt.figure(figsize=(6, 4))
    plt.bar([n for n, _, _ in levels], rates)
    plt.ylabel("Chance of finding the marked node (11)")
    plt.xlabel("Noise level")
    plt.ylim(0, 1.05)
    plt.title("Grover circuit under simulated depolarizing noise")
    plt.savefig(os.path.join(FIG, "fig7_noise_levels.png"), dpi=200, bbox_inches="tight")
    plt.close()

    # ---- 4. Fake IBM chip (noise copied from FakeBrisbane) ----
    if FakeBrisbane is not None:
        backend = FakeBrisbane()
        fake = AerSimulator.from_backend(backend)
        tqc = transpile(qc, backend, optimization_level=3, seed_transpiler=28)
        two_q = sum(v for k, v in tqc.count_ops().items() if k in ("ecr", "cx", "cz"))
        c = fake.run(tqc, shots=SHOTS, seed_simulator=SEED).result().get_counts()
        ok = c.get("11", 0)
        print("\n=== Fake IBM Brisbane (noise copied from a real 127-qubit chip) ===")
        print(f"two-qubit gates after fitting to the chip: {two_q}   circuit depth: {tqc.depth()}")
        print("counts       :", dict(sorted(c.items())))
        print(f"success rate : {ok / SHOTS:.3f}   TVD vs exact: {tvd(c, SHOTS, ideal):.4f}")
        rows.append(["Fake IBM Brisbane", f"{two_q} two-qubit gates", ok, SHOTS,
                     round(ok / SHOTS, 4), round(tvd(c, SHOTS, ideal), 4)])
        plot_histogram(c).savefig(os.path.join(FIG, "fig8_fake_brisbane.png"),
                                  dpi=200, bbox_inches="tight")
    else:
        print("\n(qiskit-ibm-runtime not installed - fake IBM chip part skipped)")

    # ---- Save table ----
    with open(os.path.join(RES, "circuit_results.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["setting", "error_or_gates", "marked_node_hits", "shots", "success_rate", "tvd"])
        w.writerows(rows)

    print("\nFigures saved in figures/, table saved in results/circuit_results.csv")


if __name__ == "__main__":
    main()
