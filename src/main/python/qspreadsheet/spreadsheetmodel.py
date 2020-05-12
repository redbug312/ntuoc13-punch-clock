#!/usr/bin/env python3
import openpyxl
import pandas as pd
from openpyxl.utils.dataframe import dataframe_to_rows
from PyQt5.QtCore import Qt, QAbstractTableModel, QModelIndex
from PyQt5.QtGui import QColor

from .utils import column_chr
from .spreadsheetrange import SpreadSheetRange


class SpreadSheetModel(QAbstractTableModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.df = pd.DataFrame()
        self.ranges = dict()
        self.formats = {
            bool:         (lambda x: ''),
            pd.Timestamp: (lambda x: x.strftime('%H:%M:%S %m/%d')),
        }

    def open(self, path, name=None):
        self.layoutAboutToBeChanged.emit()
        if path.endswith('.xlsx'):
            wb = openpyxl.load_workbook(path)
            ws = wb[name] if name else wb.active
            self.df = pd.DataFrame(ws.values)
        else:
            raise NotImplementedError(f'Unknown file extensions')
        # Sanitize empty rows and columns
        self.df.dropna(axis='rows', how='all', inplace=True)
        self.df.dropna(axis='columns', how='all', inplace=True)
        self.layoutChanged.emit()

    def save(self, path):
        wb = openpyxl.Workbook()
        rows = dataframe_to_rows(self.df, index=False, header=False)
        for row in rows:
            wb.active.append(row)
        wb.save(path)

    def updateRange(self, name, rows, cols, color):
        if name in self.ranges:
            r = self.ranges[name]
            self.dataChanged.emit(*r.corners())
        r = SpreadSheetRange(self, rows, cols, color)
        self.dataChanged.emit(*r.corners())
        self.ranges[name] = r

    # QAbstractItemModel overriden methods

    def data(self, index, role=Qt.DisplayRole):
        if role == Qt.DisplayRole:
            value = self.df.iloc[index.row(), index.column()]
            vtype = type(value)
            return str() if pd.isna(value) \
                else self.formats[vtype](value) if vtype in self.formats \
                else str(value)
        elif role == Qt.CheckStateRole:
            value = self.df.iloc[index.row(), index.column()]
            if type(value) is bool:
                return Qt.Checked if value else Qt.Unchecked
        elif role == Qt.ForegroundRole:
            # Column head is grey out
            if index.row() == 0:
                return QColor('#888A85')
        elif role == Qt.BackgroundRole:
            # Ranges are highlighted
            envelopes = [range for range in self.ranges.values()
                         if range.include(index)]
            if envelopes:
                return envelopes[-1].color

    def headerData(self, section, orientation, role):
        if role == Qt.DisplayRole:
            return section + 1 if orientation == Qt.Vertical \
                else column_chr(section + 1)

    def rowCount(self, parent=QModelIndex()):
        return self.df.shape[0]

    def columnCount(self, parent=QModelIndex()):
        return self.df.shape[1]
