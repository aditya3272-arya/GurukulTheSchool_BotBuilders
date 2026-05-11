import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from admin_panel.app import AdminApp

if __name__ == "__main__":
    app = AdminApp()
    app.mainloop()
