"""Streamlit Cloud entry point for the project application."""

from pathlib import Path
import runpy


runpy.run_path(str(Path(__file__).parent / "streamlit_app" / "app.py"), run_name="__main__")
