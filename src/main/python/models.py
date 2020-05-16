#!/usr/bin/env python3
import pandas as pd
from math import inf
from datetime import datetime

from qspreadsheet import SpreadSheetModel


def decide_penalty(expected, outcome):
    mins = int((outcome - expected).total_seconds() / 60)
    return 0 if mins <= 5 \
        else 100 if mins <= 10 \
        else 200 if mins <= 30 \
        else inf  # to be determined by case


class TimesheetModel(SpreadSheetModel):
    def __init__(self, parent=None):
        super().__init__(parent)

    def punch(self, icol, target, deadline):
        columnhead = self.df.iloc[0]
        boolmask = self._lookup_boolmask(icol, target)
        if not self.df.loc[boolmask].checked.all():
            now = datetime.now()
            penalty = decide_penalty(deadline, now)
            self.layoutAboutToBeChanged.emit()
            self.df.loc[boolmask, :3] = (True, penalty, now)
            self.layoutChanged.emit()
        # Parameter `target` can be 'r089220750', returned ['R08922075']
        return self.df.loc[boolmask].rename(columns=columnhead)

    def lookup(self, icol, target):
        columnhead = self.df.iloc[0]
        boolmask = self._lookup_boolmask(icol, target)
        return self.df.loc[boolmask].rename(columns=columnhead)

    def _lookup_boolmask(self, icol, target):
        # Case-insensitive, for barcode lookups only
        return self.df.iloc[:, icol - 1].str.upper() == target.upper()

    def fillCard(self, icol, card):
        column = self.df.columns[icol - 1]
        if self.latest_person is not None:
            self.df.loc[self.latest_person, column] = card

    # SpreadSheetModel overriden methods

    def open(self, path):
        self.layoutAboutToBeChanged.emit()
        super().open(path)
        prepend = pd.DataFrame(columns=['checked', 'penalty', 'time'])
        self.df = pd.concat([prepend, self.df], axis='columns')
        self.df.iloc[:, :3] = (False, None, None)
        self.df.iloc[0, :3] = ('簽到狀況', '酌扣獎勵金', '簽到時間')
        self.layoutChanged.emit()
