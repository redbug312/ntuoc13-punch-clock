#!/usr/bin/env python3
import sys
from fbs_runtime.application_context.PyQt5 import ApplicationContext, cached_property
from PyQt5.QtGui import QPixmap

from window import MainWindow


class AppContext(ApplicationContext):
    def run(self):
        self.window.show()
        return self.app.exec_()

    @cached_property
    def window(self):
        return MainWindow(self)

    @cached_property
    def ui(self):
        return self.get_resource('window.ui')

    @cached_property
    def placeholderUi(self):
        return self.get_resource('placeholder.ui')

    @cached_property
    def panelUi(self):
        return self.get_resource('panel.ui')

    @cached_property
    def excelPixmap(self):
        return QPixmap(self.get_resource('microsoft-excel.png'))


if __name__ == '__main__':
    context = AppContext()
    exit_code = context.run()
    sys.exit(exit_code)
