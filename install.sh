echo "Creating virtual environment..."
python3 -m venv .venv && source .venv/bin/activate
echo "Activating virtual environment..."
echo "Installing requirements..."
pip install -r requirements.txt
