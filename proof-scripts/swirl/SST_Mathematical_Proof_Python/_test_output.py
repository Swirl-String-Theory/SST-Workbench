import sys
import time
# Force unbuffered output
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(line_buffering=True)
for i in range(5):
    print(f"Test line {i+1}", flush=True)
    time.sleep(0.2)
print("Test complete!", flush=True)