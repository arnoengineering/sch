import sqlite3 as sl

from data_view import DataFrameViewer
from piv_edit import pivotDialog
from saload import saveLoad

con = sl.connect('my-test.db')

from PyQt5.QtGui import QFont, QTextCharFormat, QPalette, QPainter, QColor, QIcon, QPen  # QPainter, QPen,QBrush,
from PyQt5.QtCore import Qt, QDate, QSettings, QRect  # , QByteArray  # QTimer, QSize,

# from data_view import DataFrameViewer
from PyQt5.QtWidgets import *

import numpy as np
import pandas as pd
import sys

from functools import partial

# from piv_edit import pivotDialog
# from saload import saveLoad
# from docWiz import docPopup

# from cal_exp import calendarEdit
from super_bc import SuperCombo, SuperButton

# from email_doc import login

class Window(QMainWindow):
    def __init__(self):
        super().__init__()
        self.first_show = True
        self.setWindowTitle('Call Schedule Optimizer')
        self.setWindowIcon(QIcon('icons/calendar-blue.png'))

        # self.settings = QSettings('Claassens Software', 'Calling LLB_2022')

    def showEvent(self, event):
        if self.first_show:
            self.first_show = False

            print(f'\n{string_break}\n|| Init Doc Window ||\n{string_break}\n')

            # init items
            self._set_list()

            self._set_empty()

            self.set_date_format()
            self._setup_load()
            self._set_dataframes()

            self._creat_toolbar()
            self._create_tools()
            self._set_center()

            self._set_clinic()
            self._update_set()
            super().showEvent(event)

    def _set_list(self):
        """inits butons"""
        # init SaveLoad Option
        self.save_l = saveLoad(self, False)
        self.wn = 'Show/Hide Weeknumbers'

        # init all combo cmds, name_icon
        self.cmd_ls = {
                       'Start Week Format': ['Sun', 'Mon'],
                       'Setting Mode': ['Assign', 'On Day', 'Read'], # ['Assign', 'Mid', 'Final', 'Written', 'Quiz'],

                       'Date Format': []}

        # init all pushbutton, name_icon todo add to menu, todo grade, grade all, grade sem, grade gear, grade all year
        self.button_list = [self.wn + '_eye-half',  # todo week nof school
                            'Today_calendar-day', 'Save_disk-black',
                            'Apply',
                            'Load_document-excel-table',
                            'Add_calendar--plus', 'Cal Exp_calendar--arrow',
                            'Email_mail-send']

        self.date_n = ['StartDate']  # calselect days

    def _set_empty(self):
        """sets empty lists"""

        self.shifts = ['Assign', 'Mid', 'Final', 'Written', 'Quiz']

        self.active_col = {'Color': Qt.black, 'Fill': Qt.black}
        self.font_style = ['Bold', 'Italic', 'Underline']
        # self.active_doc = self.doc_data[0]['Name']

        self.av = {}
        # self.schedules = []
        self.list_v = {}
        self.action_list = {}
        self.combo = {}
        self.sch_ls = {}
        self.active_shifts = []

        self.default_files = {'grade': 'docInfoN.xlsx',
                              'class': 'docDays.xlsx'}

    def _set_dataframes(self):
        self.cmd_ls['Active Class'] = list(self.doc_data['Doc'])

    def _setup_load(self):
        """loads default scedual last pref"""

        def qdate_from_date(x):
            if isinstance(x, pd.DatetimeTZDtype):
                return QDate(x.year, x.month, x.day)
            elif isinstance(x, int):
                return QDate(1900, 1, 1).addDays(x)
            else:
                return QDate.fromString(x, self.day_f)

        # loading info for each doc
        self.save_l.on_load_fin(self.default_files['grade'], 1)
        print('grade')

        self.save_l.on_load_fin(self.default_files['class'], 0)

    def _creat_toolbar(self):
        self.font_sizes = [7, 8, 9, 10, 11, 12, 13, 14, 18, 24, 36, 48, 64, 72, 96, 144, 288]
        self.tool_bar = QToolBar('Main toolbar')
        self.cal_tool_bar = QToolBar('Calendar')

        self.table_tool = QToolBar('Tables')
        self.col = QColorDialog()

        self.font_op = []
        self.but_edit = {}
        self.font_ty_win = {}

        self.save_op = SuperButton('File Options', self, vals=self.button_list)
        va = [f'{i}_edit-{i.lower()}' for i in self.font_style]
        self.font_head = SuperButton('Style Options', self, vals=va)

        self.tool_bar.addWidget(self.save_op)
        self.tool_bar.addWidget(self.font_head)

        self.font_wig = {'Font': QFontComboBox(),
                         'Size': SuperCombo('Size', self, vals=[str(x) for x in self.font_sizes], run=False),
                         }

        self.but_edit['color'] = ColorButton('Color', self)
        self.but_edit['color_fill'] = ColorButton('Color Fill', self, 'Fill')
        self.tool_bar.addWidget(self.but_edit['color'])
        self.tool_bar.addWidget(self.but_edit['color_fill'])


        self.font_wig['Size'].currentTextChanged.connect(lambda x: self.set_active_font(x, 'Size'))
        self.font_wig['Font'].currentFontChanged.connect(self.set_active_font)

        for k, i in self.font_wig.items():
            if k == 'Font':
                self.tool_bar.addWidget(i)
            else:
                self.tool_bar.addWidget(i.wig)

        # for selectic cal or walkin to edit, disable if not on cal, add conditional to tables
        self.font_edit = SuperCombo('FontEdit', self, vals=self.shifts)
        self.tool_bar.addWidget(self.font_edit.wig)

        self.addToolBar(self.tool_bar)

    def _set_center(self):
        self.cal_wig = Calendar(self)

        self.setCentralWidget(self.cal_wig)
        self.active_wig = 'Cal'

    def _set_clinic(self):
        # one for grades one for assign
        self.doc_stat = DocStatus(self, self.grade_info, 'Doc Info')  # for docter clinic
        self.day_stat = DocStatus(self, self.doc_preferences, ti='Preferences')
        self.day_stat2 = DocStatus(self, self.current_schedule, ti='Current Dayly Stats', pos=Qt.LeftDockWidgetArea)

        self.ti_info = {'Doc Info': self.doc_stat, 'Preferences': self.day_stat, 'Current Dayly Stats': self.day_stat2}

    # noinspection PyArgumentList
    def _create_tools(self):
        self.tool_bar2 = QToolBar()

        self.addToolBar(self.tool_bar2)
        self.addToolBar(self.cal_tool_bar)

        # ___________comboboxes_______

        for wig_name, opt in self.cmd_ls.items():
            k = SuperCombo(wig_name, self, vals=opt)
            self.combo[wig_name] = k
            self.tool_bar2.addWidget(k.wig)

        self.lab = QLabel('date')
        self.da = QDateEdit()
        self.da.setDate(QDate.currentDate())
        self.da.setCalendarPopup(True)
        self.da.dateChanged.connect(lambda x: self.cal_wig.update_date(x))

        tool_layout = QVBoxLayout()
        wig = QWidget()
        wig.setLayout(tool_layout)
        tool_layout.addWidget(self.da)
        tool_layout.addWidget(self.lab)
        self.cal_tool_bar.addWidget(wig)

    def run_cmd(self, i, ex=None):
        print(f'Running Command: {i}  ||\n')
        if i == 'Mode':
            self.cal_wig.swap_select_mode(self.combo[i].currentText())
            self.day_stat2.reset_table()
        elif i in self.font_style:
            self.set_active_font(ty=i)

        elif i == 'Save':

            self._save_user_settings()
        elif i == 'Active':
            # self.active_doc = ex
            self.cen.update_active(ex)
        elif i == self.wn:
            # QCalendarWidget.noVer
            self.cal_wig.set_wig_2()
        elif i == 'Weekday Start':
            self.cal_wig.week_start(ex)
        elif i == "Today":
            self.cal_wig.set_today()

        elif i == 'Cal Exp':
            self._c_exp()

    def _c_exp(self):
        #cal = calendarEdit(self, self.sch_ls)
        # self.file_ls = cal.doc_save()  # todo user email list
        pass

    def doc_on_day(self, date, cfd=None, da='Current'):
        def xvx() -> list:
            doc_x = []
            for x in cfd:
                dy = list(scd[scd['Shift'] == x]['Doc'])
                if len(dy) == 0:
                    dy = [""]
                doc_x.append(dy)
            return doc_x

        data = self.sch_ls[da]
        if cfd is None:
            cfd = ['Call', 'Walkin']
        if isinstance(date, list):
            scd = data.loc[data['Days'].isin(date)]
            dyx = xvx()
        else:
            scd = data.loc[data['Days'] == date]
            dyx = xvx()
            for n in range(len(dyx)):
                dyx[n] = dyx[n][0]
        return dyx

    def set_active_wig(self, wig):
        if self.active_wig in self.ti_info:
            self.ti_info[self.active_wig].close_dia()
        self.active_wig = wig

        print(f'Window ({wig}) is now active')
        self.font_edit.setEnabled(wig == 'Cal')
        if wig == 'Cal':
            tty = self.font_edit.currentText()
            self.active_col['Fill']= self.font_ty[tty]['Fill']

        else:
            tty = self.active_wig
        self.active_col['Color'] = self.font_ty[tty]['Color']
        # self.c

    def set_active_font(self, font=None, ty='Font'):
        if self.font_edit.isEnabled():
            tty = self.font_edit.currentText()

        else:
            tty = self.active_wig

        if ty in ['Bold', 'Underline', 'Italic']:
            self.font_ty[tty][ty] = not self.font_ty[tty][ty]
        else:
            if ty in ['Color', 'Fill']:
                self.col.setCurrentColor(self.font_ty[tty][ty])
                font = QColorDialog().getColor()
            elif ty == 'Size':
                font = int(font)

            self.font_ty[tty][ty] = font

    def _update_set(self):
        print(f'\n{string_break}\n Loading Settings')
        self.setting_keys_combo = {'Date Format': 'dd-MMM-yyyy',  # y-m-d,y-d-m,d-m-y,m-d-y  # todo layer font
                                   'Weekday Format': 'let',  # long,sort,,let
                                   'Start Week Format': 'Sun',
                                   'Mode': 'Single',
                                   'Active Doc': 'Dehlen',
                                   'Setting Mode': 'Call',
                                   }

        self.font_ty = {

                                'Doc Info': {'Font': QFont("Times"), 'Size': self.font_sizes[2], 'Color': QColor(Qt.black),
                                             'AlignH': Qt.AlignHCenter, 'AlignV': Qt.AlignVCenter, 'Bold': False,
                                             'Italic': False, 'Underline': False},

                                'Current Dayly Stats': {'Font': QFont("Times"), 'Size': self.font_sizes[2], 'Color': QColor(Qt.black),
                                                        'AlignH': Qt.AlignHCenter, 'AlignV': Qt.AlignVCenter,
                                                        'Bold': False, 'Italic': False, 'Underline': False},

                                'Preferences': {'Font': QFont("Times"), 'Size': self.font_sizes[2], 'Color': QColor(Qt.black),
                                                'AlignH': Qt.AlignHCenter, 'AlignV': Qt.AlignVCenter, 'Bold': False,
                                                'Italic': False, 'Underline': False},
                                }

        self.settings.beginGroup('combo')

        for ke, v in self.setting_keys_combo.items():
            val = self.settings.value(ke, v)
            self.combo[ke].setCurrentText(val)
            # ke_new = ke.lower().replace(' ', '_')  #
            print(f'Loaded {ke} = {val}')

        self.settings.endGroup()

        self.settings.beginGroup('ActiveShift')
        for i in self.shifts:
            j = self.settings.value(i, True)
            if j:
                self.active_shifts.append(i)
        self.settings.endGroup()

        self.settings.beginGroup('File Locals')
        for i in self.default_files.keys():
            self.default_files[i] = self.settings.value(i, self.default_files[i])
        self.settings.endGroup()

        k = self.settings.allKeys()

        for i, j in [(self.restoreGeometry, "Geometry"), (self.restoreState, "windowState")]:
            if j in k:
                va = self.settings.value(j)
                i(va)

        print(f'Finished Loading Settings\n{string_break}\n')

    def set_date_format(self):
        conect = ['.', '/', ',', '-', ' ']
        y = 'yyyy'
        j = []
        for co in conect:
            for yf in range(2):
                for day in range(2, 4):
                    di = "d" * day
                    for mon in range(2, 5):
                        mo = "M" * mon
                        f = [di, mo]
                        for i in range(2):
                            if day == 3 and i == 0:
                                st = [f'{di}{co}d{co}{mo}',
                                      f'{di}{co}{mo}{co}d']
                            else:
                                st = [f'{f[i]}{co}{f[(i + 1) % 2]}']
                            if yf == 0:
                                j.extend(f'{y}{co}{si}' for si in st)
                            else:
                                j.extend(f'{si}{co}{y}' for si in st)

        self.cmd_ls['Date Format'] = j

    def _save_user_settings(self):
        self.settings = QSettings('Claassens Software', 'User Saved')
        self.user_settings()

    def user_settings(self, last_ses=True):
        print(f'\n{string_break}\nSaving Settings')
        self.settings.setValue("Geometry", self.saveGeometry())
        self.settings.setValue("windowState", self.saveState())

        if last_ses:
            self.settings.beginGroup('combo')

            for ke in self.setting_keys_combo.keys():
                val = self.combo[ke].currentText()
                self.settings.setValue(ke, val)
                print(f'Saving{ke} = {val}')
            self.settings.endGroup()

            self.settings.beginGroup('ActiveShift')
            for i in self.shifts:
                self.settings.setValue(i, i in self.active_shifts)
            self.settings.endGroup()

            self.settings.beginGroup('File Locals')
            for i, j in self.default_files.items():
                self.settings.setValue(i, j)
            self.settings.endGroup()

            setting = QSettings('Claassens School', 'School')
            setting.setValue('Load Last Session', self.load_d)
            setting.setValue('Show on Startup', self.on_start)
            print(f'Finished Saving Settings\n{string_break}\n')

    def closeEvent(self, event):
        print(f'\n{string_break}\nClosing Doc\n{string_break}\n')
        self.user_settings(self.load_d)
        super().closeEvent(event)

        for i in self.ti_info.values():
            i.close_dia()

    def legend(self):
        print('legend')

    def ret_font(self, na):
        font_in = self.font_ty[na]
        font = font_in['Font']
        font.setPixelSize(font_in['Size'])

        font.setCapitalization(self.cap_op.index(font_in['Capital']))
        for i, j in {'Bold': font.setBold, 'Italic': font.setItalic, 'Underline': font.setUnderline}.items():
            j(font_in[i])  # true false

        align = [font_in['AlignH'], font_in['AlignV']]
        return font, font_in['Color'], align


