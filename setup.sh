#!/bin/bash
set -e  # Exit on error

# Install requirements with --no-deps to avoid conflicts with Streamlit Cloud's environment
pip install --upgrade pip
pip install --no-deps -r requirements.txt

# Verify core dependencies
python -c "
import sys
for pkg in ['streamlit', 'pandas', 'numpy', 'sqlalchemy']:
    try:
        __import__(pkg)
        print(f'✅ {pkg} imported successfully')
    except ImportError as e:
        print(f'❌ {pkg} import failed: {e}', file=sys.stderr)
        sys.exit(1)
"


