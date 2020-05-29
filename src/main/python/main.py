#!/usr/bin/env python3
import sys
from fbs_runtime.application_context.PyQt5 import ApplicationContext, cached_property
from PyQt5.QtGui import QFont, QPixmap

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
        return PanelWindow(self)

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
        return QPixmap(self.get_resource('microsoft-excel.png'))

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
