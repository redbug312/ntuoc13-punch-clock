#!/usr/bin/env python3
from PyQt5.QtCore import pyqtSignal as signal
from PyQt5.QtGui import QFocusEvent


class FocusAwareWidget:
    focus = signal(QFocusEvent, name='focus')

    def focusInEvent(self, event):
        self.focus.emit(event)

    def focusOutEvent(self, event):
        self.focus.emit(event)


class DropableWidget:
    dropped = signal(str, name='dropped')

    def __init__(self, parent=None):
        # Mixin for QWidget
        self.setAcceptDrops(True)

    def isFileDropable(self, url):
        return NotImplemented

    def dragEnterEvent(self, event):
        event.accept()

    def dragMoveEvent(self, event):
        event.accept()

    def dropEvent(self, event):
        urls = event.mimeData().urls()
        if len(urls) == 1:
            url = urls[0]
            if self.isFileDropable(url):
                self.dropped.emit(url.toLocalFile())
                event.accept()
        event.ignore()
