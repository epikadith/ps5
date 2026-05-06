# How to Run: Phantom Consensus Engine

Welcome to the Phantom Consensus evaluation guide. This project features a robust Python strategic backend and a React/D3.js interactive frontend visualization. 

---

## 🚀 Quick Start (Default Dataset)

We have provided a streamlined startup script that executes the backend pipeline and launches the frontend dashboard in one click.

Ensure you have **Python (via `uv`)** and **Node.js (`npm`)** installed, then run:

```bash
bash run.sh
```
This script will:
1. Process the default dataset located in `data/raw/`
2. Output the `final_agreement.json`
3. Generate the comprehensive `analysis.json`
4. Launch the React dashboard at `http://localhost:5173`

*(To stop the dashboard server, simply press `Ctrl+C` in your terminal).*

---

## 🧪 Testing Your Own Hidden Datasets

This engine is designed to dynamically accept and visualize any hidden test data you provide. There are two ways to do this:

### Method 1: Drop-in Replacement (Recommended)
1. Navigate to the `data/raw/` directory.
2. Delete the existing 4 files.
3. Paste your custom files: `representatives.json`, `proposals.json`, `objections.json`, and `relations.csv`.
4. Run `bash run.sh`.
5. Open the dashboard in your browser. It will automatically re-render the network graphs and pipeline analytics for your new data.

### Method 2: Dynamic CLI Folder Targeting
If you have multiple folders with different test sets (e.g., `hidden_test_1/`), you do not need to move files around. You can run the Python engine directly and point it to your specific folder:

```bash
# 1. Run the Python engine on your custom folder
uv run python consensus_engine.py path/to/hidden_test_1 output/final_agreement.json

# 2. Start the dashboard
cd dashboard
npm run dev
```

---

## 🛠️ Running the Automated Test Suite

We have written an exhaustive test suite featuring **164 passing tests**, which rigorously cover data cleaning, Trojan Horse detection, and 18 advanced hidden edge-case scenarios (such as cascading betrayals and faction infiltrators).

To execute the test suite, run:
```bash
uv run pytest tests/ -v
```

---

## 📁 Output Artifacts
Whenever the engine runs, it generates two critical files:
1. `output/final_agreement.json`: The minimal standard schema output required by the hackathon.
2. `dashboard/public/analysis.json`: A massive, rich data file that intercepts every stage of the pipeline to power the frontend React visualization.
