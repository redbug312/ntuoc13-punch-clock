#!/usr/bin/env python3
import pandas as pd
from datetime import datetime

from qspreadsheet import QSpreadSheetModel


class CheckInTableModel(QSpreadSheetModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.latest = None

    def calculate_deduct(self, deadline, current):
        mins = int((current - deadline).total_seconds() / 60)
        return 0 if mins < 5 \
            else 100 if mins < 10 \
            else 200 if mins < 30 \
            else None  # absented

    def checkin(self, col_idx, target, deadline):
        column = self.df.columns[col_idx - 1]
        matches = self.df.loc[:, column] == target
        self.layoutAboutToBeChanged.emit()
        if not self.df.loc[matches].checked.all():
            now = datetime.now()
            deduct = self.calculate_deduct(deadline, now)
            self.df.loc[matches, :3] = (True, deduct, now)
        self.layoutChanged.emit()
        self.latest = matches

    def getLatestInfo(self):
        info = self.df[self.latest]
        info.rename(columns=self.df.iloc[0], inplace=True)
        return info

    def fillCard(self, col_idx, card):
        column = self.df.columns[col_idx - 1]
        if self.latest is not None:
            self.df.loc[self.latest, column] = card

    def open(self, path):
        self.layoutAboutToBeChanged.emit()
        super().open(path)
        prepend = pd.DataFrame(columns=['checked', 'deduct', 'time'])
        self.df = pd.concat([prepend, self.df], axis='columns')
        self.df.iloc[:, :3] = (False, None, None)
        self.df.iloc[0, :3] = ('簽到狀況', '酌扣獎勵金', '簽到時間')
        self.layoutChanged.emit()
