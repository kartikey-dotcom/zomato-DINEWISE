import sys
from pathlib import Path

# Add the project root directory to the python path
project_root = Path(__file__).resolve().parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Import and run the DineWise UI application
import src.app.ui
