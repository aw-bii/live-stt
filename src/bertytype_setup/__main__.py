import sys
from PySide6.QtWidgets import QApplication
from bertytype_setup.wizard import SetupWizard


def main() -> None:
    app = QApplication.instance() or QApplication(sys.argv)
    wizard = SetupWizard()
    wizard.exec()


if __name__ == "__main__":
    main()
