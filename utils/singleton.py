import socket
import sys

_LOCK_SOCKET: socket.socket | None = None
LOCK_PORT = 47283


def acquire_singleton() -> None:
  global _LOCK_SOCKET
  _LOCK_SOCKET = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  _LOCK_SOCKET.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
  try:
    _LOCK_SOCKET.bind(("127.0.0.1", LOCK_PORT))
    _LOCK_SOCKET.listen(1)
  except OSError:
    print(
      "\n❌ XATOLIK: Bot allaqachon ishlayapti!\n"
      "   1) stop.bat faylini ishga tushiring\n"
      "   2) Keyin run.bat bilan qayta oching\n"
    )
    sys.exit(1)


def release_singleton() -> None:
  global _LOCK_SOCKET
  if _LOCK_SOCKET:
    _LOCK_SOCKET.close()
    _LOCK_SOCKET = None
