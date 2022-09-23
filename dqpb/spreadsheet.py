"""
Spreadsheet data input and output.

"""

import sys
import secrets
import logging
import matplotlib.pyplot as plt
import matplotlib.lines


logger = logging.getLogger("dqpb.spreadsheet")


class SpreadSheetPrinter:
    """
    Class for printing results to spreadsheet in one hit. Add items (print
    frames and figures) to stack as you go then call flush_stack at the end to
    print everything.
    """

    def __init__(self, worksheet, rng, xl_fig_height=20, embolden=True,
                 apply_number_formats=True, clear_cells=True, font='Arial',
                 apply_font=True, apply_cell_color=False, cell_color=None):
        self.rng = rng
        self.worksheet = worksheet
        self.row = self.rng.row
        self.column = self.rng.column
        self.xl_fig_height = xl_fig_height # height in number of cells
        self.embolden = embolden
        self.apply_number_formats = apply_number_formats
        self.clear_cells = clear_cells
        self.font = font
        self.apply_font = apply_font
        self.apply_cell_color=apply_cell_color
        self.cell_color = cell_color

        self.cell_height = None  # computed at print time
        self.stack = []
        self.pictures = []

    def flush_stack(self):
        """
        Print items in stack to spreadsheet.
        """
        current_row = self.row
        self.get_cell_size()
        # set printing order according to zorder attribute
        sorted_stack = sorted(self.stack, key=lambda item: item.yorder)
        self.worksheet.book.app.screen_updating = False
        # print items one by one
        for item in sorted_stack:
            if isinstance(item, PrintFrame):
                item.print_to_sheet(self.worksheet, current_row, self.column,
                            apply_number_formats=self.apply_number_formats,
                            embolden=self.embolden, clear=self.clear_cells,
                            font=self.font, apply_font=self.apply_font,
                            apply_cell_color=self.apply_cell_color,
                            cell_color=self.cell_color)
                current_row += item.n_rows
            else:
                # if not print frame must be mpl figure
                pic, n_rows = self.print_fig(item, current_row, self.column)
                self.pictures.append(pic)
                current_row += (n_rows +1)
        self.worksheet.book.app.screen_updating = True
        self.stack = []

    def stack_frame(self, frame, yorder=1):
        frame.yorder = yorder
        if not isinstance(frame, PrintFrame):
            raise ValueError("frame must be an instance of PrintFrame")
        self.stack.append(frame)

    def stack_figure(self, fig, yorder=1):
        if not isinstance(fig, plt.Figure):
            raise ValueError("fig must be an instance of plt.Figure")
        fig.yorder = yorder
        self.stack.append(fig)

    def get_cell_size(self):
        # Get spreadsheet cell row height and width. xlwings seems to return
        # None if row height is non-uniform so in this case use average over
        # sheet instead.
        self.cell_height = self.worksheet.cells.row_height
        if self.cell_height is None:
            self.cell_height = (self.worksheet.cells.height
                                / self.worksheet.cells.rows.count)

    def get_picture_dims(self, fig):
        """
        Re-scale figure size to given row height while preserving scale.
        """
        width, height = fig.get_size_inches()
        aspect_ratio = width / height
        n_rows = self.xl_fig_height
        xl_height = n_rows * self.cell_height
        xl_width = aspect_ratio * xl_height
        return xl_width, xl_height, n_rows

    def print_fig(self, fig, row, col):
        rng = self.worksheet.range((row, col))
        width, height, n_rows = self.get_picture_dims(fig)
        # Create random name for picture to avoid possibility of
        # ShapeAlreadyExists error being raised.
        name = "Picture " + secrets.token_hex(5)
        picture_opts = {'top': rng.top,
                        'left': rng.left,
                        'width': width,
                        'height': height,
                        'name': name,
                        'update': False,
                        'format': 'png'}
        # pic = self.worksheet.pictures.add(fig, **picture_opts)
        pic = self.worksheet.pictures.add(fig, **picture_opts)
        return pic, n_rows


