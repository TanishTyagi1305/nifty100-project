import sys
import os
import signal
import threading

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import uvicorn
from src.api.main import app

# Block all signals that could cause immediate shutdown on Windows
def ignore_signal(signum, frame):
    pass

try:
    signal.signal(signal.SIGBREAK, ignore_signal)
except AttributeError:
    pass

def run_server():
    uvicorn.run(app, host="0.0.0.0", port=8080, log_level="info")

# Run in a daemon thread so the main thread keeps it alive
t = threading.Thread(target=run_server, daemon=False)
t.start()

print("Server running at http://localhost:8080")
print("Press Ctrl+C to stop")

try:
    t.join()
except KeyboardInterrupt:
    print("\nStopping server...")
    sys.exit(0)