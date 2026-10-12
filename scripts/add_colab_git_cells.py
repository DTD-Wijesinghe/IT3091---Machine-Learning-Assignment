from pathlib import Path
import nbformat as nbf

ROOT = Path(__file__).resolve().parents[1]
NOTEBOOKS = ROOT / "notebooks"

configs = {
    "01_production_data_wijesinghe.ipynb": ("main", "IT24100858 - Wijesinghe D.T.D", "Clean production data and prepare yield target", ["notebooks/01_production_data_wijesinghe.ipynb", "data/preprocessed/crop_yield_preprocessed.csv"]),
    "02_weather_data_danthanarayana.ipynb": ("main", "IT24100533 - Danthanarayana D.M.R", "Add historical weather and location features", ["notebooks/02_weather_data_danthanarayana.ipynb"]),
    "03_price_data_jayakody.ipynb": ("main", "IT24101090 - Jayakody N.D", "Prepare Colombo next-week wholesale price data", ["notebooks/03_price_data_jayakody.ipynb", "data/preprocessed/colombo_weekly_prices_preprocessed.csv"]),
    "04_model_training_gunathilake.ipynb": ("main", "IT23361690 - Gunathilake B.M.P", "Train and evaluate regression models", ["notebooks/04_model_training_gunathilake.ipynb", "models/crop_yield_model.joblib", "models/wholesale_price_model.joblib", "streamlit_app/app.py"]),
}

for filename, (branch, responsibility, message, paths) in configs.items():
    path = NOTEBOOKS / filename
    nb = nbf.read(path, as_version=4)
    setup = nbf.v4.new_code_cell(f'''# COLAB CELL 1 — run this first\n# This cell clones the current repository and creates this student's branch.\nimport os, subprocess\nfrom pathlib import Path\n\nREPO_URL = "https://github.com/DTD-Wijesinghe/IT3091---Machine-Learning-Assignment.git"\nBRANCH = "{branch}"\nSTUDENT_ROLE = "{responsibility}"\nSTUDENT_NAME = input("Enter your real GitHub display name: ").strip()\nSTUDENT_EMAIL = input("Enter your verified GitHub email: ").strip()\nCLONE_DIR = Path("/content/IT3091---Machine-Learning-Assignment")\n\nif not CLONE_DIR.exists():\n    subprocess.run(["git", "clone", REPO_URL, str(CLONE_DIR)], check=True)\nos.chdir(CLONE_DIR)\nsubprocess.run(["git", "fetch", "origin"], check=True)\nsubprocess.run(["git", "checkout", "main"], check=True)\nsubprocess.run(["git", "pull", "--ff-only", "origin", "main"], check=True)\nsubprocess.run(["git", "checkout", "-B", BRANCH], check=True)\nsubprocess.run(["git", "config", "user.name", STUDENT_NAME], check=True)\nsubprocess.run(["git", "config", "user.email", STUDENT_EMAIL], check=True)\nprint("Prepared", BRANCH, "for", STUDENT_ROLE)\nprint("Important: name/email set the commit author only; GitHub authentication is still required before push.")\n''')
    add_commands = "\n".join([f'subprocess.run(["git", "add", "{item}"], check=True)' for item in paths])
    finish = nbf.v4.new_code_cell(f'''# COLAB FINAL CELL — review before running\n# Direct-to-main workflow: run notebooks one at a time.\n# Do not run this cell concurrently with another student's notebook.\nimport subprocess\n\nprint(subprocess.run(["git", "status", "--short"], capture_output=True, text=True).stdout)\n{add_commands}\nsubprocess.run(["git", "commit", "-m", "{message}"], check=False)\nprint("Authenticate with the {responsibility} GitHub account if Git requests it.")\nsubprocess.run(["git", "push", "origin", "main"], check=True)\nprint("Student contribution pushed directly to main.")\n''')
    nb.cells = [setup] + nb.cells + [finish]
    nbf.write(nb, path)
    print("Updated", path)
