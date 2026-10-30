"""
real_hardware_run.py  -  Part C: run the Grover circuit on a real IBM quantum computer

What it is used for
  Sends the same 2-qubit Grover circuit (marked node = 11) to the least busy
  real IBM chip, measures it 1024 times and saves the result. The result is
  compared with the exact answer using the total variation distance (TVD):
  0 = same as ideal, 1 = completely different.

Before the first run (one time only):
  1. Make a free account at https://quantum.cloud.ibm.com and copy your API key.
  2. In Python run:
       from qiskit_ibm_runtime import QiskitRuntimeService
       QiskitRuntimeService.save_account(token="YOUR_API_KEY", set_as_default=True, overwrite=True)

Run:        python src/real_hardware_run.py
Fetch later: python src/real_hardware_run.py --job-id <JOB_ID>
"""
import argparse
import csv
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager
from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2 as Sampler

from search_circuit import STATES, build_grover_circuit, ideal_distribution, tvd

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
FIG = os.path.join(ROOT, "figures")
RES = os.path.join(ROOT, "results")
os.makedirs(FIG, exist_ok=True)
os.makedirs(RES, exist_ok=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--shots", type=int, default=1024)
    parser.add_argument("--job-id", default=None, help="fetch the result of an earlier job")
    args = parser.parse_args()

    service = QiskitRuntimeService()          # uses the saved IBM Quantum API key
    two_q = ""

    if args.job_id:
        job = service.job(args.job_id)
        backend_name = job.backend().name
    else:
        backend = service.least_busy(operational=True, simulator=False, min_num_qubits=2)
        backend_name = backend.name
        pm = generate_preset_pass_manager(backend=backend, optimization_level=3, seed_transpiler=28)
        isa = pm.run(build_grover_circuit())  # fit the circuit onto the chip's own gates
        two_q = sum(1 for inst in isa.data if inst.operation.num_qubits == 2)
        print(f"Running on {backend_name}: {two_q} two-qubit gates, depth {isa.depth()}")

        sampler = Sampler(mode=backend)
        sampler.options.default_shots = args.shots
        sampler.options.dynamical_decoupling.enable = True   # helps against dephasing
        job = sampler.run([isa])
        print("Job id:", job.job_id(), "(waiting for the result, this can take a few minutes)")

    counts = job.result()[0].data.c.get_counts()
    shots = sum(counts.values())
    ideal = ideal_distribution()
    hits = counts.get("11", 0)
    distance = tvd(counts, shots, ideal)

    print(f"\n=== Result on {backend_name} ({shots} shots) ===")
    print("counts       :", dict(sorted(counts.items())))
    print(f"success rate : {hits / shots:.3f}   TVD vs ideal: {distance:.3f}")

    # save the table (one row per run)
    path = os.path.join(RES, "real_hardware_runs.csv")
    new = not os.path.exists(path)
    with open(path, "a", newline="") as f:
        w = csv.writer(f)
        if new:
            w.writerow(["backend", "job_id", "two_qubit_gates", "shots", "marked_node_hits", "success_rate", "tvd"])
        w.writerow([backend_name, job.job_id(), two_q, shots, hits, round(hits / shots, 4), round(distance, 4)])

    # save the figure: bars = real chip, dots = ideal answer
    plt.figure(figsize=(6, 4))
    plt.bar(STATES, [counts.get(s, 0) / shots for s in STATES], label=f"{backend_name} (real)")
    plt.plot(STATES, [ideal[s] for s in STATES], "ko", label="Ideal answer")
    plt.xlabel("Measured node")
    plt.ylabel("Probability")
    plt.title(f"Grover circuit on {backend_name}  (TVD = {distance:.2f})")
    plt.legend()
    plt.savefig(os.path.join(FIG, f"fig9_real_hardware_{backend_name}.png"), dpi=200, bbox_inches="tight")
    plt.close()
    print(f"Saved results/real_hardware_runs.csv and figures/fig9_real_hardware_{backend_name}.png")


if __name__ == "__main__":
    main()
