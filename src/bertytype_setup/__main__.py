import tkinter as tk
from bertytype_setup.wizard import Wizard


def main() -> None:
    root = tk.Tk()
    Wizard(root)
    root.mainloop()


if __name__ == "__main__":
    main()
