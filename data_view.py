from PyQt5 import QtGui, QtCore, QtWidgets
from PyQt5.QtCore import QModelIndex, QSize, Qt, QItemSelectionModel, QDate
from PyQt5.QtGui import QPainter, QFont, QFontMetrics, QPalette, QBrush, QColor, QTransform
from PyQt5.QtWidgets import QSizePolicy
import pandas as pd
import numpy as np

import threading


def pos_adj(self, pos, func):
    jk = self.over_header_edge(pos)
    if jk is not None:

        if self.orientation == Qt.Horizontal:
            func(True, jk)
        elif self.orientation == Qt.Vertical:
            func(False, jk)
        return True
    else:
        self.header_being_resized = None


# @self
def auto_rc(self, a1, pos):
    if a1:
        self.parent.auto_size_column(pos)
    else:
        self.parent.auto_size_row(pos)


def resize_start(self, a1, pos):
    self.header_being_resized = pos
    self.resize_start_position = pos
    if a1:
        self.initial_header_size = self.columnWidth(self.header_being_resized)
    else:
        self.initial_header_size = self.rowHeight(self.header_being_resized)


class DataFrameViewer(QtWidgets.QWidget):
    """
    Displays a DataFrame as a table.
    Args:
        df (DataFrame): The DataFrame to display
    """

    def __init__(self, df, inplace=True):

        if not inplace:
            self.df = df.copy()
        else:
            self.df = df

        super().__init__()
        # Indicates whether the widget has been shown yet. Set to True in
        self._loaded = False

        if not type(df) == pd.DataFrame:
            orig_type = type(df)
            self.df = self.df.to_frame()
            print(f'DataFrame was automatically converted from {orig_type} to DataFrame for viewing')

        # Set up DataFrame TableView and Model
        self.dataView = DataTableView(self.df, parent=self)

        # Create headers
        self.columnHeader = HeaderView(parent=self, df=self.df, orientation=Qt.Horizontal)
        self.indexHeader = HeaderView(parent=self, df=self.df, orientation=Qt.Vertical)

        # Set up layout
        self.gridLayout = QtWidgets.QGridLayout()
        self.setLayout(self.gridLayout)

        # Link scrollbars
        # Scrolling in data table also scrolls the headers
        self.dataView.horizontalScrollBar().valueChanged.connect(self.columnHeader.horizontalScrollBar().setValue)
        self.dataView.verticalScrollBar().valueChanged.connect(self.indexHeader.verticalScrollBar().setValue)
        # Scrolling in headers also scrolls the data table
        self.columnHeader.horizontalScrollBar().valueChanged.connect(self.dataView.horizontalScrollBar().setValue)
        self.indexHeader.verticalScrollBar().valueChanged.connect(self.dataView.verticalScrollBar().setValue)

        self.dataView.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.dataView.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        # Disable scrolling on the headers. Even though the scrollbars are hidden, scrolling by dragging desyncs them
        self.indexHeader.horizontalScrollBar().valueChanged.connect(lambda: None)

        self.gridLayout.setContentsMargins(0, 0, 0, 0)
        self.gridLayout.setSpacing(0)

        # Toggle level names
        if not (any(df.columns.names) or df.columns.name):
            self.columnHeader.verticalHeader().setFixedWidth(0)
        if not (any(df.index.names) or df.index.name):
            self.indexHeader.horizontalHeader().setFixedHeight(0)

        # Add items to layout
        self.gridLayout.addWidget(self.columnHeader, 0, 1, 1, 2)
        self.gridLayout.addWidget(self.indexHeader, 1, 0, 2, 2)
        self.gridLayout.addWidget(self.dataView, 2, 2, 1, 1)
        self.gridLayout.addWidget(self.dataView.horizontalScrollBar(), 3, 2, 1, 1)
        self.gridLayout.addWidget(self.dataView.verticalScrollBar(), 2, 3, 1, 1)

        # These expand when the window is enlarged instead of having the grid squares spread out
        self.gridLayout.setColumnStretch(4, 1)
        self.gridLayout.setRowStretch(4, 1)

        # These placeholders will ensure the size of the blank spaces beside our headers
        self.gridLayout.addWidget(TrackingSpacer(ref_x=self.columnHeader.verticalHeader()), 3, 1, 1, 1)
        self.gridLayout.addWidget(TrackingSpacer(ref_y=self.indexHeader.horizontalHeader()), 1, 2, 1, 1)
        self.gridLayout.addItem(QtWidgets.QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Expanding), 0, 0, 1, 1)
        self.data_items = [self.dataView, self.columnHeader, self.indexHeader]
        # Styling
        for header in [self.indexHeader, self.columnHeader]:
            header.setStyleSheet("background-color: white;"
                                 "selection-color: black;"
                                 "selection-background-color: #EAEAEA;")

        self.dataView.setStyleSheet("background-color: white;"
                                    "alternate-background-color: #F4F6F6;"
                                    "selection-color: black;"
                                    "selection-background-color: #BBDEFB;")

        for item in self.data_items:
            item.setContentsMargins(0, 0, 0, 0)
            item.setStyleSheet(item.styleSheet() + "border: 0px solid black;")
            item.setItemDelegate(NoFocusDelegate())

    def showEvent(self, event: QtGui.QShowEvent):
        """
        Initialize column and row sizes on the first time the widget is shown
        """
        if not self._loaded:
            # Set column widths
            for column_index in range(self.columnHeader.data_model.columnCount()):
                self.auto_size_column(column_index)

            # Set row heights
            # Just sets a single uniform row height based on the first N rows for performance.
            num = 100
            default_row_height = 30
            for row_index in range(self.indexHeader.data_model.rowCount())[:num]:
                self.auto_size_row(row_index)
                height = self.indexHeader.rowHeight(row_index)
                default_row_height = max(default_row_height, height)

            # Set limit for default row height
            default_row_height = min(default_row_height, 100)

            self.indexHeader.verticalHeader().setDefaultSectionSize(default_row_height)
            self.dataView.verticalHeader().setDefaultSectionSize(default_row_height)

        self._loaded = True
        event.accept()

    def auto_size_column(self, column_index):
        """
        Set the size of column at column_index to fit its contents
        """
        padding = 20

        self.columnHeader.resizeColumnToContents(column_index)
        width = self.columnHeader.columnWidth(column_index)

        # Iterate over the column's rows and check the width of each to determine the max width for the column
        # Only check the first N rows for performance. If there is larger content in cells below it will be cut off
        num = 100
        for i in range(self.dataView.data_model.rowCount())[:num]:
            mi = self.dataView.data_model.index(i, column_index)
            text = self.dataView.data_model.data(mi)
            w = self.dataView.fontMetrics().boundingRect(text).width()

            width = max(width, w)

        width += padding

        # add maximum allowable column width so column is never too big.
        max_allowable_width = 500
        width = min(width, max_allowable_width)

        self.columnHeader.setColumnWidth(column_index, width)
        self.dataView.setColumnWidth(column_index, width)

        self.dataView.updateGeometry()
        self.columnHeader.updateGeometry()

    def auto_size_row(self, row_index):
        """
        Set the size of row at row_index to fix its contents
        """
        padding = 20

        self.indexHeader.resizeRowToContents(row_index)
        height = self.indexHeader.rowHeight(row_index)

        # Iterate over the row's columns and check the width of each to determine the max height for the row
        # Only check the first N columns for performance.
        num = 100
        for i in range(min(num, self.dataView.data_model.columnCount())):
            mi = self.dataView.data_model.index(row_index, i)
            cell_width = self.columnHeader.columnWidth(i)
            text = self.dataView.data_model.data(mi)
            # Gets row height at a constrained width (the column width).
            # This constrained width, with the flag of Qt.TextWordWrap
            # gets the height the cell would have to be to fit the text.
            constrained_rect = QtCore.QRect(0, 0, cell_width, 0)
            h = self.dataView.fontMetrics().boundingRect(constrained_rect,
                                                         Qt.TextWordWrap,
                                                         text).height()

            height = max(height, h)

        height += padding

        self.indexHeader.setRowHeight(row_index, height)
        self.dataView.setRowHeight(row_index, height)

        self.dataView.updateGeometry()
        self.indexHeader.updateGeometry()

    def set_data(self, df=None):
        if df is not None:
            self.df = df
        for item in self.data_items:
            item.set_data(self.df)

    def keyPressEvent(self, event):

        QtWidgets.QWidget.keyPressEvent(self, event)

        if event.matches(QtGui.QKeySequence.Copy):
            print('Ctrl + C')
            self.dataView.copy()
        if event.matches(QtGui.QKeySequence.Paste):
            self.dataView.paste()
            print('Ctrl + V')
        if event.key() == Qt.Key_P and (event.modifiers() & Qt.ControlModifier):
            self.dataView.print()
            print('Ctrl + P')
        if event.key() == Qt.Key_D and (event.modifiers() & Qt.ControlModifier):
            self.debug()
            print('Ctrl + D')

    def debug(self):
        print(self.columnHeader.sizeHint())
        print(self.dataView.sizeHint())
        print(self.dataView.horizontalScrollBar().sizeHint())


