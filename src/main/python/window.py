#!/usr/bin/env python3
import re
import pypugjs
import inspect
from datetime import date, datetime
from PyQt5 import uic
from PyQt5.QtCore import Qt, QSize, QTime, pyqtSlot as slot
from PyQt5.QtGui import QColor, QPalette, QFocusEvent
from PyQt5.QtWidgets import QMainWindow, QFileDialog, QAbstractItemView, QTableView, QFrame


LATEST_COLOR  = QColor(240, 198, 116, 50)
BARCODE_COLOR = QColor(136, 138, 133, 50)
GRPCODE_COLOR = QColor(211, 215, 207, 50)
UNFOCUS_COLOR = QColor(204, 102, 102, 50)


class MainWindow(QMainWindow):
    def __init__(self, context, parent=None):
        super().__init__(parent)
        self.context = context

        placeholder, tableview = QFrame(), QTableView()
        uic.loadUi(context.ui, self)
        uic.loadUi(context.uiPlaceholder, placeholder)

        placeholder.uiIconLbl.setPixmap(context.pixmapExcel)
        placeholder.uiTextLbl.setText('尚未開啟簽到名單')
        tableview.setModel(context.timesheet)
        tableview.setTabKeyNavigation(False)
        tableview.setSelectionMode(QAbstractItemView.NoSelection)

        checkboxes = (context.iconCheckboxBlank, context.iconCheckboxMarked)
        context.timesheet.setCheckboxIcons(*checkboxes)
        tableview.setIconSize(self.iconSize() * 0.8)

        self.uiPmLateTime.setTime(QTime.currentTime())
        self.uiTaLateTime.setTime(QTime.currentTime())
        self.uiTimesheetFrame.setPlaceholder(placeholder)
        self.uiTimesheetFrame.setView(tableview)
        self.uiTimesheetFrame.overlay()

        self.connects = [sig.connect(slt) for sig, slt in {
            self.uiFileOpenBtn.clicked:     self.openXlsx,
            self.uiFileSaveBtn.clicked:     self.saveXlsx,
            self.uiInputEdit.returnPressed: self.scanCard,
            self.uiBarColSpn.valueChanged:  lambda: self.updateSpreadSheet(0b0100),
            self.uiGrpColSpn.valueChanged:  lambda: self.updateSpreadSheet(0b0100),
            self.uiAbsenceSpn.valueChanged: lambda: self.updateProgressBar(0b10),
            self.uiInputEdit.focus:         lambda x: self.warnFocusEvent(x),
            self.uiPanelChk.stateChanged:   lambda x: context.panel.setVisible(x == Qt.Checked),
            self.uiTimesheetFrame.dropped:  lambda x: self.openXlsx(x),
        }.items()]

    @slot()
    @slot(str)
    def openXlsx(self, xlsx=None):
        timesheet = self.context.timesheet
        if xlsx is None:
            dialog = QFileDialog()
            dialog.setAcceptMode(QFileDialog.AcceptOpen)
            dialog.setFileMode(QFileDialog.ExistingFile)
            dialog.setNameFilter('Spreadsheets (*.xlsx)')
            if not dialog.exec_():
                return False
            xlsx = dialog.selectedFiles()[0]
            # xlsx = 'oc13.xlsx'
        timesheet.open(xlsx)
        # View
        self.uiTimesheetFrame.display()
        self.uiInputEdit.setDisabled(False)
        self.uiInputEdit.setFocus()
        self.uiFileSaveBtn.setDisabled(False)
        self.updateSpreadSheet()
        self.updateProgressBar()
        # Spinbox backgrounds
        palette = self.uiBarColSpn.palette()
        palette.setColor(QPalette.Base, BARCODE_COLOR.lighter())
        self.uiBarColSpn.setPalette(palette)
        palette = self.uiGrpColSpn.palette()
        palette.setColor(QPalette.Base, GRPCODE_COLOR.lighter())
        self.uiGrpColSpn.setPalette(palette)
        self.statusbar.showMessage('載入 %d 列資料。' % timesheet.rowCount())

    @slot()
    @slot(str)
    def saveXlsx(self, xlsx=None):
        timesheet = self.context.timesheet
        if xlsx is None:
            dialog = QFileDialog()
            dialog.setAcceptMode(QFileDialog.AcceptSave)
            dialog.setFileMode(QFileDialog.AnyFile)
            dialog.setNameFilter('Spreadsheets (*.xlsx)')
            if not dialog.exec_():
                return False
            xlsx = dialog.selectedFiles()[0]
            # xlsx = 'output.xlsx'
        if not xlsx.endswith('.xlsx'):
            xlsx += '.xlsx'
        timesheet.save(xlsx)

    @slot()
    def scanCard(self):
        timesheet = self.context.timesheet
        panel = self.context.panel

        scan = self.uiInputEdit.text()
        iloc_grp = self.uiGrpColSpn.value()
        iloc_bar = self.uiBarColSpn.value()
        latetime_pm = self.uiPmLateTime.time().toPyTime()
        latetime_ta = self.uiTaLateTime.time().toPyTime()

        try:
            # Lookup their group
            group = timesheet.lookup(iloc_bar, scan).iloc[:, iloc_grp - 1]
            latetime = latetime_pm if group.isin(['籌員']).all() \
                else latetime_ta
            deadline = datetime.combine(date.today(), latetime)
            # Punch clock in timesheet
            matches = timesheet.punch(iloc_bar, scan, deadline)
            if matches.empty:
                raise KeyError()
            print(matches)
        except ValueError:
            panel.setFailMsg(scan, '號碼格式錯誤')
            return
        except KeyError:
            panel.setFailMsg(scan, '號碼不存在')
            return
        finally:
            self.uiInputEdit.clear()

        # Highlight latest checked-in one
        row = matches.index[0] + 1
        timesheet.updateRange('latest', (row, row),
                              (1, timesheet.columnCount()), LATEST_COLOR)
        focus = timesheet.index(row, 0)
        self.uiTimesheetFrame.view() \
            .scrollTo(focus, QAbstractItemView.PositionAtCenter)
        self.context.sound.play()
        self.updateProgressBar(0x01)
        panel.setOkayMsg(matches, deadline)

    @slot(int)
    def updateSpreadSheet(self, flags=0b1111):
        timesheet = self.context.timesheet
        # Update order determined by the spinboxes read/write operations
        if flags & 0b0001:  # shape of spreadsheet
            cols = timesheet.columnCount()
            self.uiBarColSpn.setMaximum(cols)
            self.uiGrpColSpn.setMaximum(cols)
            rows = timesheet.rowCount()
            self.uiAbsenceSpn.setMaximum(rows - 1)
        if flags & 0b0010:  # columnhead of spreadsheet
            pass
        if flags & 0b0100:  # ranges in spreadsheet
            rows = 2, timesheet.rowCount()
            cols_bar = (self.uiBarColSpn.value(), ) * 2
            cols_grp = (self.uiGrpColSpn.value(), ) * 2
            timesheet.updateRange('barcode', rows, cols_bar, BARCODE_COLOR)
            timesheet.updateRange('grpcode', rows, cols_grp, GRPCODE_COLOR)

    @slot(int)
    def updateProgressBar(self, flags=0b11):
        timesheet = self.context.timesheet
        if flags & 0b01:  # set value
            checked = sum(timesheet.df.iloc[1:].checked)
            self.uiPunchStatProg.setValue(checked)
        if flags & 0b10:  # set maximum
            expected = self.uiAbsenceSpn.maximum()
            absented = self.uiAbsenceSpn.value()
            self.uiPunchStatProg.setMaximum(expected - absented)

    @slot(QFocusEvent)
    def warnFocusEvent(self, event):
        panel = self.context.panel
        panel.hintFocusEvent(event)

        palette = self.uiInputEdit.style().standardPalette()
        if event.lostFocus():
            palette.setColor(QPalette.Base, UNFOCUS_COLOR.lighter())
        self.uiInputEdit.setPalette(palette)


