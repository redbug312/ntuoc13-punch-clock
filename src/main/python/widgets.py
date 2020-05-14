#!/usr/bin/env python3
from PyQt5.QtWidgets import QFrame, QHBoxLayout, QLineEdit

from mixins import FocusAwareWidget, DropableWidget


class ScanInputLineEdit(QLineEdit, FocusAwareWidget):
    def __init__(self, parent=None):
        super().__init__(parent)


class PlaceholderFrame(QFrame, DropableWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._placeholder = None
        self._view = None

        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

    def overlay(self):
        if self._placeholder:
            self._placeholder.show()
        if self._view:
            self._view.hide()

    def display(self):
        if self._placeholder:
            self._placeholder.hide()
        if self._view:
            self._view.show()

    # Member setters and getters

    def placeholder(self):
        return self._placeholder

    def view(self):
        return self._view

    def setPlaceholder(self, placeholder):
        self._placeholder = placeholder
        self.layout().addWidget(placeholder)

    def setView(self, view):
        self._view = view
        self.layout().addWidget(view)

    # QWidget overriden methods

    def isFileDropable(self, url):
        return url.endswith('.xlsx')
