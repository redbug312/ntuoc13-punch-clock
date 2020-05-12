#!/usr/bin/env python3
import re
from datetime import date, datetime
from PyQt5 import uic
from PyQt5.QtCore import Qt, QTime, pyqtSlot as slot
from PyQt5.QtGui import QColor, QFont, QPalette
from PyQt5.QtWidgets import QMainWindow, QFileDialog, QMessageBox, QAbstractItemView

from models import CheckInTableModel


LATEST_COLOR = QColor(240, 198, 116, 50)
INTVW_COLOR = QColor(178, 148, 187, 50)
TMSLT_COLOR = QColor(138, 190, 183, 50)
ERROR_COLOR = QColor(204, 102, 102, 50)


class MainWindow(QMainWindow):
    def __init__(self, context, parent=None):
        super().__init__(parent)
        uic.loadUi(context.ui, self)
        uic.loadUi(context.placeholderUi, self.uiTimesheetFrame.frame)

        self.sheet = CheckInTableModel()
        self.panel = PanelWindow(context, parent=self)

        self.uiTimesheetFrame.frame.uiIconLbl.setPixmap(context.excelPixmap)
        self.uiTimesheetFrame.frame.uiTextLbl.setText('尚未開啟簽到名單')
        self.uiTimesheetFrame.view.setModel(self.sheet)
        self.uiTimesheetFrame.view.setTabKeyNavigation(False)
        self.uiTimesheetFrame.view.setSelectionMode(QAbstractItemView.NoSelection)
        self.uiDeadlineTime.setTime(QTime.currentTime())

        self.connects = [sig.connect(slt) for sig, slt in {
            self.uiFileOpenBtn.clicked:         self.openXlsx,
            self.uiFileSaveBtn.clicked:         self.saveXlsx,
            self.uiInputEdit.returnPressed:     self.scanCard,
            self.uiPanelChk.stateChanged:       lambda s: self.panel.setVisible(s == Qt.Checked),
            self.uiTimesheetFrame.dropped:      lambda f: self.openXlsx(f),
            self.uiBarColumnSpn.valueChanged:   lambda: self.updateFromSpreadsheet(4),
            self.uiNfcColumnSpn.valueChanged:   lambda: self.updateFromSpreadsheet(4),
            self.uiTotalSpn.valueChanged:       lambda v: self.uiPunchStatProg.setMaximum(v),
        }.items()]

    @slot()
    @slot(str)
    def openXlsx(self, xlsx=None):
        if xlsx is None:
            dialog = QFileDialog()
            dialog.setAcceptMode(QFileDialog.AcceptOpen)
            dialog.setFileMode(QFileDialog.ExistingFile)
            dialog.setNameFilter('Spreadsheets (*.xlsx)')
            if not dialog.exec_():
                return False
            xlsx = dialog.selectedFiles()[0]
            # xlsx = 'oc13.xlsx'
        self.sheet.open(xlsx)
        # View
        self.uiTimesheetFrame.display()
        self.uiDeadlineTime.setDisabled(False)
        self.uiInputEdit.setDisabled(False)
        self.uiInputEdit.setFocus()
        self.updateFromSpreadsheet()
        # Spinbox backgrounds
        palette = self.uiBarColumnSpn.palette()
        palette.setColor(QPalette.Base, INTVW_COLOR.lighter())
        self.uiBarColumnSpn.setPalette(palette)
        palette.setColor(QPalette.Base, TMSLT_COLOR.lighter())
        self.uiNfcColumnSpn.setPalette(palette)
        self.statusbar.showMessage('載入 %d 列資料。' % self.sheet.rowCount())

    @slot()
    @slot(str)
    def saveXlsx(self, xlsx=None):
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
        self.sheet.save(xlsx)

    @slot()
    def scanCard(self):
        scan = self.uiInputEdit.text()
        self.uiInputEdit.clear()
        # Update spreadsheet by scanned
        deadline_time = self.uiDeadlineTime.time().toPyTime()
        deadline = datetime.combine(date.today(), deadline_time)
        if re.fullmatch(r'[A-Za-z]\d{2}\w\d{5}', scan):  # manually inputed
            self.sheet.checkin(self.uiBarColumnSpn.value(), scan.upper(), deadline)
        elif re.fullmatch(r'[A-Za-z]\d{2}\w\d{6}', scan):  # scan barcode
            self.sheet.checkin(self.uiBarColumnSpn.value(), scan[:-1].upper(), deadline)
        elif re.fullmatch(r'\d{10}', scan):  # scan rfc code
            if self.uiOverwriteChk.isChecked():
                self.sheet.fillCard(self.uiNfcColumnSpn.value(), scan)
            else:
                self.sheet.checkin(self.uiNfcColumnSpn.value(), scan, deadline)
        else:
            self.panel.setFailureMessage(scan, '號碼格式錯誤')
            self.sheet.latest = None
            return
        # Highlight latest checked-in one
        # self.lateTimeEdit.setDisabled(True)
        self.uiPunchStatProg.setValue(sum(self.sheet.df.iloc[1:].checked))
        info = self.sheet.getLatestInfo()
        print(info)
        if not info.empty:
            row = info.index[0] + 1
            self.sheet.range('latest', (row, row), (1, self.sheet.columnCount()), LATEST_COLOR)
            focus = self.uiTimesheetFrame.view.model().index(row, 0)
            self.uiTimesheetFrame.view.scrollTo(focus, QAbstractItemView.PositionAtCenter)
            self.panel.setSuccessMessage(info, deadline)
        else:
            self.panel.setFailureMessage(scan, '號碼不存在')
            self.sheet.latest = None

    @slot(int)
    def updateFromSpreadsheet(self, flags=0b1111):
        # Update order determined by the spinboxes read/write operations
        if flags & 0b0001:  # shape of spreadsheet
            cols = self.sheet.columnCount()
            self.uiBarColumnSpn.setMaximum(cols)
            self.uiNfcColumnSpn.setMaximum(cols)
            rows = self.sheet.rowCount()
            self.uiTotalSpn.setMaximum(rows - 1)
            self.uiTotalSpn.setValue(rows - 1)
        if flags & 0b0010:  # columnhead of spreadsheet
            pass
        if flags & 0b0100:  # ranges in spreadsheet
            rows = 2, self.sheet.rowCount()
            cols_bar = (self.uiBarColumnSpn.value(), ) * 2
            cols_nfc = (self.uiNfcColumnSpn.value(), ) * 2
            self.sheet.range('interviewee', rows, cols_bar, INTVW_COLOR)
            self.sheet.range('timeslot', rows, cols_nfc, TMSLT_COLOR)