class Calendar(QCalendarWidget):
    def __init__(self, par):
        super().__init__()
        self.par = par
        self.st_h = 1

        self.sel = 'Single'

        self.full_date_list = [QDate.currentDate(), QDate.currentDate()]
        self.clicked.connect(lambda checked: self.on_cl(checked))
        self.setGridVisible(True)
        self.set_menu()

        self.set_wig_2()
        self._init_calendar()
        self._init_high()

    def mousePressEvent(self, event):
        print('clicked cal')
        self.par.set_active_wig('Cal')
        super().mousePressEvent(event)

    def _init_high(self):
        self.highlight_format = QTextCharFormat()
        self.highlight_format.setBackground(self.palette().brush(QPalette.Highlight))
        self.highlight_format.setForeground(self.palette().color(QPalette.HighlightedText))

    def _init_calendar(self):
        self.calendar_view = self.findChild(QTableView, "qt_calendar_calendarview")
        self.calendar_delegate = CalendarDayDelegate(par=self)
        self.calendar_view.setItemDelegate(self.calendar_delegate)

    def set_wig_2(self):
        self.st_h = (self.st_h + 1) % 2

        i3 = self.VerticalHeaderFormat(self.st_h)
        self.setVerticalHeaderFormat(i3)

    def week_start(self, j):
        k = 1 if j == 'Mon' else 7
        self.setFirstDayOfWeek(Qt.DayOfWeek(k))

    def set_today(self):
        self.showToday()

    def on_cl(self, date):
        def fr_ls(in_date, xv, yv):
            if yv:
                date_v_l = []
                dt = self.full_date_list[-1].daysTo(in_date)

                sn = np.sign(dt)
                for n in range(0, dt + sn, sn):
                    date_v_l.append(self.full_date_list[-1].addDays(n))
            else:
                date_v_l = [in_date]

            if xv:
                if len(date_v_l) <= 1 and date_v_l[0] in self.full_date_list:
                    self.full_date_list.remove(date_v_l)
                else:
                    self.full_date_list.extend(date_v_l)
            else:
                self.full_date_list = date_v_l

        if self.par.combo['Mode'].currentText() == 'Range':
            self.update_date(date)
        else:
            self.print_selected(QTextCharFormat())
            ap1 = [False, False]

            mo = QApplication.instance().keyboardModifiers()

            for ni, ij in enumerate([Qt.ControlModifier, Qt.ShiftModifier]):
                if mo & ij:
                    ap1[ni] = True

            fr_ls(date, *ap1)

        self.print_selected(self.highlight_format)
        self.par.set_active_wig('Cal')

    def print_selected(self, form):
        for date in self.full_date_list:
            self.setDateTextFormat(date, form)

    def swap_select_mode(self, mo):
        if mo == 'Range':
            en = True

        else:
            en = False
        for i in self.par.date_list.keys():
            self.par.date_list[i].setEnabled(en)

    def add_text(self, ite):
        xi = self.menu_item[ite].isChecked()
        if xi:
            self.par.active_shifts.append(ite)
        else:
            self.par.active_shifts.remove(ite)
        self.par.legend()

    def add_sch(self, ite):
        xi = self.menu_item[ite].isChecked()
        if xi:
            self.par.active_sch.append(ite)
        else:
            self.par.active_sch.remove(ite)
        self.par.legend()

    def _add_menu(self, pos):
        self.menu_item = {}
        print('Context Menu opened')
        self.context_menu = QMenu("Show Events", self)
        # self.context_menu.addSection('Shifts')
        for ite in self.par.shifts:

            action = QAction(ite)
            action.setCheckable(True)
            if ite in self.par.active_shifts:
                action.setChecked(True)
            action.triggered.connect(partial(self.add_text, ite))
            self.menu_item[ite] = action
            self.context_menu.addAction(action)

        print('next sec')
        self.context_menu.addSeparator()
        for i in self.par.schedules:
            action = QAction(i)

            action.setCheckable(True)
            if i in self.par.active_sch:
                action.setChecked(True)
            if i not in self.par.avalible_sch:
                action.setEnabled(False)

            action.triggered.connect(partial(self.add_sch, i))
            self.menu_item[i] = action
            self.context_menu.addAction(action)
            print('add action sch')

        self.context_menu.exec(self.mapToGlobal(pos))

    def set_menu(self):
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        # def setContextMenuPolicy(self):
        self.customContextMenuRequested.connect(self._add_menu)


