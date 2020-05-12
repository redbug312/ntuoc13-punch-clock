#!/usr/bin/env python3
from PyQt5.QtWidgets import QTableView, QWidget, QFrame, QHBoxLayout

from .mixins import DropableWidget


class QSpreadSheetView(QTableView, DropableWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

    def isFileDropable(self, url):
        return url.endswith('.xlsx')


class QSpreadSheetFrameView(QWidget, DropableWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.frame = QFrame()
        self.view = QTableView()

        layout = QHBoxLayout()
        layout.addWidget(self.frame)
        layout.addWidget(self.view)
        self.setLayout(layout)
        self.overlay()

    def overlay(self):
        self.frame.show()
        self.view.hide()

    def display(self):
        self.frame.hide()
        self.view.show()

    def isFileDropable(self, url):
        return url.endswith('.xlsx')
