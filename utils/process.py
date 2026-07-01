import os
import subprocess
import sys
from pathlib import Path


def kill_other_bot_instances() -> None:
  """Ishga tushishdan oldin boshqa bot jarayonlarini to'xtatadi (joriy jarayonni emas)."""
  if sys.platform != "win32":
    return

  script = Path(__file__).parent.parent / "stop.ps1"
  subprocess.run(
    [
      "powershell",
      "-NoProfile",
      "-ExecutionPolicy",
      "Bypass",
      "-File",
      str(script),
      str(os.getpid()),
    ],
    capture_output=True,
    text=True,
  )
