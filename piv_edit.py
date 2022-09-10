from PyQt5.QtGui import  QDrag
from PyQt5.QtCore import Qt, QDate, QMimeData
# from logging import exception

from PyQt5.QtWidgets import *

import numpy as np

import sys

from functools import partial


def multi_handel(func):
    def wrap(x, x_col, df, cols):
        di = df.loc[df[x_col] == x, cols]
        return func(x, di.values)

    return wrap


@multi_handel
def p_cent_all(x, xf):
    return x / np.sum(xf)


def group2(mi):
    mi = mi.lower()
    def wrap(df):
        def rap(xi, ffff):
            if isinstance(xi, QDate):
                x2 = ffff(xi)
            else:
                x2 = ""
            return x2

        if mi == 'm':
            dfx = df['Days'].apply(lambda x: rap(x, lambda xii: xii.month()))
        elif mi == 'w':
            dfx = df['Days'].apply(lambda x: rap(x, lambda xii: xii.weeknumber()))
        elif mi == '2w':
            dfx = df['Days'].apply(lambda x: rap(x, lambda xii: xii.weeknumber() % 2))
        elif mi == 'd':
            dfx = df['Days'].apply(lambda x: rap(x, lambda xii: xii.day()))
        else:
            dfx = df['Days'].apply(lambda x: rap(x, lambda xii: xii.dayofweek()))
        # elif mi == 'gen':
        #     dfx = df['Days'].apply(lambda x: rap(x, lambda xii: xii.dayofweek()))
        return dfx

    return wrap


# def group2(mi):
#     def wrap(df):
#         def rap(xi):
#             if isinstance(xi, QDate):
#                 x2 = pd.Timestamp(year=xi.year(), day=xi.day(), month=xi.month())
#             else:
#                 x2 = ""  # groupby multiple func
#             return x2
#
#         if mi == 'm':
#
#     return rap


class pivotDialog(QDialog):

    def __init__(self, df, par=None):
        super().__init__()  # no acept
        self.par = par  # todo sum ave cnt
        self.func_ls = {'mean': np.mean, 'max': np.max, 'min': np.min, 'cnt': 'count', 'sd': np.std}
        self.setWindowTitle('Pivot Table Fields')
        self.button = QDialogButtonBox()
        self.feild_data = {}
        self.button.setOrientation(Qt.Vertical)
        self.button.setStandardButtons(QDialogButtonBox.Cancel | QDialogButtonBox.Ok)
        self.gridLayoutWidget = QWidget()
        self.piv_lay = QGridLayout()
        self.v_layout = QVBoxLayout()
        self.check_lay = QVBoxLayout()
        self.group1 = ['month', 'week', '2Week']
        self.freq_op = {'month': group2('m'), 'week': group2('W'), '2Week': group2('2w')}
        self.df = df
        self.group = ['Gender', 'Categories', 'Time Per Patient']  # self.par.par.doc_data
        for i in self.group:
            self.freq_op[i] = self.group3(i)
        # self.retranslateUi(self)
        self.button.accepted.connect(self.accept)
        self.button.rejected.connect(self.reject)
        self._set_list_widgets()
        self._set_check_lay()

    def group3(self, mi):  # self.par.par.doc_data
        mi = mi.lower()

        def wrap(df):

            dfx = df['Doc'].apply(lambda x: lambda xii: self.par.doc_data.loc[self.par.doc_data['Doc'] == xii, mi])

            return dfx

        return wrap

    def super_piv(self, index=None, columns=None, values=None, filt=None, aggfunc=None):

        print(f'super piv')
        if values is not None:
            print(f'super piv---')
            df2 = self.df.copy()
            for row in self.freq_op.keys():
                if any(row in x for x in [aggfunc, filt, values, columns, index] if x is not None):
                    df2[row] = self.freq_op[row](df2)
            if filt is not None and len(filt) > 0:
                df2 = df2.filter(filt)

            if columns is not None:
                if len(columns) == 0:
                    columns = None

            if aggfunc is None or len(aggfunc) == 0:
                aggfunc = np.sum
            return df2.pivot_table(values, index, columns, aggfunc)
        return 'error'

    def pivot(self):
        print('pivot')
        k = {'aggfunc': {}}
        for f in np.array(self.item_ls).flatten():
            vals = self.but_ls[f]
            if f == 'Rows':
                print('set row')
                f = 'index'
            elif f == 'Filters':
                print('set filt')
                f = 'filt'
            if f == 'Values':
                print('seting val')
                k[f.lower()] = []
                for ite in range(vals.count()):
                    va = vals.item(ite).text()
                    if "_" in va:
                        va, vg = va.split('_')
                    else:
                        vg = 'cnt'
                    k['aggfunc'][va] = self.func_ls[vg]  # should hold list,single
                    k[f.lower()].append(va)
                print('set-- val')
            else:
                print(f'seting--- {f}')
                k[f.lower()] = [vals.item(ite).text() for ite in range(vals.count())]
                print(f'---set--- {f}')
        print('k=', k)
        pp = self.super_piv(**k)
        if isinstance(pp, str):
            print('eeeee')
            self.bb.setText(pp)
        else:
            self.bb.setText('Good')
            print('good')
            if self.par is not None:
                print('par')
                self.par.df = pp
                self.par.reset_table()

    def _set_list_widgets(self):
        self.item_ls = [['Filters', 'Columns'], ['Rows', 'Values']]
        self.but_ls = {}
        for r in range(2):
            for c in range(2):
                lab = self.item_ls[r][c]
                j = QLabel(lab)
                i = PivotBlock(self, col=lab == 'Values')

                self.but_ls[lab] = i
                # noinspection PyArgumentList
                self.piv_lay.addWidget(j, r * 2, c)
                # noinspection PyArgumentList
                self.piv_lay.addWidget(i, r * 2 + 1, c)

        self.setLayout(self.v_layout)
        self.bb = QLabel('Good')
        # noinspection PyArgumentList
        self.v_layout.addWidget(self.bb)
        self.v_layout.addLayout(self.check_lay)
        self.v_layout.addLayout(self.piv_lay)

        # self.bb.clicked.connect(self.pivot)

    def _set_check_lay(self):
        self.data_col = list(self.df.columns)
        self.fields = {}
        if 'Date' in self.data_col or 'Days' in self.data_col:
            self.data_col.extend(self.group1)
        if 'Doc' in self.data_col:
            self.data_col.extend(self.group)
        for i in self.data_col:
            wi = QCheckBox(i)

            wi.stateChanged.connect(partial(self.rr, i))
            self.fields[i] = wi
            self.feild_data[i] = []
            # noinspection PyArgumentList
            self.check_lay.addWidget(wi)
            # multiindex for rows asnd do funcs

    def rr(self, i):

        click = self.fields[i].isChecked()
        print(f'click: i:{i}, v:{click}')
        if click:
            self.but_ls['Rows'].addItem(QListWidgetItem(i))
        else:
            for j in self.but_ls.values():
                items = j.findItems(i, Qt.MatchExactly)

                if len(items) > 0:
                    j.takeItem(j.row(items[0]))

    def closeEvent(self, event):
        self.par.dia_act = False
        super().closeEvent(event)


