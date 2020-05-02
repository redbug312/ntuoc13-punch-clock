#!/usr/bin/env python3
class QSpreadSheetRange:
    def __init__(self, sheet, rows=(0, 0), cols=(0, 0), color=None):
        self.sheet = sheet
        self.rows = rows[0] - 1, rows[1]
        self.cols = cols[0] - 1, cols[1]
        self.color = color

    def __iter__(self):
        return (self.sheet.data(self.sheet.index(row, col))
                for row in range(*self.rows)
                for col in range(*self.cols))

    def include(self, index):
        row, col = index.row(), index.column()
        return (self.rows[0] <= row < self.rows[1] and
                self.cols[0] <= col < self.cols[1])

    def corners(self):
        return [self.sheet.index(*pos) for pos in zip(self.rows, self.cols)]
