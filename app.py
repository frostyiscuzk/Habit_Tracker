"""Streamlit entrypoint.

The Railway launcher starts this file with Streamlit. Keeping the entrypoint
small makes it clear that the real UI code lives in src/dashboard.py.
"""

from src.dashboard import render_dashboard


# Start the web dashboard.
render_dashboard()
