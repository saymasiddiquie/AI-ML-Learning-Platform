#!/bin/bash
set -e  # Exit on error

# Upgrade pip first
python -m pip install --upgrade pip==23.3.1

# Install base dependencies first
pip install --no-cache-dir \
    markdown-it-py==2.2.0 \
    mdurl==0.1.2 \
    Pygments==2.15.1 \
    rich==13.6.0

# Install the rest of the requirements
pip install --no-cache-dir -r requirements.txt

# Verify critical installations
python -c "
import sys
for pkg in ['streamlit', 'pandas', 'numpy', 'rich']:
    try:
        __import__(pkg)
        print(f'✅ {pkg} installed successfully')
    except ImportError as e:
        print(f'❌ {pkg} import failed: {e}', file=sys.stderr)
        sys.exit(1)
"
