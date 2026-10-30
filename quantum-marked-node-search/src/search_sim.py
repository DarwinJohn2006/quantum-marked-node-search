"""
search_sim.py  -  Part A: exact simulation (no shots needed)

What it is used for
  1. Grover search on 4 nodes (n = 2) and 8 nodes (n = 3): the oracle marks
     node |11..1> and we read the exact probability of that node after every
     Grover iteration (statevector simulation).
  2. Coined quantum walk on a cycle of 4 and 8 nodes: an oracle (a different
     coin at the marked node) is added and we follow the probability of the
     marked node over 30 steps.
  3. Classical random walk on the same cycle: average hitting time of the
     marked node, compared with the formula (N^2 - 1) / 6.
  4. Validation checks, saved plots and saved result tables.

Run:  python src/search_sim.py
"""
import csv
import os

import matplotlib
matplotlib.use("Agg")            # save the plots as files (no window needed)
import matplotlib.pyplot as plt
import numpy as np
from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
FIG = os.path.join(ROOT, "figures")
RES = os.path.join(ROOT, "results")
os.makedirs(FIG, exist_ok=True)
os.makedirs(RES, exist_ok=True)


# ----------------------------------------------------------------------------
# 1. Grover search (statevector)
# ----------------------------------------------------------------------------
def flip_marked(qc, n):
    """Flips the sign of the marked state |11...1>."""
    if n == 2:
        qc.cz(0, 1)
    elif n == 3:
        qc.h(2); qc.ccx(0, 1, 2); qc.h(2)
    else:
        raise ValueError("only n = 2 or n = 3 is built here")


def oracle(qc, n):
    flip_marked(qc, n)


def spread(qc, n):
    """Diffusion: spreads (reflects) amplitude about the average."""
    qc.h(range(n)); qc.x(range(n))
    flip_marked(qc, n)
    qc.x(range(n)); qc.h(range(n))


def grover_probs(n, steps=7):
    """Exact probability of the marked node after 0, 1, ..., steps iterations."""
    marked = 2**n - 1
    qc = QuantumCircuit(n)
    qc.h(range(n))                                   # equal start
    probs = [Statevector.from_instruction(qc).probabilities()[marked]]
    for _ in range(steps):
        oracle(qc, n)
        spread(qc, n)
        probs.append(Statevector.from_instruction(qc).probabilities()[marked])
    return np.array(probs)


def grover_theory(n, steps=7):
    """Textbook formula: sin^2((2k + 1) * theta), with sin(theta) = 1/sqrt(N)."""
    theta = np.arcsin(1 / np.sqrt(2**n))
    return np.array([np.sin((2 * k + 1) * theta) ** 2 for k in range(steps + 1)])


def plot_grover(n, probs, theory, fig_name):
    plt.figure(figsize=(6, 4))
    plt.plot(range(len(probs)), probs, marker="o", label="Simulation")
    plt.plot(range(len(theory)), theory, linestyle=":", color="gray", label="Theory")
    plt.xlabel("Number of Grover iterations")
    plt.ylabel("Probability of marked node")
    plt.title(f"Grover search on {2**n} nodes (n = {n})")
    plt.grid(True)
    plt.legend()
    plt.savefig(os.path.join(FIG, fig_name), dpi=200, bbox_inches="tight")
    plt.close()


# ----------------------------------------------------------------------------
# 2. Quantum walk on a cycle (marked node = different coin)
# ----------------------------------------------------------------------------
def quantum_walk(N, marked=0, steps=30):
    """State = (coin, node). Coin 0 = move right, coin 1 = move left."""
    H = np.array([[1, 1], [1, -1]]) / np.sqrt(2)

    shift = np.zeros((2 * N, 2 * N))
    coin = np.zeros((2 * N, 2 * N))
    for x in range(N):
        shift[(x + 1) % N, x] = 1              # right-movers go to the next node
        shift[N + (x - 1) % N, N + x] = 1      # left-movers go to the previous node
        c = H if x != marked else -np.eye(2)   # the oracle: a different coin at the marked node
        for a in range(2):
            for b in range(2):
                coin[a * N + x, b * N + x] = c[a, b]

    U = shift @ coin                           # one step = coin, then move

    psi = np.ones(2 * N) / np.sqrt(2 * N)      # equal start
    probs = []
    for _ in range(steps + 1):
        probs.append(abs(psi[marked]) ** 2 + abs(psi[N + marked]) ** 2)
        psi = U @ psi
    return np.array(probs), U, float(np.linalg.norm(psi))