# class DStat
class DocStatus(DataFrameViewer):  # self.doc_dataframe_items
    def __init__(self, par, df, ti='Clinic', pos=Qt.RightDockWidgetArea):
        super().__init__(df)
        self.df_init = df.copy()
        self.ti = ti
        self.sort_ascend = True
        self.sort_col = 'Name'
        self.par = par
        self.pos = pos
        self.d_r = 30
        self.dialog = pivotDialog(self.df_init, self)
        self.dia_act = False
        #
        # self.horizontalHeader().sectionClicked.connect(self.sort_by)
        # self.cellClicked.connect(self.tab_s)
        # self.cellDoubleClicked.connect(self.set_popup)
        self.dia = None
        self._init_dock()
        # self.reset_table()

    def mousePressEvent(self, event):
        if self.par.active_wig != self.ti:
            self.dialog.show()
            self.dia_act = True
            self.par.set_active_wig(self.ti)

    def close_dia(self):
        if self.dia_act:
            self.dialog.close()

    def _init_dock(self):
        self.dock = QDockWidget(self.ti)
        self.dock.setWidget(self)
        self.par.addDockWidget(self.pos, self.dock)

    def reset_table(self):
        print('update df')
        self.set_data()
        print(self.df.head())
        self.dataView.model().layoutChanged.emit()

    def reset_table_main(self, dd, r, c):
        # r += 1
        self.setHorizontalHeaderLabels(list(dd.columns))
        self.setRowCount(r)
        self.setColumnCount(c)
        for n in range(r):
            for m in range(c):
                tx = dd.iloc[n, m]
                if isinstance(tx, QDate):
                    j = tx.toString(self.par.combo['Date Format'].currentText())
                else:
                    j = str(tx)
                self.setItem(n, m, QTableWidgetItem(j))

    def tab_s(self, row_n, col_n):
        if row_n == 0:
            self.sort_by(col_n)
        r_n = self.item(row_n, 0).text()
        self.par.combo['doc'].setCurrentText(r_n)

    def sort_by(self, col):
        new_col = self.horizontalHeaderItem(col).text()
        if new_col == self.sort_col:
            self.sort_ascend = not self.sort_ascend
        else:
            self.sort_ascend = True
            self.sort_col = new_col
        print(f'column {self.sort_col}:  ascend {self.sort_ascend}')

    def update_active(self, doc):
        na = list(self.par.doc_data['Name']).index(doc)
        for r in range(self.rowCount()):
            for i in range(self.columnCount()):
                if r != na:
                    col = Qt.white
                else:
                    col = Qt.cyan
                self.item(r, i).setBackground(col)


