import sys
import urllib.request

try:
    urllib.request.urlopen('http://localhost:8000/health', timeout=2)
    sys.exit(0)
except Exception:
    sys.exit(1)