class PrintFrame:
    """
    This represents a region of cells with set number of columns that will
    be used for printing related results. E.g. multiple tables of results that
    will be printed together.
    """
    line_sep = "-"
    sep_width = 34

    def __init__(self, n_col=2, yorder=1):
        self.yorder = yorder
        self.n_col = n_col
        self.items = []
        self.item_formats = []
        self.header_rows = []
        self.current_row = 0

    @property
    def n_rows(self):
        return len(self.items)

    def add_table(self, data, formats=None, title=None,
                   format_first_col=False, add_line_sep=False):
        """
        Add table of results to print stack.
        data : list of lists
            Data to print with each list element of data a different column.
        formats : list
            List of xl format codes (either one per column or one per row
            following settings).
        skip_first_rc : bool
            Format first row or column (depending on formats_by_row) or skip
            (e.g. if it contains parameter keys as strings)
        """
        if not isinstance(data, list) or not isinstance(data[0], list):
            raise ValueError('data mus be a list of lists')
        if not all(len(x) == len(data[0]) for x in data):
            raise ValueError('elements must all be of equal length')
        if formats is not None:
            if not isinstance(formats, list) or not isinstance(formats[0], list):
                # raise ValueError('data mus be a list of lists')
                # try converting to list of lists
                formats = [formats]
            if len(formats[0]) != len(data[0]):
                raise ValueError('number of elements in data and formats inconsistent')
            # check all format rows equal length and same as data

        data_array = []
        format_array = []
        n_row = len(data[0])
        data_col = len(data)
        if formats is not None:
            format_col = len(formats)
        none_col = [None] * n_row

        # Expand number of columns to same as print frame by appending Nones
        if data_col > self.n_col:
            raise ValueError('too many columns in data for this print frame')
        else:
            data_array = data
            if data_col < self.n_col:
                data_array += [none_col] * (self.n_col - data_col)

        # Check shape of formats
        # Should be one of:
        # [[a, b, c]] of equal length as each results column
        # or [[a,b,c], [d,e,f], [g,h,i]] with one element for each column

        if formats is not None:
            format_array = formats
            broadcast_allowed = True if format_col == 1 else False
            # insert column of nones
            if not format_first_col and format_col != data_col \
                    and data_col > 1:
                format_array.insert(0, none_col)
            # If format array now has same sahpe as data then done.
            # If format array now has more columns than data there is an error.
            # If format array still has less than data, then need try
            # broadcasting
            if len(format_array) == len(data):
                pass
            elif len(format_array) > len(data):
                raise ValueError
            else:
                if broadcast_allowed:
                    format_array += formats * (data_col - 1)
                else:
                    raise ValueError
        else:
            format_array = [none_col] * self.n_col

        # Pad with None to fill columns
        if len(format_array) != self.n_col:
            format_array += [none_col] * (self.n_col - len(format_array))

        # Add title to print frame
        if title:
            self.items += [[title, *[None] * (self.n_col - 1)]]
            self.header_rows.append(self.current_row)
            self.item_formats += [[None] * self.n_col]
            self.current_row += 1

            if add_line_sep:
                self.items += [[self.line_sep * self.sep_width,
                                *[None] * (self.n_col - 1)]]
                self.item_formats += [[None] * self.n_col]
                self.current_row += 1

        # Add each row of data to frame
        for row in zip(*data_array):
            self.items.append(list(row))
            self.current_row += 1

        # Add each row of formats to frame
        for row in zip(*format_array):
            self.item_formats.append(list(row))

        # Add blank row at end
        self.add_blank_row()

    def print_to_sheet(self, worksheet, row, col, embolden=True, underline=True,
                       apply_number_formats=True, clear=False,
                       apply_font=True, font='Calibri', apply_cell_color=False,
                       cell_color=()):
        if len(self.items) == 0:
            return

        n_row = len(self.items)
        # print values
        rng = worksheet.range((row, col),
                              (row + n_row - 1, col + self.n_col - 1)
                              )
        if clear:
            rng.clear()
            #TODO: what to do here?
            # rng.font.bold = False
        rng.value = self.items

        # # apply bold formats
        # make_bold = self.header_rows if apply_bold_formats else []
        if apply_number_formats or embolden:
            for i, row in enumerate(rng.rows):
                for j, col in enumerate(row.columns):
                    if apply_number_formats:
                        col.number_format = self.item_formats[i][j]
                    if apply_cell_color:
                        col.color = cell_color
                    if apply_font and (font not in (None, 'none')):
                        col.font.name = font
                    if embolden and j == 0 and (i in self.header_rows):
                        col.font.bold = True
                    if underline and j == 0 and (i in self.header_rows):
                        if sys.platform == 'darwin':
                            from appscript import k
                            col.api.font_object.underline.set(k.underline_style_single)
                        else:
                            # Fix this!
                            col.api.Font.Underline = True

    def add_blank_row(self):
        self.items.append([*[None] * self.n_col])
        self.item_formats.append([*[None] * self.n_col])
        self.current_row += 1


def print_plot_data_to_sheet(d, pr_range, header='Regression-fit plot data',
                             start_col=1):
    """
    Print dict containing plot data as transposed list of lists to worksheet.
    """
    # Length of longest list in d
    max_key = max(d, key=lambda x: len(set(d[x])))

    n = len(d[max_key])

    # Create empty list of equal length lists, since xlwings doesn't transpose
    # lists of lists with non uniform length.
    p = [[None] * n for x in range(len(d))]
    i = 0

    for i, (k, v) in enumerate(d.items()):
        for j in range(len(v)):
            p[i][j] = v[j]
        p[i].insert(0, k)

    top_range = pr_range
    top_range.value = header
    bottom_range = top_range.offset(1, 0)
    bottom_range.options(transpose=True).value = p
    next_col = i + 3 if i != 0 else 0

    return next_col


