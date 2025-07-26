#!/bin/bash
set -e  # Exit on error

# Create necessary directories
mkdir -p .streamlit
mkdir -p templates

# Install core requirements first
CORE_DEPS="streamlit pandas numpy Pillow PyPDF2 python-dotenv SQLAlchemy requests beautifulsoup4 scikit-learn plotly pyyaml pdfplumber newspaper3k"

# Install core dependencies
for dep in $CORE_DEPS; do
    echo "Installing $dep..."
    python -m pip install --no-cache-dir "$dep" || echo "Warning: Failed to install $dep"
done

# Install ML/AI dependencies with specific versions
ML_DEPS="transformers>=4.30.0 sentence-transformers>=2.2.2"
for dep in $ML_DEPS; do
    echo "Installing $dep..."
    python -m pip install --no-cache-dir "$dep" || echo "Warning: Failed to install $dep"
done

# Install LangChain components
LANGCHAIN_DEPS="langchain>=0.0.340 langchain-community>=0.0.10"
for dep in $LANGCHAIN_DEPS; do
    echo "Installing $dep..."
    python -m pip install --no-cache-dir "$dep" || echo "Warning: Failed to install $dep"
done

# Verify core dependencies
python -c "
import sys
for pkg in ['streamlit', 'pandas', 'numpy', 'sqlalchemy', 'transformers', 'langchain']:
    try:
        __import__(pkg)
        print(f'✅ {pkg} imported successfully')
    except ImportError as e:
        print(f'⚠️ {pkg} import warning: {e}', file=sys.stderr)
"

# Create a minimal config.toml if it doesn't exist
if [ ! -f .streamlit/config.toml ]; then
    echo "[server]" > .streamlit/config.toml
    echo "headless = true" >> .streamlit/config.toml
    echo "port = $PORT" >> .streamlit/config.toml
    echo "enableCORS = false" >> .streamlit/config.toml
    echo "enableXsrfProtection = false" >> .streamlit/config.toml
fi

echo "✅ Setup completed successfully"


