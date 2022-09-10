import os.path
import re

from PyQt5.QtCore import Qt, QDate
from PyQt5.QtWidgets import *
import pandas as pd
import sys


def save_csv(file, data):

    print('load csv')
    data.to_csv(file)


def save_json(file, data):
    data.to_json(file)
    print('load json')





def load_csv(file):
    print('load csv')
    data = pd.read_csv(file)
    return data


def load_json(file):
    data = pd.read_json(file)
    print('load json')
    return data


def load_ex(file):
    print('Load ex')
    xl = pd.ExcelFile(file)
    data = {}
    docs = xl.sheet_names
    for sheet in docs:
        data[sheet] = pd.read_excel(xl, sheet_name=sheet)
    return data


class saveLoad(QFileDialog):
    def __init__(self, par, sa=True):
        super().__init__()
        self.setModal(True)
        self.sa = sa
        self.par = par
        self.df_key = ['dates Here','Dates away', 'days want', 'pref', 'time per patient', 'categories']

        self._set_f_t()
        self._on_save_load()


        # self.load_settings()
        self.func = [self.save_doc_preferences,  # of day,
                     self.save_doc_info,  # of properties and delta t, ]
                     self.save_secdual]

        self.func_load = [self.load_doc_preferences,  # of day,
                          self.load_doc_info,  # of properties and delta t, ]
                          self.load_secdual]

        self.save_fucs = {'excel': self.save_ex, 'csv': save_csv, 'json': save_json}
        self.load_fucs = {'excel': load_ex, 'csv': load_csv, 'json': load_json}

        # self.currentChanged.connect(self._on_pox)
        # self._on_pox()
        # self._on_start()
        # self.save_settings()

    def save_ex(self, file, data):
        print('save ex')

        with pd.ExcelWriter(file, engine="openpyxl") as writer:
            data.to_excel(writer, sheet_name='Days', index=False)

            pd.DataFrame({'Format': [self.par.combo['Date Format'].currentText()]}).to_excel(writer, sheet_name='Format',
                                                                                           index=False)
            print('saved')

    def on_save_load(self):
        self._on_save_load()

    def _on_start(self):
        self.dia = QDialog(self)
        self.dia_lay = QVBoxLayout()
        self.name_lay = QLabel('Name')
        self.box = QComboBox()
        self.box.addItems(['prefernces', 'Info', 'Scedule'])
        self.dia_lay.addWidget(self.name_lay)
        self.dia_lay.addWidget(self.box)

        # if dia not load breack else load

        self.buttonBox = QDialogButtonBox()
        self.buttonBox.setOrientation(Qt.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.Cancel | QDialogButtonBox.Save)
        self.buttonBox.setCenterButtons(False)
        self.buttonBox.accepted.connect(self._dia_acc)
        self.buttonBox.rejected.connect(self.dia.reject)
        self.dia_lay.addWidget(self.buttonBox)
        self.dia.setLayout(self.dia_lay)
        self.on_save()

        self.dia.exec()

    def _dia_acc(self):
        self.f_ty = self.box.currentIndex()
        self.dia.accept()
        #

    def _on_save_load(self):
        if self.sa:
            self.end_fun = self.on_save_fin
            self.accepted.connect(self.end_fun)
            self.save_settings()
        else:
            self.end_fun = self.on_load_fin
            self.accepted.connect(self.end_fun)
            self.load_settings()

    def on_save_fin(self, file=None, ty=None):
        if file is None:
            file = self.selectedFiles()[0]
        if ty is None:
            ty = self.f_ty

        if '.' not in file[-5:]:
            print('not in')
            filter_sel = self.selectedNameFilter()
            fil = re.search('\((.+?)\)', filter_sel).group(1).replace('*', '')
            file += fil

        ex = os.path.splitext(file)[-1]
        fi = self.func[ty]
        data = fi()
        type1 = 'excel'

        for i, j in self.f_t.items():
            if ex in j:
                type1 = i
        fi = self.save_fucs[type1]
        fi(file,data)

    def on_load_fin(self,file=None,ty=0):
        if file is None:
            file = self.selectedFiles()[0]

        ex = os.path.splitext(file)[-1]

        type1 = 'excel'

        for i, j in self.f_t.items():
            if ex in j:
                type1 = i

        fi = self.load_fucs[type1]
        data = fi(file)
        #     load = pref
        lo = self.func_load[ty]
        #
        lo(data)

    def ff(self):
        print('hi')
        f = self.children()
        print(f)

    def load_f_type(self, names):

        st = []

        for na in names:
            if self.acceptMode() == QFileDialog.AcceptOpen:
                st_2 = ', '.join([f'*.{ty}' for ty in self.f_t[na]])
                na_1 = f'{na} files: ({st_2})'
                st.append(na_1)
            else:
                print('ya')
                for ty in self.f_t[na]:
                    na_1 = f'{na} file: (*.{ty})'
                    st.append(na_1)
        return ';; '.join(st)

    def on_save(self):
        name = 'Shedual.xslm'
        self.setDirectory(name)

    def _set_f_t(self):
        self.combo = {'User Readable': ['exel', 'csv'], 'data frame': ['json', 'exel', 'csv']}
        self.f_t = {'json': ['json'], 'csv': ['csv'], 'excel': ['xmls', 'xslm'], 'text': 'txt'}

    def load_func(self):
        self.setDefaultSuffix('csv')
        self.setAcceptMode(QFileDialog.AcceptOpen)

    # @load_func
    def load_settings(self):
        self.load_func()
        self.setNameFilter(['json', 'csv', 'excel'])
        pass

    def setNameFilter(self, filters):
        super().setNameFilter(self.load_f_type(filters))

    def load_doc_preferences(self, data):
        self.par.doc_preferences = data['Days']

    def load_secdual(self, data):
        self.par.current_schedule = data['Days']
        try:
            self.par.day_f = list(data['Format']['Format'])[0]
        except KeyError:
            raise ValueError('no Format')
        pass

    def load_doc_info(self, data):  # note for doc excel
        self.par.doc_data = data['Sheet1']

    def save_doc_preferences(self):
        print('save_doc pref')
        df = {'d': 20, 'x': 50}
        print('data = ', df)
        return df

    def save_doc_info(self):
        print('save_doc_iinfo')
        df = {'d': 20, 'x': 50}
        print('data = ', df)
        return df

    def save_secdual(self):
        print('save_doc_sch')
        df = self.par.current_schedule
        df['Days'] = df['Days'].apply(lambda x: x.toString(self.par.combo['Date Format'].currentText()))
        print('data = ', df.head())
        return df

    def save_settings(self):
        name = 'Shedual.csv'
        self.setDirectory(name)
        self.setDefaultSuffix('csv')
        self.setAcceptMode(QFileDialog.AcceptSave)
        self.setNameFilter(['json', 'csv', 'excel'])