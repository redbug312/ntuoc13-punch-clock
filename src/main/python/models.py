#!/usr/bin/env python3
import re
import pandas as pd
from math import inf
from datetime import datetime

from qspreadsheet import SpreadSheetModel


def decide_penalty(deadline, now):
    mins = int((now - deadline).total_seconds() / 60)
    return 0 if mins <= 0 \
        else 100 if mins <= 10 \
        else 200 if mins <= 30 \
        else inf  # to be determined by case


def provide_brief(deadline, now):
    mins = int((now - deadline).total_seconds() / 60)
    return '準時簽到' if mins <= 0 \
        else f'遲到 {mins} 分鐘'


PREPENDS = {
    'checked': {'name': '簽到紀錄', 'init': False, 'punch': (lambda *_: True)},
    'penalty': {'name': '酌減獎勵', 'init': None,  'punch': decide_penalty},
    'brief':   {'name': '簽到狀況', 'init': None,  'punch': provide_brief},
    'moment':  {'name': '簽到時間', 'init': None,  'punch': (lambda _, now: now)},
}


class TimesheetModel(SpreadSheetModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._lookup_cache = ((None, None), None)
        self.prepends = pd.DataFrame(PREPENDS).transpose()

    def punch(self, icol, target, deadline):
        boolmask = self._lookup_boolmask(icol, target)
        params = (deadline, datetime.now())
        fields = tuple(map(lambda f: f(*params), self.prepends.punch))
        if not self.df.loc[boolmask].checked.all() \
                or (self.df.loc[boolmask].penalty > fields[1]).any():
            self.layoutAboutToBeChanged.emit()
            self.df.loc[boolmask, :len(self.prepends)] = fields
            self.layoutChanged.emit()
        # Parameter `target` can be 'r089220750', returned ['R08922075']
        return self.df.loc[boolmask]

    def lookup(self, icol, target):
        boolmask = self._lookup_boolmask(icol, target)
        return self.df.loc[boolmask]

    def columnhead(self):
        return self.df.iloc[0]

    def _lookup_boolmask(self, icol, target):
        sanitized = self._sanitize_target(target)
        if (icol, sanitized) != self._lookup_cache[0]:
            # Case-insensitive, for barcode lookups only
            self._lookup_cache = \
                ((icol, sanitized), self.df.iloc[:, icol - 1]
                 .str.strip().str.upper() == sanitized.strip().upper())
        return self._lookup_cache[1]

    def _sanitize_target(self, target):
        sanitizes = {
            r'[A-Za-z]\d{2}\w\d{5}': (lambda x: x),
            r'[A-Za-z]\d{2}\w\d{6}': (lambda x: x[:-1]),
        }
        for regex, transform in sanitizes.items():
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
