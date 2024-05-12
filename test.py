import sys
from PyQt6.QtWidgets import QApplication, QPlainTextEdit


class Example(QPlainTextEdit):
    def __init__(self):
        super().__init__()

        self.textChanged.connect(self.onTextChanged)

    def onTextChanged(self):
        print("The text has changed!")


if __name__ == "__main__":
    app = QApplication(sys.argv)

    example = Example()
    example.show()

    app.exec()