class SideDoc(QDockWidget):
    def __init__(self, par, loc, name):
        super().__init__(loc)
        self.par = par
        self.name = name

    def closeEvent(self, event):
        self.par.settings.beginGroup('Docks')
        self.par.settings.beginGroup(self.name)

        self.par.settings.setValue('isOpen', False)  # todo to par main, read main
        self.par.settings.setValue('Area', self.area)  # is undocked?

        self.par.settings.endGroup()
        self.par.settings.endGroup()

        self.settings.setValue("Geometry", self.saveGeometry())  # todo do we Have?
        self.settings.setValue("windowState", self.saveState())
        pass


class dataPopup(QDialog):
    # noinspection PyArgumentList
    def __init__(self, par, res=None):
        super().__init__()
        self.res = res
        self.par = par
        self.table_op = [self.par.day_stat, self.par.day_stat2, self.par.doc_stat]
        self.doc_data = {}
        self.setModal(False)
        self._init_layout()

        # self.show()

    def _init_layout(self):
        print('show wigit')
        self.dia_lay = QVBoxLayout()
        self.horizontalLayout = QHBoxLayout()
        self.verticalLayout_2 = QVBoxLayout()
        self.verticalLayout = QVBoxLayout()

        self.name_lay = QLabel('Name')
        self.name_edit = QLineEdit()
        if self.res:
            self.name_edit.setText(self.res)

        # noinspection PyArgumentList
        self.verticalLayout_2.addWidget(self.name_lay)
        # noinspection PyArgumentList
        self.verticalLayout_2.addWidget(self.name_edit)
        # self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        # self.verticalLayout_2.addItem(self.verticalSpacer)

        self.doc_op_check = {}
        for op in self.doc_op:
            op_box = QCheckBox(op)
            self.doc_op_check[op] = op_box
            # noinspection PyArgumentList
            self.verticalLayout.addWidget(op_box)

        self.buttonBox = QDialogButtonBox()
        self.buttonBox.setOrientation(Qt.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.Cancel | QDialogButtonBox.Save)
        self.buttonBox.setCenterButtons(False)
        self.buttonBox.accepted.connect(self.acc)
        self.buttonBox.rejected.connect(self.rej)

        # noinspection PyArgumentList
        self.dia_lay.addWidget(self.buttonBox)
        self.horizontalLayout.addLayout(self.verticalLayout_2)
        self.horizontalLayout.addLayout(self.verticalLayout)

        self.dia_lay.addLayout(self.horizontalLayout)
        self.setLayout(self.dia_lay)

    def acc(self):
        print('accet')
        if self.res:
            del self.doc_data[self.res]

        kk = []
        for i, k in self.doc_op_check.items():
            if k:
                kk.append(i)
        self.doc_data[self.name_edit.text()] = kk
        print('doc d', self.doc_data)

        self.accept()

    def rej(self):
        print('reject')
        self.reject()


