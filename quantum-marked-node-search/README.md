# Marked Node Search on a Cycle Graph

IA-3, 23CS2037 Quantum Computing, Karunya Institute of Technology and Sciences

Problem: add an oracle that marks one node of a small cycle graph, observe how
the amplitude (probability) concentrates on that node over time, and compare it
with the classical hitting time. Everything is built with Qiskit and NumPy.

## Files

| File | Part | What it is used for |
|------|------|---------------------|
| `src/search_sim.py` | A: exact simulation | Grover search (4 and 8 nodes), quantum walk on a cycle (4 and 8 nodes), classical hitting time, validation checks |
| `src/search_circuit.py` | B: Qiskit circuit | 2-qubit Grover circuit on the Aer simulator (1024 shots), noise test, fake IBM chip (FakeBrisbane) |
| `src/real_hardware_run.py` | C: real IBM machine | Sends the same circuit to a real IBM quantum computer and saves the result |
| `notebooks/QCIA3.ipynb` | Colab notebook | The original Google Colab notebook the code was developed in |
| `figures/` | | All plots (fig1 to fig8, fig9 after a real-hardware run) |
| `results/` | | Result tables (`.csv`) and the saved console output of each run (`.txt`) |

## How to run

```bash
pip install -r requirements.txt
python src/search_sim.py
python src/search_circuit.py
python src/real_hardware_run.py      # needs a free IBM Quantum API key
```

The first two scripts need no account. They also work in Google Colab.

## Real hardware (Part C)

1. Make a free account at https://quantum.cloud.ibm.com and copy the API key.
2. Save it once:
   ```python
   from qiskit_ibm_runtime import QiskitRuntimeService
   QiskitRuntimeService.save_account(token="YOUR_API_KEY", set_as_default=True, overwrite=True)
   ```
3. Run `python src/real_hardware_run.py`. It picks the least busy chip, so it can wait in a queue.
4. To read an earlier job later: `python src/real_hardware_run.py --job-id <JOB_ID>`.

## Results

| Experiment | Result |
|-----------|--------|
| Grover, 4 nodes | marked node probability 0.25 to 1.000 after 1 iteration |
| Grover, 8 nodes | 0.125 to 0.945 after 2 iterations (matches the formula sin²((2k+1)θ)) |
| Quantum walk, 4-node cycle | best 0.427 at step 3 (start 0.25) |
| Quantum walk, 8-node cycle | best 0.410 at step 29, inside a 30-step window (start 0.125) |
| Classical walk, 4 nodes | average hitting time 2.50 (theory 2.50) |
| Classical walk, 8 nodes | average hitting time 10.46 (theory 10.50) |
| Noise test (1024 shots) | success 100.0%, 98.2%, 89.7%, 74.4% for none, low, medium, high noise |
| Fake IBM Brisbane | success 95.1% with 2 two-qubit gates |

The random seed is fixed in the scripts, so the same numbers come out each run.
All results are simulations, except any run done with Part C.

## Team
- Darwin John DS (URK24CS1278)
- Dheepan Chakkaravarty P (URK24CS9022)
