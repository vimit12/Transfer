import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget, QComboBox
from PyQt6.QtCore import QDate


class MyWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Month and Year Selector")
        self.setGeometry(100, 100, 400, 200)

        centralWidget = QWidget(self)
        self.setCentralWidget(centralWidget)

        layout = QVBoxLayout()
        centralWidget.setLayout(layout)

        self.monthLabel = QLabel("Select Month:", self)
        self.monthCombo = QComboBox(self)
        months = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October",
                  "November", "December"]
        self.monthCombo.addItems(months)

        # Set default month to current month
        currentMonthIndex = QDate.currentDate().month() - 1  # Month indices start from 0
        self.monthCombo.setCurrentIndex(currentMonthIndex)

        self.yearLabel = QLabel("Select Year:", self)
        self.yearCombo = QComboBox(self)
        years = [str(year) for year in range(2022, 2051)]  # Years from 2022 to 2050
        self.yearCombo.addItems(years)

        # Set default year to current year
        currentYear = QDate.currentDate().year()
        yearIndex = self.yearCombo.findText(str(currentYear))
        if yearIndex != -1:
            self.yearCombo.setCurrentIndex(yearIndex)

        layout.addWidget(self.monthLabel)
        layout.addWidget(self.monthCombo)
        layout.addWidget(self.yearLabel)
        layout.addWidget(self.yearCombo)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MyWindow()
    window.show()
    sys.exit(app.exec())