class PanelWindow(QMainWindow):
    def __init__(self, context, parent=None):
        super().__init__(parent)
        self.context = context

        uic.loadUi(context.uiPanel, self)
        self.setFont(context.fontSans)
        self._focus_message = self.uiInfoLbl.text()

    def hintFocusEvent(self, event):
        if event.lostFocus():
            self._focus_message = self.uiInfoLbl.text()
            unfocus_message = re.sub(r'color:#\w{6}', 'color:#BABDB6',
                                     self._focus_message)
            self.uiInfoLbl.setText(unfocus_message)
        else:
            self.uiInfoLbl.setText(self._focus_message)

    def setFailMsg(self, scan, reason):
        def truncate(string, length):
            return string if len(string) <= length \
                else string[:length] + '&hellip;'
        pug = inspect.cleandoc(f"""
            div(align='center' style='font-size:36pt; color:#2E3436;')
              p 掃描條碼失敗
              p(style='font-size:18pt; color:#888A85;')
                | {reason}：{truncate(scan, 10)}
        """)
        html = pypugjs.simple_convert(pug)
        self.uiInfoLbl.setText(html)

    def setOkayMsg(self, matches, deadline):
        columnhead = self.context.timesheet.columnhead()
        match = matches.iloc[0]
        informs = zip(columnhead.reindex(range(3)), match.reindex(range(3)))
        pug = inspect.cleandoc(f"""
            div(align='center' style='font-size:36pt; color:#2E3436;')
              table
                each key, val in {list(informs)}
                  tr
                    td(align='right')= key + '：'
                    td= val
              if not {match.penalty}
                p(style='color:#4E9A06') {match.brief}
              else
                p(style='color:#A40000') {match.brief}
        """)
        html = pypugjs.simple_convert(pug)
        self.uiInfoLbl.setText(html)
