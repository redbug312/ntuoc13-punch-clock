#!/usr/bin/env python3
from functools import reduce
from PyQt5.QtGui import QValidator
from PyQt5.QtWidgets import QSpinBox, QFrame, QTableView

from mixins import DropableWidget


class AlphabetSpinBox(QSpinBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMaximum(702)  # allow columns from `A` to `ZZ`

    def validate(self, text, pos):
        # Equivalent to QRegExp('[A-Za-z]{1,2}')
        result = QValidator.Intermediate if not text \
            else QValidator.Acceptable if text.isalpha() and pos <= 2 \
            else QValidator.Invalid
        return result, text.upper(), pos

    def valueFromText(self, text):
        return reduce(lambda x, y: x * 26 + (ord(y) - 64), text, 0)

    def textFromValue(self, num):
        name = ''
        while num:
            num, rem = divmod(num - 1, 26)
            name = chr(65 + rem) + name
        return name


class DropableFrame(QFrame, DropableWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

    def setOverlay(self, overlay):
        self.overlay = overlay
        self.overlay.hide()

    def setContent(self, icon, text):
        self.iconLabel.setPixmap(icon)
        self.textLabel.setText(text)

    def hide(self):
        super().hide()
        self.overlay.show()

    def isFileDropable(self, url):
        return url.endswith('.xlsx')


class DropableTableView(QTableView, DropableWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

    def isFileDropable(self, url):
        return url.endswith('.xlsx')
