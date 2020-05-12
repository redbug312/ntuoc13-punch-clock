#!/usr/bin/env python3
from PyQt5.QtGui import QValidator
from PyQt5.QtWidgets import QSpinBox

from .utils import column_ord, column_chr


MAX_COLUMN = column_ord('ZZ')


class AlphabetSpinBox(QSpinBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMaximum(MAX_COLUMN)

    def validate(self, text, pos):
        # Equivalent to QRegExp('[A-Za-z]{1,2}')
        result = QValidator.Intermediate if not text \
            else QValidator.Acceptable if text.isalpha() and pos <= 2 \
            else QValidator.Invalid
        return result, text.upper(), pos

    def valueFromText(self, text):
        return column_ord(text)

    def textFromValue(self, num):
        return column_chr(num)
