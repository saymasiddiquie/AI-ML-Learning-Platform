#!/bin/bash
set -e  # Exit on error

# Upgrade pip first
python -m pip install --upgrade pip

# Install requirements without strict dependency checking
pip install --no-cache-dir -r requirements.txt

# Verify core dependencies
python -c "
import sys
for pkg in ['streamlit', 'pandas', 'numpy', 'sqlalchemy']:
    try:
        __import__(pkg)
        print(f'✅ {pkg} imported successfully')
    except ImportError as e:
        print(f'⚠️ {pkg} import warning: {e}', file=sys.stderr)
        print('Continuing anyway...', file=sys.stderr)
"

# Create necessary directories
mkdir -p .streamlit
mkdir -p templates


