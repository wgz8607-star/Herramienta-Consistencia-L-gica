"""Double-click launcher or run: python iniciar.py"""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def main():
    try:
        import tkinter
        import openpyxl
        import psycopg2
    except ImportError as error:
        message = ('Falta una dependencia: ' + str(error) + '\n\n'
                   'En Windows: ejecute instalar_windows.bat y luego iniciar_windows.bat.\n'
                   'En otros sistemas: instale requirements.txt y Tkinter para Python.')
        try:
            import tkinter as tk
            from tkinter import messagebox
            root = tk.Tk(); root.withdraw()
            messagebox.showerror('Administrador de reglas', message)
            root.destroy()
        except ImportError:
            print(message, file=sys.stderr)
        return 1
    from cargador_reglas.interfaz import main as run
    run()
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
