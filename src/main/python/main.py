#!/usr/bin/env python3
import sys
from fbs_runtime.application_context.PyQt5 import ApplicationContext, cached_property
from PyQt5.QtCore import QUrl
from PyQt5.QtGui import QFont, QIcon, QPixmap
from PyQt5.QtMultimedia import QMediaContent, QMediaPlayer

from window import MainWindow, PanelWindow
from models import TimesheetModel


class AppContext(ApplicationContext):
    def run(self):
        self.window.show()
        return self.app.exec_()

    @cached_property
    def window(self):
        return MainWindow(self)

    @cached_property
    def panel(self):
        return PanelWindow(self, parent=self.window)

    @cached_property
    def timesheet(self):
        return TimesheetModel()

    @cached_property
    def ui(self):
        return self.get_resource('window.ui')

    @cached_property
    def uiPlaceholder(self):
        return self.get_resource('placeholder.ui')

    @cached_property
    def uiPanel(self):
        return self.get_resource('panel.ui')

    @cached_property
    def pixmapExcel(self):
        path = self.get_resource('microsoft-excel.png')
        return QPixmap(path)

    @cached_property
    def iconCheckboxBlank(self):
        path = self.get_resource('checkbox-blank-outline.svg')
        return QIcon(path)

    @cached_property
    def iconCheckboxMarked(self):
        path = self.get_resource('checkbox-marked.svg')
        return QIcon(path)

    @cached_property
    def sound(self):
        path = self.get_resource('stairs.mp3')
        content = QMediaContent(QUrl.fromLocalFile(path))
        player = QMediaPlayer(flags=QMediaPlayer.LowLatency)
        player.setMedia(content)
        return player

    @cached_property
    def fontSans(self):
        sans = QFont('IPAexGothic')
        alternatives = ['Noto Sans CJK TC', 'Microsoft YaHei']
        sans.insertSubstitutions('IPAexGothic', alternatives)
        sans.setStyleStrategy(QFont.PreferAntialias)
        return sans


if __name__ == '__main__':
    context = AppContext()
    exit_code = context.run()
    sys.exit(exit_code)