def add_new_sheet(ws_before, base_name='Plot data'):
    """
    Add new sheet to Excel workbook.
    """
    index = ""
    wb = ws_before.book
    while True:
        new_sheet_name = str(base_name) + index
        try:
            ws_before.book.sheets.add(new_sheet_name, after=ws_before)
            break
        except ValueError:
            if index:
                # append 1 to number in brackets
                index = '(' + str(int(index[1:-1]) + 1) + ')'
            else:
                index = '(1)'
            pass

    return wb.sheets[new_sheet_name]


def print_plot_data(ax, sheet_name='Plot data', header='Isochron plot data',
                    ws_main=None, ws=None, next_col=1, labels=None,
                    max_length=10_000):
    """
    Print plot data to new sheet in Excel. Requires labels to be added to each
    matplotlib element as plots are constructed.

    Notes
    -----
    Assumes data point ellipses are plotted in same order as labels.

    """
    if ws_main is None and ws is None:
        raise ValueError("")

    if ws is None:  # create new sheet
        ws = add_new_sheet(ws_main, base_name=sheet_name)
    else:
        # if not isinstance(ws, x)
        pass

    n_data_ellipses = sum([p.get_label() == 'data ellipse' for p in ax.patches])

    if labels is not None:
        if n_data_ellipses > 0:
            if n_data_ellipses!= len(labels):
                raise ValueError('number of labels not equal to number of data '
                             'points')

    # Create dictionary to store plot data in header: list pairs.
    d = dict()

    # axis limits
    d['x-limits'] = ax.get_xlim()
    d['y-limits'] = ax.get_ylim()

    # Each annotation constitutes a separate child, so need to add each one to
    # a list then add to dict.
    concordia_label_txt = []
    concordia_label_x = []
    concordia_label_y = []

    # ellipses
    for i, e in enumerate(ax.patches):
        label = ax.patches[i].get_label()
        if label == 'data ellipse':
            if labels is None:
                j = i + 1
            else:
                j = labels[i]
            d[f'ellipse {j}, x'] = ax.transData.inverted().transform(e.get_verts())[:, 0]
            d[f'ellipse {j}, y'] = ax.transData.inverted().transform(e.get_verts())[:, 1]
        elif label.startswith('age ellipse'):
            d[f'{label}, x'] = ax.transData.inverted().transform(e.get_verts())[:, 0]
            d[f'{label}, y'] = ax.transData.inverted().transform(e.get_verts())[:, 1]

        elif label == 'intercept ellipse':
            d['intercept ellipse, x'] = ax.transData.inverted().transform(e.get_verts())[:, 0]
            d['intercept ellipse, y'] = ax.transData.inverted().transform(e.get_verts())[:, 1]

    j = 0
    k = 0

    for ch in ax.get_children():
        if ch.get_label() == 'regression line':
            d["regression line, x"] = ch.get_data()[0]
            d["regression line, y"] = ch.get_data()[1]
        elif ch.get_label() == 'regression envelope line':
            if isinstance(ch, matplotlib.lines.Line2D):
                # use envelope lines (ignore fill)
                d[f"regression env {j+1}, x"] = ch.get_data()[0]
                d[f"regression env {j+1}, y"] = ch.get_data()[1]
                j += 1
        elif ch.get_label() == 'concordia line':
            d["concordia line, x"] = ch.get_data()[0]
            d["concordia line, y"] = ch.get_data()[1]
        elif ch.get_label() == 'concordia envelope line':
            if isinstance(ch, matplotlib.lines.Line2D):
                # use envelope lines (ignore fill)
                d[f"concordia env {k+1}, x"] = ch.get_data()[0]
                d[f"concordia env {k+1}, y"] = ch.get_data()[1]
                k += 1
        elif ch.get_label() == "concordia marker":
            d["concordia marker, x"] = ch.get_data()[0]
            d["concordia marker, y"] = ch.get_data()[1]
        elif ch.get_label() == 'concordia label':
            concordia_label_txt.append(ch.get_text())
            concordia_label_x.append(ch.xy[0])
            concordia_label_y.append(ch.xy[1])
        elif ch.get_label() == 'intercept markers':
            d["intercept marker, x"] = ch.get_data()[0]
            d["intercept marker, y"] = ch.get_data()[1]

    if concordia_label_txt:
        d['concordia label'] = concordia_label_txt
        d['concordia label, x'] = concordia_label_x
        d['concordia label, y'] = concordia_label_y

    next_col = print_plot_data_to_sheet(d, ws.range((1, next_col)),
                                        header=header)
    return ws, next_col
