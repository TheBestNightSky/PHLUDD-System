import subprocess
import time
from lib.util import Is_Process

while True:
    time.sleep(5)
    if not Is_Process("Phludd-System"):
        subprocess.run("python", "Phludd System.py")