class CalendarDayDelegate(QItemDelegate):
    def __init__(self, parent=None, projects=None, par=None):
        super(CalendarDayDelegate, self).__init__(parent=parent)

        self.projects = projects
        # self.items_ls = {'Call': '', }
        self.par = par
        self.labs = []
        self.space = {'Current': 0.6, 'Edited': 0.3}  # todo edit offset
        self.space_ver = 0.15
        self.board_size = 1
        self.v_off = 0.4
        self.board_col = {'Current': Qt.red, 'Edited': Qt.black}
        self.v_space = 2
        self.last_month = True

    # def draw_rect(self):
    def paint(self, painter: QPainter, option, index):

        painter._date_flag = index.row() > 0
        super(CalendarDayDelegate, self).paint(painter, option, index)

        # only calls on date
        if painter._date_flag:

            # find month and year of date
            date_num_full = index.data()
            index_loc = (index.row(), index.column())

            year = self.par.yearShown()
            month = self.par.monthShown()

            # check if previous or next month
            if date_num_full > 7 and index_loc[0] == 1:
                if month == 1:
                    year -= 1
                    month = 12
                else:
                    month -= 1
            elif date_num_full < 15 and index_loc[0] > 4:
                if month == 12:
                    year += 1
                    month = 1
                else:
                    month += 1

            # converts to QDate
            date = QDate(year, month, date_num_full)
            active_shifts = self.par.par.active_shifts
            painter.save()

            # rectangle of current date
            rect = option.rect
            x, y, w, h = rect.getRect()

            # loop through schedules
            for da in self.par.par.active_sch:
                for n, i in enumerate(active_shifts):  # loop throw shifts
                    doc = self.par.par.doc_on_day(date, [i], da)[0]

                    # back_color = Qt.red
                    siz = int(w * self.space[da])  # todo sort
                    size_v = int(w * self.space_ver)
                    if i == 'Call':
                        size_v += 10
                    if da == 'Current':
                        x0 = x + w - siz - self.v_space
                        y_off = 0
                    else:
                        x0 = self.v_space
                        y_off = self.v_off

                    if doc != "":
                        rect2 = QRect(x0, y + self.v_space + y_off, siz, size_v)

                        font, color, align = self.par.par.ret_font(i)
                        painter.setFont(font)
                        # align = self.op[n]

                        back_color = self.par.par.font_ty[i]['Fill']
                        y += size_v + self.v_space + self.board_size * 2

                        painter.setPen(QPen(self.board_col[da], self.board_size))
                        painter.setBrush(back_color)
                        painter.drawRect(rect2)

                        painter.setPen(color)
                        painter.drawText(rect2, align[0] | align[1], doc)  # , option=)

            painter.restore()

    def drawDisplay(self, painter, option, rect, text):
        if painter._date_flag:
            option.displayAlignment = Qt.AlignTop | Qt.AlignLeft
        super(CalendarDayDelegate, self).drawDisplay(painter, option, rect, text)


class ColorButton(QPushButton):
    def __init__(self, col='', par=None, ty='Color'):
        if ty == 'color':
            tx = 'icons/edit-color.png'
        else:
            tx = 'icons/paint-can-color.png'
        super().__init__(QIcon(tx), col)
        self.ty = ty
        self.par = par
        self.clicked.connect(lambda _: self.par.set_active_font(ty=self.ty))

    def paintEvent(self, event):
        super().paintEvent(event)
        w, h = self.width(), self.height()
        r_w = w // 3
        r_h = h // 4

        rect = QRect((w - r_w) // 2, h - r_h - 2, r_w, r_h)
        # rect.moveTo(self.rect().bottomRight() - rect.bottomRight())

        painter = QPainter(self)
        painter.setBrush(self.par.active_col[self.ty])
        painter.drawRect(rect)


string_break = '_' * 10
if __name__ == '__main__':
    strs = ' ___     ____     ____\n' \
           '|   \\   |    |   |    |\n' \
           '|    )  |    |   |\n' \
           '|___/   |____|   |____|\n\n'
    print(strs)
    print(string_break)
    app = QApplication(sys.argv)
    win = Window()
    win.show()
    sys.exit(app.exec_())