# Remove dotted border on cell focus.  https://stackoverflow.com/a/55252650/3620725
class NoFocusDelegate(QtWidgets.QStyledItemDelegate):
    def paint(self, painter, veiw_item, index):
        if veiw_item.state & QtWidgets.QStyle.State_HasFocus:
            veiw_item.state = veiw_item.state ^ QtWidgets.QStyle.State_HasFocus
        super().paint(painter, veiw_item, index)


class DataTableModel(QtCore.QAbstractTableModel):
    """
    Model for DataTableView to connect for DataFrame data
    """

    def __init__(self, df, par, parent=None):
        super().__init__(parent)
        self.df = df
        self.par = par
        self.align = Qt.AlignCenter  # todo for each type?

    def headerData(self, section, orientation, role=None):
        # Headers for DataTableView are hidden. Header data is shown in HeaderView
        pass

    def columnCount(self, parent=None):
        if type(self.df) == pd.Series:
            return 1
        else:
            return self.df.columns.shape[0]

    def rowCount(self, parent=None):
        return len(self.df)

    # Returns the data from the DataFrame
    def data(self, index, role=QtCore.Qt.DisplayRole):
        if any(role == x for x in [QtCore.Qt.DisplayRole,
                                   QtCore.Qt.EditRole,
                                   QtCore.Qt.ToolTipRole,
                                   QtCore.Qt.DecorationRole]):
            row = index.row()
            col = index.column()
            cell = self.df.iloc[row, col]

            # NaN case
            if pd.isnull(cell):
                return ""

            # Float formatting
            if isinstance(cell, (float, np.floating)):
                if not role == QtCore.Qt.ToolTipRole:
                    return "{:.4f}".format(cell)
            if isinstance(cell, QDate):
                if role == QtCore.Qt.DisplayRole:
                    return cell.toString(self.par.par.combo['Date Format'].currentText())
                elif role == QtCore.Qt.DecorationRole:

                    return QtGui.QIcon('icons/calendar.png')
            elif (self.df.columns.values[col] == 'Doc' or self.df.index.values[row] == 'Doc') \
                    and role == QtCore.Qt.DecorationRole:
                id2 = self.par.par.doc_data.loc[self.par.par.doc_data['Doc'] == cell, 'Gender']
                if id2.values[0] == 'Male':
                    ids = 'icons/user-medical.png'
                else:
                    ids = 'icons/user-medical-female.png'
                return QtGui.QIcon(ids)
            elif role == QtCore.Qt.ToolTipRole and pd.isnull(cell):
                return "NaN"

            return str(cell)
        elif role in [Qt.FontRole, Qt.ForegroundRole, Qt.TextAlignmentRole]:
            font, color, align = self.par.par.ret_font(self.par.ti)
            if role == Qt.FontRole:
                return font
            elif role == Qt.ForegroundRole:
                return color
            else:
                return align[0] | align[1]

    def flags(self, index):
        # Set the table to be editable
        return QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable

    # Set data in the DataFrame. Required if table is editable
    def setData(self, index, value, role=None):
        if role == QtCore.Qt.EditRole:
            row = index.row()
            col = index.column()
            try:
                self.df.iat[row, col] = value
            except Exception as e:
                print(e)
                return False
            self.dataChanged.emit(index, index)

            return True


