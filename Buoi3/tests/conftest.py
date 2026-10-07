import sys
from pathlib import Path
BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE / 'secure-chat'))
sys.path.insert(0, str(BASE / 'netrecon'))
