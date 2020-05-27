#!/usr/bin/env python3
import re
import pypugjs
from datetime import date, datetime
from inspect import cleandoc
from PyQt5 import uic
from PyQt5.QtCore import Qt, QTime, pyqtSlot as slot
from PyQt5.QtGui import QColor, QFont, QPalette, QFocusEvent
from PyQt5.QtWidgets import QMainWindow, QFileDialog, QAbstractItemView, QTableView, QFrame


LATEST_COLOR  = QColor(240, 198, 116, 50)
BARCODE_COLOR = QColor(178, 148, 187, 50)
GRPCODE_COLOR = QColor(138, 190, 183, 50)
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

        self.uiPmLateTime.setTime(QTime.currentTime())
        self.uiTaLateTime.setTime(QTime.currentTime())
        self.uiTimesheetFrame.setPlaceholder(placeholder)
        self.uiTimesheetFrame.setView(tableview)
        self.uiTimesheetFrame.overlay()

        self.connects = [sig.connect(slt) for sig, slt in {
            self.uiFileOpenBtn.clicked:     self.openXlsx,
            self.uiFileSaveBtn.clicked:     self.saveXlsx,
            self.uiInputEdit.returnPressed: self.scanCard,
            self.uiGrpColSpn.valueChanged:  lambda: self.updateSpreadSheet(4),
            self.uiBarColSpn.valueChanged:  lambda: self.updateSpreadSheet(4),
            self.uiInputEdit.focus:         lambda x: self.warnFocusEvent(x),
            self.uiPanelChk.stateChanged:   lambda x: context.panel.setVisible(x == Qt.Checked),
            self.uiTimesheetFrame.dropped:  lambda x: self.openXlsx(x),
            self.uiTotalSpn.valueChanged:   lambda x: self.uiPunchStatProg.setMaximum(x),
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
        self.uiPmLateTime.setDisabled(False)
        self.uiTaLateTime.setDisabled(False)
        self.uiFileSaveBtn.setDisabled(False)
        self.updateSpreadSheet()
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
        scan = self.uiInputEdit.text()
        self.uiInputEdit.clear()
        iloc_grp = self.uiGrpColSpn.value()
        iloc_bar = self.uiBarColSpn.value()
        latetime_pm = self.uiPmLateTime.time().toPyTime()
        latetime_ta = self.uiTaLateTime.time().toPyTime()
        # Lookup their group
        timesheet = self.context.timesheet
        info = timesheet.lookup(iloc_bar, scan)
        latetime = latetime_pm \
            if info.iloc[:, iloc_grp - 1].isin(['籌員']).all() \
            else latetime_ta
        deadline = datetime.combine(date.today(), latetime)
        # Punch clock in timesheet
        panel = self.context.panel
        if re.fullmatch(r'[A-Za-z]\d{2}\w\d{5}', scan):  # manually inputed
            matches = timesheet.punch(iloc_bar, scan, deadline)
        elif re.fullmatch(r'[A-Za-z]\d{2}\w\d{6}', scan):  # scan barcode
            matches = timesheet.punch(iloc_bar, scan[:-1], deadline)
        elif re.fullmatch(r'\d{10}', scan):  # scan rfc code
            matches = timesheet.punch(self.uiGrpColSpn.value(), scan, deadline)
        else:
            panel.setFailMsg(scan, '號碼格式錯誤')
            timesheet.latest_person = None
            return
        # Highlight latest checked-in one
        self.uiPunchStatProg.setValue(sum(timesheet.df.iloc[1:].checked))
        print(matches)
        if not matches.empty:
            row = matches.index[0] + 1
            timesheet.updateRange('latest', (row, row), (1, timesheet.columnCount()), LATEST_COLOR)
            focus = timesheet.index(row, 0)
            self.uiTimesheetFrame.view().scrollTo(focus, QAbstractItemView.PositionAtCenter)
            panel.setOkayMsg(matches, deadline)
        else:
            panel.setFailMsg(scan, '號碼不存在')
            timesheet.latest_person = None

    @slot(int)
    def updateSpreadSheet(self, flags=0b1111):
        timesheet = self.context.timesheet
        # Update order determined by the spinboxes read/write operations
        if flags & 0b0001:  # shape of spreadsheet
            cols = timesheet.columnCount()
            self.uiBarColSpn.setMaximum(cols)
            self.uiGrpColSpn.setMaximum(cols)
            rows = timesheet.rowCount()
            self.uiTotalSpn.setMaximum(rows - 1)
            self.uiTotalSpn.setValue(rows - 1)
        if flags & 0b0010:  # columnhead of spreadsheet
            pass
        if flags & 0b0100:  # ranges in spreadsheet
            rows = 2, timesheet.rowCount()
            cols_bar = (self.uiBarColSpn.value(), ) * 2
            cols_grp = (self.uiGrpColSpn.value(), ) * 2
            timesheet.updateRange('barcode', rows, cols_bar, BARCODE_COLOR)
            timesheet.updateRange('grpcode', rows, cols_grp, GRPCODE_COLOR)

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
        uic.loadUi(context.uiPanel, self)
        self._focus_message = self.uiInfoLbl.text()

        sans = QFont('IPAexGothic')
        sans.insertSubstitutions('sans', ['Noto Sans CJK TC', 'Microsoft YaHei'])
        sans.setStyleStrategy(QFont.PreferAntialias)
        self.setFont(sans)

    def hintFocusEvent(self, event):
        if event.lostFocus():
            self._focus_message = self.uiInfoLbl.text()
            unfocus_message = re.sub(r'color:#\w{6}', 'color:#BABDB6', self._focus_message)
            self.uiInfoLbl.setText(unfocus_message)
        else:
            self.uiInfoLbl.setText(self._focus_message)

    def setFailMsg(self, scan, reason):
        pug = cleandoc(f"""
            div(align='center' style='font-size:36pt; color:#2E3436;')
              p 掃描條碼失敗
              p(style='font-size:18pt; color:#888A85;') {reason}：{scan}
        """)
        html = pypugjs.simple_convert(pug)
        self.uiInfoLbl.setText(html)

    def setOkayMsg(self, matches, deadline):
        late_mins = int((matches.iloc[0, 2] - deadline).total_seconds() / 60)
        informs = matches.iloc[0, 3:6].to_dict()
        pug = cleandoc(f"""
            div(align='center' style='font-size:36pt; color:#2E3436;')
              table
                each key, val in {list(informs.items())}
                  tr
                    td(align='right')= key + '：'
                    td= val
              if {late_mins} <= 0
                p(style='color:#4E9A06') 準時簽到
              else  // elif/elsif/else-if seems broken
                if {late_mins} <= 5
                  p(style='color:#4E9A06') 遲到 {late_mins} 分鐘
                else
                  p(style='color:#A40000') 遲到 {late_mins} 分鐘
        """)
        html = pypugjs.simple_convert(pug)
        self.uiInfoLbl.setText(html)