class DataTableView(QtWidgets.QTableView):
    """
    Displays the DataFrame data as a table
    """

    def __init__(self, df, parent, orientation=None):
        super().__init__(parent)
        self.parent = parent
        self.orientation = orientation
        self.setMouseTracking(True)

        # Create and set model

        # These are used during column resizing
        self.header_being_resized = None
        self.resize_start_position = None
        self.initial_header_size = None
        self._init_0(df)

    def _init_0(self, df):
        self.data_model = DataTableModel(df, self.parent)
        self.setModel(self.data_model)
        # Hide the headers. The DataFrame headers (index & columns) will be displayed in the DataFrameHeaderViews
        self.horizontalHeader().hide()
        self.verticalHeader().hide()

        # Link selection to headers
        self.selectionModel().selectionChanged.connect(self.on_selection_changed)

        # Settings
        # self.setWordWrap(True)
        # self.resizeRowsToContents()
        self.setAlternatingRowColors(True)
        self.setHorizontalScrollMode(QtWidgets.QAbstractItemView.ScrollPerPixel)
        self.setVerticalScrollMode(QtWidgets.QAbstractItemView.ScrollPerPixel)

    def on_selection_changed(self):
        """
        Runs when cells are selected in the main table. This logic highlights the correct cells in the vertical and
        horizontal headers when a data cell is selected
        """
        column_header = self.parent.columnHeader
        index_header = self.parent.indexHeader

        # The two blocks below check what columns or rows are selected in the data table and highlights the
        # corresponding ones in the two headers. The if statements check for focus on headers, because if the user
        # clicks a header that will auto-select all cells in that row or column which will trigger this function
        # and cause and infinite loop

        if not column_header.hasFocus():
            selection = self.selectionModel().selection()
            column_header.selectionModel().select(selection,
                                                  QItemSelectionModel.Columns | QItemSelectionModel.ClearAndSelect)

        if not index_header.hasFocus():
            selection = self.selectionModel().selection()
            index_header.selectionModel().select(selection,
                                                 QItemSelectionModel.Rows | QItemSelectionModel.ClearAndSelect)

    def print(self):
        print(self.data_model.df)

    def copy(self):
        """
        Copy the selected cells to clipboard in an Excel-pasteable format
        """

        # Get the bounds using the top left and bottom right selected cells
        indexes = self.selectionModel().selection().indexes()

        rows = [ix.row() for ix in indexes]
        cols = [ix.column() for ix in indexes]

        df = self.data_model.df.iloc[min(rows):max(rows) + 1, min(cols):max(cols) + 1]

        # If I try to use Pyperclip without starting new thread large values give access denied error
        def thread_function(df):
            df.to_clipboard(index=False, header=False)

        threading.Thread(target=thread_function, args=(df,)).start()

        # clipboard.setText(text)

    # def paste(self):
    #     # Set up clipboard object
    #     app = QtWidgets.QApplication.instance()
    #     if not app:
    #         app = QtWidgets.QApplication(sys.argv)
    #     clipboard = app.clipboard()
    #
    #     # TODO
    #     print(clipboard.text())

    def sizeHint(self):
        # Set width and height based on number of columns in model
        # Width
        width = 2 * self.frameWidth()  # Account for border & padding
        # width += self.verticalScrollBar().width()  # Dark theme has scrollbars always shown
        for i in range(self.data_model.columnCount()):
            width += self.columnWidth(i)

        # Height
        height = 2 * self.frameWidth()  # Account for border & padding
        # height += self.horizontalScrollBar().height()  # Dark theme has scrollbars always shown
        for i in range(self.data_model.rowCount()):
            height += self.rowHeight(i)

        return QSize(width, height)

    def set_data(self, df):
        m = self.data_model
        m.df = df
        m.layoutChanged.emit()

    def pos_adj(self, event, func):
        pos = self.orient(event)
        jk = self.over_header_edge(event)
        print(f'Pos: {pos}, iscol: {jk}')
        if jk is not None:
            func(self.orientation == Qt.Horizontal, jk, pos)
            return True
        else:
            self.header_being_resized = None

        # @self

    def auto_rc(self, a1, *pos):
        if a1:
            self.parent.auto_size_column(pos[0])
        else:
            self.parent.auto_size_row(pos[0])

    def resize_start(self, a1, *pos):
        self.header_being_resized = pos[0]
        self.resize_start_position = pos[1]
        if a1:
            self.initial_header_size = self.columnWidth(self.header_being_resized)
        else:
            self.initial_header_size = self.rowHeight(self.header_being_resized)

    def orient(self, event):
        if self.orientation == Qt.Horizontal:
            mouse_position = event.pos().x()
        else:  # self.orientation == Qt.Vertical
            mouse_position = event.pos().y()
        return mouse_position

    def data_view_ret(self):
        if self.orientation == Qt.Horizontal:


            return self.parent.columnHeader
        else:

            return self.parent.indexHeader

    def mouseMoveEvent(self, event: QtGui.QMouseEvent):  # todo extra jump, todo swap while drah, other not updaing

        mouse_position = self.orient(event)

        if self.header_being_resized is not None:

            size = self.initial_header_size + (mouse_position - self.resize_start_position)
            if size > 10:
                data = self.data_view_ret()

                if self.orientation == Qt.Horizontal:

                    self.setColumnWidth(self.header_being_resized, size)
                    data.setColumnWidth(self.header_being_resized, size)
                else:

                    self.setRowHeight(self.header_being_resized, size)
                    data.setRowHeight(self.header_being_resized, size)

                self.updateGeometry()
                data.updateGeometry()

        # Set the cursor shape
        if self.over_header_edge(event) is not None:

            if self.orientation == Qt.Horizontal:

                self.viewport().setCursor(QtGui.QCursor(Qt.SplitHCursor))
            else:

                self.viewport().setCursor(QtGui.QCursor(Qt.SplitVCursor))
        else:

            self.viewport().setCursor(QtGui.QCursor(Qt.ArrowCursor))

    def mouseReleaseEvent(self, event: QtGui.QMouseEvent):
        self.header_being_resized = None

    def mouseDoubleClickEvent(self, event: QtGui.QMouseEvent):  # todo font align, font center, add new types
        pos = event.pos()
        pos2 = (self.rowAt(pos.y()), self.columnAt(pos.x()))


        d2 = self.data_model.df.iloc[pos2]

        # Find which column or row edge the mouse was over and auto size it
        self.parent.set_popup(d2, True)

    def mousePressEvent(self, event: QtGui.QMouseEvent):
        # If mouse is on an edge, start the drag resize process

        self.pos_adj(event, self.resize_start)
        # Handle active drag resizing

    def over_header_edge(self, mouse_position, margin=3):
        # self.c
        # Return the index of the column this x position is on the right edge of
        x = mouse_position.pos().x()
        y = mouse_position.pos().y()
        # print(f'Pos: ({x}, {y}), col at marg: {self.columnAt(x + margin)}, row at: {self.rowAt(y + margin)}')
        if self.columnAt(x - margin) != self.columnAt(x + margin) and self.columnAt(x + margin) != 0:
            self.orientation = Qt.Horizontal

            return self.columnAt(x - margin)

        elif self.rowAt(y - margin) != self.rowAt(y + margin) and self.rowAt(y + margin) != 0:

            self.orientation = Qt.Vertical
            return self.rowAt(y - margin)

        else:
            return None


