from PyQt5.QtGui import QIcon  # QPainter, QPen,QBrush,

from PyQt5.QtWidgets import *

from functools import partial


class SuperCombo(QComboBox):
    def __init__(self, name, par, orient_v=True, vals=None, show_lab=True, run=True):
        super().__init__()

        self.par = par
        self.orient_v = orient_v
        self.show_lab = show_lab
        self.name = name
        self.item_ls = []
        self.wig = QWidget()

        self.lab = QLabel(self.name)

        if self.name in self.par.tool_tip:
            self.setToolTip(self.par.tool_tip[self.name])

        self._layout_set()

        if vals is not None:
            for v in vals:
                if '_' in v:
                    v, ic = v.split('_', 1)
                    self.addItem(QIcon(f'icons/{ic}.png'), v)
                elif self.name == 'Active Doc':
                    self.addItem(self.load_doc(v), v)
                else:
                    self.addItem(v)
                self.item_ls.append(v)

        if run:
            self.currentTextChanged.connect(lambda x: self.par.run_cmd(self.name, x))

    def load_doc(self, cell):
        id2 = self.par.doc_data.loc[self.par.doc_data['Doc'] == cell, 'Gender']
        if id2.values[0] == 'Male':
            ids = 'icons/user-medical.png'
        else:
            ids = 'icons/user-medical-female.png'
        return QIcon(ids)

    # noinspection PyArgumentList
    def _layout_set(self):
        if self.orient_v:
            self.layout = QVBoxLayout()
        else:
            self.layout = QHBoxLayout()
        self.layout.addWidget(self)
        self.layout.addWidget(self.lab)
        self.wig.setLayout(self.layout)

    def reset_show(self, show_lab=False, flip=False):
        if flip:
            self.orient_v = not self.orient_v
            self._layout_set()
        if show_lab:
            self.show_lab = not self.show_lab
            if self.show_lab:
                self.layout.addWidget(self.lab)
            else:
                self.layout.removeWidget(self.lab)


class SuperButton(QWidget):
    def __init__(self, name, par, orient_v=True, vals=None, show_lab=True):
        super().__init__()

        self.par = par
        self.orient_v = orient_v
        self.show_lab = show_lab
        self.name = name
        self.but = {}
        self.lab = QLabel(self.name)

        if vals:
            for i in vals:
                if '_' in i:
                    i, ic = i.split('_', 1)
                    j = QPushButton(QIcon(f'icons/{ic}.png'), "")
                else:
                    j = QPushButton(i)
                j.clicked.connect(partial(self.par.run_cmd, i))
                if i in self.par.tool_tip:
                    j.setToolTip(self.par.tool_tip[i])
                self.but[i] = j

        self._layout_set()

    def _layout_set(self):
        self.layout = QGridLayout()
        n = 0
        if self.orient_v:

            for i in self.but.keys():
                self.layout.addWidget(self.but[i], 0, n)
                n += 1
            self.layout.addWidget(self.lab, 1, 0, 1, n)
        else:
            for i in self.but.keys():
                self.layout.addWidget(self.but[i], n, 0)
                n += 1
            self.layout.addWidget(self.lab, 0, 1, n, 1)
        self.setLayout(self.layout)

    def reset_show(self, show_lab=False, flip=False):
        if flip:
            self.orient_v = not self.orient_v
            self._layout_set()
        if show_lab:
            self.show_lab = not self.show_lab
            if not self.show_lab:
                self.layout.removeWidget(self.lab)