class PivotBlock(QListWidget):
    def __init__(self, par:pivotDialog, col=False):
        super().__init__()
        self.col = col
        self.par = par
        # self.setViewMode(QListView.IconMode)
        # self.setIconSize((55,55))
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.setDragEnabled(True)
        self.setDefaultDropAction(Qt.MoveAction)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)
        self.set_menu()

    def dragMoveEvent(self, event):
        if event.mimeData().hasFormat("application/x-item"):
            event.setDropAction(Qt.MoveAction)
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        print('drop')
        if event.mimeData().hasFormat("application/x-item"):
            event.accept()
            event.setDropAction(Qt.MoveAction)
            item = QListWidgetItem()
            name = event.mimeData().data("application/x-item")
            n2 = str(name, 'utf-8')
            if '_' in n2:
                n2 = n2.split('_')[0]
            item.setText(n2)
            # item.setIcon(QIcon(":/images/iString")) # set path to image
            self.addItem(item)
            self.reset_text(item,n2)

        else:
            event.ignore()

    def startDrag(self, supportedActions):  # , Qt.DropActions, supportedActions):
        # print('start drag')
        item = self.currentItem()
        mimeData = QMimeData()

        ba = item.text()
        mimeData.setData("application/x-item", bytes(ba, 'utf-8'))
        drag = QDrag(self)
        drag.setMimeData(mimeData)
        if drag.exec(Qt.MoveAction) == Qt.MoveAction:
            self.takeItem(self.row(item))
            self.par.pivot()
            # self.set_piv()
        #     self.emit(self.itemDroped())

    def set_menu(self):
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        # def setContextMenuPolicy(self):
        self.customContextMenuRequested.connect(self._add_menu)

    def add_text(self, i, ite, ii):
        xi = self.menu_item[ite].isChecked()
        if xi:
            self.par.feild_data[i].append(ite)

            print(f'added {ite} to {i}')
        else:
            self.par.feild_data[i].remove(ite)
            print(f'removed{ite} from {i}')
        if len(self.par.feild_data[i]) > 0:
            ii.setText(i + '_' + '_'.join(self.par.feild_data[i]))
        else:
            ii.setText(i)
        self.par.pivot()

    def reset_text(self, ii,i):
        if self.col and len(self.par.feild_data[i]) > 0:
            ii.setText(i + '_' + '_'.join(self.par.feild_data[i]))
        else:
            ii.setText(i)
        pass

    def _add_menu(self, pos):
        print('menu')

        if self.col:
            ii = self.itemAt(pos)
            if isinstance(ii, QListWidgetItem):
                self.menu_item = {}
                print('wig')
                i = ii.text()
                if '_' in i:
                    i = i.split['_'][0]

                self.context_menu = QMenu("Context menu", self)
                print('qmen')
                for ite in self.par.func_ls.keys():
                    print('ite', ite)
                    action = QAction(ite)
                    action.setCheckable(True)
                    if ite in self.par.feild_data[i]:
                        action.setChecked(True)
                    action.triggered.connect(partial(self.add_text, i, ite, ii))
                    self.menu_item[ite] = action
                    self.context_menu.addAction(action)
                    print('loaded action:', action.text())

                self.context_menu.exec(self.mapToGlobal(pos))

    def dragEnterEvent(self, event):

        if event.mimeData().hasFormat("application/x-item"):
            event.accept()
        else:
            event.ignore()

    def supportedDropActions(self):
        return Qt.MoveAction

if __name__ == '__main__':
    import seaborn as sns

    titanic = sns.load_dataset('titanic')
    app = QApplication(sys.argv)
    win = pivotDialog(df=titanic)
    win.show()
    sys.exit(app.exec_())