class HeaderModel(QtCore.QAbstractTableModel):
    """
    Model for HeaderView
    """

    def __init__(self, df, orientation, par, parent=None):
        super().__init__(parent)
        self.df = df
        self.orientation = orientation
        self.par = par

    def columnCount(self, parent=None):
        if self.orientation == Qt.Horizontal:
            return self.df.columns.shape[0]
        else:  # Vertical
            return self.df.index.nlevels

    def rowCount(self, parent=None):
        if self.orientation == Qt.Horizontal:
            return self.df.columns.nlevels
        elif self.orientation == Qt.Vertical:
            return self.df.index.shape[0]

    # def set_data(self, index: QModelIndex, value: typing.Any, role: int = ...) -> bool:
    def data(self, index, role=None):
        def handel_data(data):
            if isinstance(data, QDate):
                dx = data.toString(self.par.par.combo['Date Format'].currentText())
            else:
                dx = str(data)
            return dx

        row = index.row()
        col = index.column()

        if role == QtCore.Qt.DisplayRole or role == QtCore.Qt.ToolTipRole:

            if self.orientation == Qt.Horizontal:
                dy = self.df.columns
                i1 = col
                i2 = row
            elif self.orientation == Qt.Vertical:
                dy = self.df.index
                i1 = row
                i2 = col
            else:
                dy = None
                i1 = None
                i2 = None

            if dy is not None:
                if type(dy) == pd.MultiIndex:
                    da = dy.values[i1][i2]

                else:
                    da = dy.values[i1]
                if role == QtCore.Qt.DisplayRole or role == QtCore.Qt.ToolTipRole:
                    return handel_data(da)

                if role == QtCore.Qt.DecorationRole:
                    if isinstance(da, QDate):
                        return QtGui.QIcon('calendar.png')

    # The headers of this table will show the level names of the MultiIndex
    def headerData(self, section, orientation, role=None):
        if role in [QtCore.Qt.DisplayRole, QtCore.Qt.ToolTipRole]:

            if self.orientation == Qt.Horizontal and orientation == Qt.Vertical:
                if type(self.df.columns) == pd.MultiIndex:
                    return str(self.df.columns.names[section])
                else:
                    return str(self.df.columns.name)
            elif self.orientation == Qt.Vertical and orientation == Qt.Horizontal:
                if type(self.df.index) == pd.MultiIndex:
                    return str(self.df.index.names[section])
                else:
                    return str(self.df.index.name)
            else:
                return None  # These cells should be hidden anyways