def classical_hitting(N, marked=0, trials=20000, seed=1):
    """Average number of steps a classical random walker needs to reach the marked node."""
    rng = np.random.default_rng(seed)

    def hitting_time(start):
        pos, t = start, 0
        while pos != marked:
            pos = (pos + rng.choice([-1, 1])) % N
            t += 1
        return t

    return float(np.mean([hitting_time(rng.integers(N)) for _ in range(trials)]))


def plot_walk(N, q_probs, avg, fig_name):
    plt.figure(figsize=(6, 4))
    plt.plot(q_probs, marker="o", label="Quantum walk")
    plt.axhline(1 / N, color="gray", linestyle="--", label="Starting probability 1/N")
    plt.axvline(avg, color="red", linestyle=":", label="Classical average hitting time")
    plt.xlabel("Step")
    plt.ylabel("Probability of marked node")
    plt.title(f"Quantum walk on a cycle of {N} nodes")
    plt.legend(loc="upper left", bbox_to_anchor=(1, 1))
    plt.grid(True)
    plt.savefig(os.path.join(FIG, fig_name), dpi=200, bbox_inches="tight")
    plt.close()


# ----------------------------------------------------------------------------
# 3. Run everything, validate, save
# ----------------------------------------------------------------------------
def main():
    checks = []          # (name, expected, got, ok)

    def check(name, expected, got, tol):
        ok = abs(expected - got) <= tol
        checks.append((name, expected, got, ok))

    # ---- Grover ----
    grover_rows = []
    grover = {}
    for n, fig_name in ((2, "fig1_grover_n2.png"), (3, "fig2_grover_n3.png")):
        probs = grover_probs(n)
        theory = grover_theory(n)
        grover[n] = probs
        plot_grover(n, probs, theory, fig_name)
        print(f"\n=== Grover search, n = {n} ({2**n} nodes) ===")
        print("iterations  probability(sim)  probability(theory)")
        for k, (p, t) in enumerate(zip(probs, theory)):
            print(f"{k:>10}  {p:>16.3f}  {t:>19.3f}")
            grover_rows.append([2**n, k, round(p, 6), round(t, 6)])
        check(f"Grover n={n}: simulation vs theory (largest difference)", 0.0,
              float(np.max(np.abs(probs - theory))), 1e-9)

    check("Grover n=2: probability after 1 iteration", 1.0, grover[2][1], 1e-9)
    check("Grover n=3: probability after 2 iterations", float(grover_theory(3)[2]),
          grover[3][2], 1e-9)

    # ---- Quantum walk + classical walk ----
    walk_rows = []
    for N, fig_name in ((4, "fig3_walk_N4.png"), (8, "fig4_walk_N8.png")):
        q_probs, U, norm = quantum_walk(N)
        avg = classical_hitting(N)
        theory = (N**2 - 1) / 6
        plot_walk(N, q_probs, avg, fig_name)
        best = int(np.argmax(q_probs))
        print(f"\n=== Quantum walk and classical walk, N = {N} nodes ===")
        print(f"Start probability of marked node : {q_probs[0]:.3f}")
        print(f"Best quantum probability         : {q_probs[best]:.3f} at step {best} (window = 30 steps)")
        print(f"Classical average hitting time   : {avg:.2f}  (theory (N^2-1)/6 = {theory:.2f})")
        for t, p in enumerate(q_probs):
            walk_rows.append([N, t, round(p, 6)])
        check(f"N={N}: walk operator is unitary (U^T U = I)", 0.0,
              float(np.max(np.abs(U.T @ U - np.eye(2 * N)))), 1e-12)
        check(f"N={N}: total probability stays 1 after 30 steps", 1.0, norm, 1e-9)
        check(f"N={N}: classical hitting time vs (N^2-1)/6", theory, avg, 0.1 * theory)

    # ---- Validation table ----
    print("\n=== Validation ===")
    print(f"{'check':<58}{'expected':>10}{'got':>10}  ok")
    for name, expected, got, ok in checks:
        print(f"{name:<58}{expected:>10.4f}{got:>10.4f}  {'Yes' if ok else 'NO'}")

    # ---- Save tables ----
    with open(os.path.join(RES, "sim_grover.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["nodes", "iterations", "probability_simulated", "probability_theory"])
        w.writerows(grover_rows)
    with open(os.path.join(RES, "sim_walk.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["nodes", "step", "marked_node_probability"])
        w.writerows(walk_rows)
    with open(os.path.join(RES, "sim_validation.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["check", "expected", "got", "ok"])
        for name, expected, got, ok in checks:
            w.writerow([name, round(expected, 6), round(got, 6), "Yes" if ok else "NO"])

    print("\nFigures saved in figures/, tables saved in results/")


if __name__ == "__main__":
    main()
