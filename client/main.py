from __future__ import annotations

from client.app import CortexiaDesktopApp
from client.config import ClientConfig


def main() -> None:
    app = CortexiaDesktopApp(config=ClientConfig())
    app.mainloop()


if __name__ == "__main__":
    main()
