#!/usr/bin/env python3
import re
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
        self._lookup_cache = (None, None)
        self.sanitizes = {
            r'[A-Za-z]\d{2}\w\d{5}': (lambda x: x),
            r'[A-Za-z]\d{2}\w\d{6}': (lambda x: x[:-1]),
        }
        self.prepends = pd.DataFrame({
            'checked': {'name': '簽到狀況',   'init': False},
            'penalty': {'name': '酌扣獎勵金', 'init': None},
            'time':    {'name': '簽到時間',   'init': None},
        }).transpose()

    def punch(self, icol, target, deadline):
        columnhead = self.df.iloc[0]
        boolmask = self._lookup_boolmask(icol, target)
        if not self.df.loc[boolmask].checked.all():
            now = datetime.now()
            penalty = decide_penalty(deadline, now)
            self.layoutAboutToBeChanged.emit()
            self.df.loc[boolmask, :len(self.prepends)] = (True, penalty, now)
            self.layoutChanged.emit()
        # Parameter `target` can be 'r089220750', returned ['R08922075']
        return self.df.loc[boolmask].rename(columns=columnhead)

    def lookup(self, icol, target):
        columnhead = self.df.iloc[0]
        boolmask = self._lookup_boolmask(icol, target)
        return self.df.loc[boolmask].rename(columns=columnhead)

    def _lookup_boolmask(self, icol, target):
        sanitized = self._sanitize_target(target)
        if sanitized != self._lookup_cache[0]:
            # Case-insensitive, for barcode lookups only
            self._lookup_cache = \
                (sanitized,
                 self.df.iloc[:, icol - 1].str.upper() == sanitized.upper())
        return self._lookup_cache[1]

    def _sanitize_target(self, target):
        for regex, transform in self.sanitizes.items():
            if re.fullmatch(regex, target):
                return transform(target)
        else:
            raise ValueError('號碼格式錯誤')

    # SpreadSheetModel overriden methods

    def open(self, path):
        super().open(path)
        pre_df = pd.DataFrame(columns=self.prepends.index)
        self.layoutAboutToBeChanged.emit()
        self.df = pd.concat([pre_df, self.df], axis='columns')
        self.df.iloc[:, :len(self.prepends)] = self.prepends.init.to_list()
        self.df.iloc[0, :len(self.prepends)] = self.prepends.name.to_list()
        self.layoutChanged.emit()

    def save(self, path):
        infs = self.df.penalty == inf
        self.df.loc[infs, 'penalty'] = str(inf)
        super().save(path)
