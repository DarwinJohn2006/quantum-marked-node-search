# Marked Node Search on a Cycle Graph

**IA-3 Project, 23CS2037 Quantum Computing**
Karunya Institute of Technology and Sciences, Team 27

## About

A cycle graph (a ring) has one marked node. This project uses an oracle to mark
that node and studies how the probability of finding it changes over time. The
result is compared with a classical random walk. Everything is built with
Qiskit and NumPy and run as simulations.

Two quantum methods are used:

- **Grover search** on 4 nodes (2 qubits) and 8 nodes (3 qubits). An oracle marks
  one node, and a diffusion step raises its probability. Each oracle plus
  diffusion pair is one Grover iteration.
- **Quantum walk** on a cycle of 4 and 8 nodes. A coin decides whether the walker
  moves left or right. The marked node gets a different coin, which acts as the
  oracle.

The classical baseline is a random walk. Its average hitting time of the marked
node is compared with the formula (N² - 1) / 6.

## Files

| File | What it does |
|------|--------------|
| `src/search_sim.py` | Exact simulation (no shots). Grover on 4 and 8 nodes, quantum walk on 4 and 8 nodes, classical hitting time, and 10 validation checks |
| `src/search_circuit.py` | Qiskit circuit. The 2-qubit Grover circuit run 1024 times on the Aer simulator, a noise test, and a run with the noise copied from a real IBM chip (FakeBrisbane) |
| `src/real_hardware_run.py` | Optional. Sends the same circuit to a real IBM quantum computer. Written but not run for the report |
| `notebooks/QCIA3.ipynb` | The original Google Colab notebook |
| `figures/` | All graphs and the circuit diagram (fig1 to fig8) |
| `results/` | Result tables (`.csv`) and the saved console output of each run (`.txt`) |

## Folder structure

```
quantum-marked-node-search/
├── README.md
├── requirements.txt
├── .gitignore
├── src/
│   ├── search_sim.py
│   ├── search_circuit.py
│   └── real_hardware_run.py
├── notebooks/
│   └── QCIA3.ipynb
├── figures/
└── results/
```

## How to run

You need Python 3.10 or newer. It was tested with Python 3.14.

1. Download or clone the repo and open a terminal (Command Prompt on Windows)
   inside the project folder.
2. Install the libraries once:
   ```
   pip install -r requirements.txt
   ```
3. Run the two main programs:
   ```
   python src/search_sim.py
   python src/search_circuit.py
   ```

Each program prints its results in the terminal, saves its graphs in `figures/`
and saves its tables in `results/`. The same steps also work in Google Colab
(put `!` before each command).

### Real hardware (optional)

`real_hardware_run.py` needs a free IBM Quantum account and API key. Save the key once:

```python
from qiskit_ibm_runtime import QiskitRuntimeService
QiskitRuntimeService.save_account(token="YOUR_API_KEY", set_as_default=True, overwrite=True)
```

Then run `python src/real_hardware_run.py`. It uses the least busy chip, so it may
wait in a queue. To read the result of an earlier job:
`python src/real_hardware_run.py --job-id <JOB_ID>`.

## Results

| Experiment | Result |
|-----------|--------|
| Grover, 4 nodes | Marked node probability 0.25 to 1.000 after 1 iteration |
| Grover, 8 nodes | 0.125 to 0.945 after 2 iterations. It falls again after 3 |
| Quantum walk, 4-node cycle | Best 0.427 at step 3 (start 0.25) |
| Quantum walk, 8-node cycle | Best 0.410 at step 29, inside a 30-step window (start 0.125) |
| Classical walk, 4 nodes | Average hitting time 2.50 (formula gives 2.50) |
| Classical walk, 8 nodes | Average hitting time 10.46 (formula gives 10.50) |
| Circuit, no noise (1024 shots) | Marked node found in 1024 of 1024 shots |
| Noise test | Success 100.0%, 98.2%, 89.7%, 74.4% for none, low, medium, high noise |
| Fake IBM Brisbane | About 95% success. The circuit needs only 2 two-qubit gates |

The random seeds are fixed. Counts on the fake IBM chip can still differ by a
few shots from one machine to another.

## Notes

- All results are simulations. The fake IBM chip is a copy of a real chip's noise,
  not a run on a real quantum computer.
- With 4 or 8 nodes no practical quantum advantage is shown. Grover search
  treats the nodes as an unstructured list, and the quantum walk was studied over
  a limited number of steps.
- Tested with Python 3.14, Qiskit 2.6, Qiskit Aer 0.18, NumPy 2.5,
  Matplotlib 3.11 and qiskit-ibm-runtime 0.51.

## Team

- Darwin John DS (URK24CS1278)
- Dheepan Chakkaravarty P (URK24CS9022)
