#!/bin/bash
set -e

echo "Python version:"
python --version

echo "Upgrading pip..."
python -m pip install --upgrade pip

echo "Installing requirements..."
pip install -r requirements.txt

echo "Starting Streamlit..."
python -m streamlit run streamlit_app.py --server.port=${PORT:-8000} --server.address=0.0.0.0