class HeaderView(DataTableView):
    """
    Displays the DataFrame index or columns depending on orientation
    """

    def __init__(self, parent: DataFrameViewer, df, orientation):
        super().__init__(df, parent, orientation)

    def _init_0(self, df):
        # Setup

        self.table = self.parent.dataView
        self.data_model = HeaderModel(df, self.orientation, self.parent)
        self.setModel(self.data_model)

        # Handled by self.eventFilter()

        # self.viewport().setMouseTracking(True)

        # Settings
        self.setSizePolicy(QSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum))
        self.setWordWrap(False)
        self.setFont(QtGui.QFont("Times", weight=QtGui.QFont.Bold))
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollMode(QtWidgets.QAbstractItemView.ScrollPerPixel)
        self.setVerticalScrollMode(QtWidgets.QAbstractItemView.ScrollPerPixel)

        # Link selection to DataTable
        self.selectionModel().selectionChanged.connect(self.on_selection_changed)
        self.set_spans()
        self.init_size()

        # Orientation specific settings
        if self.orientation == Qt.Horizontal:
            self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)  # Scrollbar is replaced in DataFrameViewer
            self.horizontalHeader().hide()
            self.verticalHeader().setDisabled(True)
            self.verticalHeader().setHighlightSections(False)  # Selection lags a lot without this

        else:
            self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            self.verticalHeader().hide()
            self.horizontalHeader().setDisabled(True)

            self.horizontalHeader().setHighlightSections(False)  # Selection lags a lot without this

        # Set initial size
        self.resize(self.sizeHint())

    def data_view_ret(self):
        return self.parent.dataView

    def over_header_edge(self, mouse_position, margin=3):

        # Return the index of the column this x position is on the right edge of
        # print('user 2 edge')
        x = self.orient(mouse_position)
        # print(x=)
        if self.orientation == Qt.Horizontal:
            fun = self.columnAt
            # Return the index of the row this y position is on the top edge of
        else:
            fun = self.rowAt
        if fun(x - margin) != fun(x + margin) and fun(x + margin) != 0:
            # We're at the left edge of the first column
            # print(f'user 2 edge func = {fun.__name__}')
            return fun(x - margin)
        else:
            # print(f'user 2 no fun')
            return None

    # Header
    def on_selection_changed(self):
        """
        Runs when cells are selected in the Header. This selects columns in the data table when the header is clicked,
        and then calls select_above()
        """
        # Check focus so we don't get recursive loop, since headers trigger selection of data cells and vice versa
        if self.hasFocus():
            data_view = self.parent.dataView

            # Set selection mode so selecting one row or column at a time adds to selection each time
            if self.orientation == Qt.Horizontal:  # This case is for the horizontal header
                # Get the header's selected columns
                selection = self.selectionModel().selection()

                # Removes the higher levels so that only the lowest level of the header affects the data table selection
                last_row_ix = self.df.columns.nlevels - 1
                last_col_ix = self.data_model.columnCount() - 1
                higher_levels = QtCore.QItemSelection(self.data_model.index(0, 0),
                                                      self.data_model.index(last_row_ix - 1, last_col_ix))
                selection.merge(higher_levels, QtCore.QItemSelectionModel.Deselect)

                # Select the cells in the data view
                data_view.selectionModel().select(selection,
                                                  QtCore.QItemSelectionModel.Columns | QtCore.QItemSelectionModel.ClearAndSelect)
            if self.orientation == Qt.Vertical:
                selection = self.selectionModel().selection()

                last_row_ix = self.data_model.rowCount() - 1
                last_col_ix = self.df.index.nlevels - 1
                higher_levels = QtCore.QItemSelection(self.data_model.index(0, 0),
                                                      self.data_model.index(last_row_ix, last_col_ix - 1))
                selection.merge(higher_levels, QtCore.QItemSelectionModel.Deselect)

                data_view.selectionModel().select(selection,
                                                 QtCore.QItemSelectionModel.Rows | QtCore.QItemSelectionModel.ClearAndSelect)

        self.select_above()

    # Take the current set of selected cells and make it so that any spanning cell above a selected cell is selected too
    # This should happen after every selection change
    def select_above(self):
        if self.orientation == Qt.Horizontal:
            if self.df.columns.nlevels == 1:
                return
        else:
            if self.df.index.nlevels == 1:
                return

        for ix in self.selectedIndexes():
            if self.orientation == Qt.Horizontal:
                # Loop over the rows above this one
                for row in range(ix.row()):
                    ix2 = self.data_model.index(row, ix.column())
                    self.setSelection(self.visualRect(ix2), QtCore.QItemSelectionModel.Select)
            else:
                # Loop over the columns left of this one
                for col in range(ix.column()):
                    ix2 = self.data_model.index(ix.row(), col)
                    self.setSelection(self.visualRect(ix2), QtCore.QItemSelectionModel.Select)

    # Fits columns to contents but with a minimum width and added padding
    def init_size(self):
        padding = 20

        if self.orientation == Qt.Horizontal:
            min_size = 100

            self.resizeColumnsToContents()

            for col in range(self.data_model.columnCount()):
                width = self.columnWidth(col)
                if width + padding < min_size:
                    new_width = min_size
                else:
                    new_width = width + padding

                self.setColumnWidth(col, new_width)
                self.table.setColumnWidth(col, new_width)
        else:
            max_size = 1000
            self.resizeColumnsToContents()
            for col in range(self.data_model.columnCount()):
                width = self.columnWidth(col)
                self.setColumnWidth(col, width + padding)

    # This sets spans to group together adjacent cells with the same values
    def set_spans(self):
        df = self.data_model.df

        # Find spans for horizontal HeaderView
        if self.orientation == Qt.Horizontal:

            # Find how many levels the MultiIndex has
            if type(df.columns) == pd.MultiIndex:
                num = len(df.columns[0])
            else:
                num = 1

            for level in range(num):  # Iterates over the levels
                # Find how many segments the MultiIndex has
                if type(df.columns) == pd.MultiIndex:
                    arr = [df.columns[i][level] for i in range(len(df.columns))]
                else:
                    arr = df.columns

                # Holds the starting index of a range of equal values.
                # None means it is not currently in a range of equal values.
                match_start = None

                for col in range(1, len(arr)):  # Iterates over cells in row
                    # Check if cell matches cell to its left
                    if arr[col] == arr[col - 1]:
                        if match_start is None:
                            match_start = col - 1
                        # If this is the last cell, need to end it
                        if col == len(arr) - 1:
                            match_end = col
                            span_size = match_end - match_start + 1
                            self.setSpan(level, match_start, 1, span_size)
                    else:
                        if match_start is not None:
                            match_end = col - 1
                            span_size = match_end - match_start + 1
                            self.setSpan(level, match_start, 1, span_size)
                            match_start = None

        # Find spans for vertical HeaderView
        else:
            # Find how many levels the MultiIndex has
            if type(df.index) == pd.MultiIndex:
                num = len(df.index[0])
            else:
                num = 1

            for level in range(num):  # Iterates over the levels

                # Find how many segments the MultiIndex has
                if type(df.index) == pd.MultiIndex:
                    arr = [df.index[i][level] for i in range(len(df.index))]
                else:
                    arr = df.index

                # Holds the starting index of a range of equal values.
                # None means it is not currently in a range of equal values.
                match_start = None

                for row in range(1, len(arr)):  # Iterates over cells in column

                    # Check if cell matches cell above
                    if arr[row] == arr[row - 1]:
                        if match_start is None:
                            match_start = row - 1
                        # If this is the last cell, need to end it
                        if row == len(arr) - 1:
                            match_end = row
                            span_size = match_end - match_start + 1
                            self.setSpan(match_start, level, span_size, 1)
                    else:
                        if match_start is not None:
                            match_end = row - 1
                            span_size = match_end - match_start + 1
                            self.setSpan(match_start, level, span_size, 1)
                            match_start = None

    # Return the size of the header needed to match the corresponding DataTableView
    def sizeHint(self):

        # Horizontal HeaderView
        if self.orientation == Qt.Horizontal:
            # Width of DataTableView
            width = self.table.sizeHint().width() + self.verticalHeader().width()
            # Height
            height = 2 * self.frameWidth()  # Account for border & padding
            for i in range(self.data_model.rowCount()):
                height += self.rowHeight(i)

        # Vertical HeaderView
        else:
            # Height of DataTableView
            height = self.table.sizeHint().height() + self.horizontalHeader().height()
            # Width
            width = 2 * self.frameWidth()  # Account for border & padding
            for i in range(self.data_model.columnCount()):
                width += self.columnWidth(i)
        return QSize(width, height)

    # This is needed because otherwise when the horizontal header is a single row it will add whitespace to be bigger
    def minimumSizeHint(self):
        if self.orientation == Qt.Horizontal:
            return QSize(0, self.sizeHint().height())
        else:
            return QSize(self.sizeHint().width(), 0)

    def mouseDoubleClickEvent(self, event: QtGui.QMouseEvent):

        # Find which column or row edge the mouse was over and auto size it
        if self.pos_adj(event, self.auto_rc):
            return True



# This is a fixed size widget with a size that tracks some other widget
class TrackingSpacer(QtWidgets.QFrame):
    def __init__(self, ref_x=None, ref_y=None):
        super().__init__()
        self.ref_x = ref_x
        self.ref_y = ref_y

    def minimumSizeHint(self):
        width = 0
        height = 0
        if self.ref_x:
            width = self.ref_x.width()
        if self.ref_y:
            height = self.ref_y.height()

        return QtCore.QSize(width, height)