class PanelWindow(QMainWindow):
    def __init__(self, context, parent=None):
        super().__init__(parent)
        uic.loadUi(context.panelUi, self)

        sans = QFont('IPAexGothic')
        sans.insertSubstitutions('sans', ['Noto Sans CJK TC', 'Microsoft YaHei'])
        sans.setStyleStrategy(QFont.PreferAntialias)
        self.setFont(sans)

    def setFailureMessage(self, scan, reason):
        self.uiInfoLbl.setText(
            '<div align="center" style="font-size:36pt; color:#2E3436;">' +
            f'<p>掃描條碼失敗</p>' +
            f'<p style="font-size:18pt; color:#888A85;">{reason}：{scan}</p>' +
            '</div>'
        )

    def setSuccessMessage(self, info, deadline):
        passed_mins = int((info.iloc[0, 2] - deadline).total_seconds() / 60)
        self.uiInfoLbl.setText(
            '<div align="center" style="font-size:36pt; color:#2E3436;"><table>' +
            ''.join([f'<tr><td align="right">{k}：</td><td>{v}</td></tr>'
                     for k, v in info.iloc[0, 3:6].items()]) +
            '</table>' +
            '<p style="color:%s">%s</p></div>' % (
                '#4E9A06' if passed_mins < 5 else '#A40000',
                '準時簽到' if passed_mins <= 0 else f'遲到 {passed_mins} 分鐘'
            )
        )
