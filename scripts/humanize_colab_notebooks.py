from pathlib import Path
import nbformat as nbf

ROOT = Path(__file__).resolve().parents[1]
NOTEBOOKS = ROOT / "notebooks"

configs = {
    "01_production_data_wijesinghe.ipynb": ("IT24100858 - Wijesinghe D.T.D", "Clean production data and prepare yield target", ["notebooks/01_production_data_wijesinghe.ipynb", "data/preprocessed/crop_yield_preprocessed.csv"]),
    "02_weather_data_danthanarayana.ipynb": ("IT24100533 - Danthanarayana D.M.R", "Add historical weather and location features", ["notebooks/02_weather_data_danthanarayana.ipynb"]),
    "03_price_data_jayakody.ipynb": ("IT24101090 - Jayakody N.D", "Prepare Colombo next-week wholesale price data", ["notebooks/03_price_data_jayakody.ipynb", "data/preprocessed/colombo_weekly_prices_preprocessed.csv"]),
    "04_model_training_gunathilake.ipynb": ("IT23361690 - Gunathilake B.M.P", "Train and evaluate regression models", ["notebooks/04_model_training_gunathilake.ipynb", "models/crop_yield_model.joblib", "models/wholesale_price_model.joblib", "streamlit_app/app.py"]),
}

for filename, (role, message, paths) in configs.items():
    path = NOTEBOOKS / filename
    nb = nbf.read(path, as_version=4)
    useful = []
    for cell in nb.cells:
        if cell.cell_type == "code" and ("COLAB CELL 1" in cell.source or "COLAB FINAL CELL" in cell.source):
            continue
        if cell.cell_type == "code":
            cell.source = "\n".join(line for line in cell.source.splitlines() if not line.lstrip().startswith("#"))
        useful.append(cell)

    setup = nbf.v4.new_code_cell(f'''import os
import subprocess
from pathlib import Path

REPO_URL = "https://github.com/DTD-Wijesinghe/IT3091---Machine-Learning-Assignment.git"
BRANCH = "main"
STUDENT_ROLE = "{role}"
STUDENT_NAME = input("Enter your real GitHub display name: ").strip()
STUDENT_EMAIL = input("Enter your verified GitHub email: ").strip()
CLONE_DIR = Path("/content/IT3091---Machine-Learning-Assignment")

if not CLONE_DIR.exists():
    subprocess.run(["git", "clone", REPO_URL, str(CLONE_DIR)], check=True)
os.chdir(CLONE_DIR)
subprocess.run(["git", "fetch", "origin"], check=True)
subprocess.run(["git", "checkout", "main"], check=True)
subprocess.run(["git", "pull", "--ff-only", "origin", "main"], check=True)
subprocess.run(["git", "config", "user.name", STUDENT_NAME], check=True)
subprocess.run(["git", "config", "user.email", STUDENT_EMAIL], check=True)
print("Ready for", STUDENT_ROLE)
print("The GitHub account must be authenticated before the final cell is run.")
''')

    add_commands = "\n".join(f'subprocess.run(["git", "add", "{item}"], check=True)' for item in paths)
    finish = nbf.v4.new_code_cell(f'''import subprocess

print(subprocess.run(["git", "status", "--short"], capture_output=True, text=True).stdout)
{add_commands}
subprocess.run(["git", "commit", "-m", "{message}"], check=False)
subprocess.run(["git", "push", "origin", "main"], check=True)
print("Contribution pushed to main.")
''')

    nb.cells = [setup] + useful + [finish]
    nbf.write(nb, path)
    print("Updated", filename)
