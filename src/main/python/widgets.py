#!/usr/bin/env python3
from PyQt5.QtWidgets import QFrame, QHBoxLayout

from mixins import DropableWidget


class PlaceholderFrame(QFrame, DropableWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

    def contain(self, placeholder, view):
        self.placeholder = placeholder
        self.view = view
        layout = self.layout()
        layout.addWidget(placeholder)
        layout.addWidget(view)

    def overlay(self):
        self.placeholder.show()
        self.view.hide()

    def display(self):
        self.placeholder.hide()
        self.view.show()

    def isFileDropable(self, url):
        return url.endswith('.xlsx')
