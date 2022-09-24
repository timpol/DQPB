"""
Miscellaneous functions

"""

import os
import sys
import math
import logging
import numpy as np

from PyQt5.QtGui import QFontDatabase


logger = logging.getLogger("dqpb.util")


def fixedFont():
    font = QFontDatabase.systemFont(QFontDatabase.FixedFont)
    if sys.platform == "darwin":
        font.setPointSize(font.pointSize() + 2)
    return font


def save_plot_to_disk(fig, dir, fname='Plot', file_ext='', overwrite=False):
    """
    """
    if dir == '':
        dir = os.path.expanduser("~/Desktop/DQPB/Figures/")
    path = get_save_path(dir, fname, file_ext, overwrite=overwrite)
    # fig.savefig(path, bbox_inches='tight')
    fig.savefig(path, dpi=fig.get_dpi())
    return path


def get_save_path(dirname, fname, file_ext, overwrite=False):
    """ """
    try:
        os.makedirs(dirname)
    except FileExistsError:
        pass   # directory already exists

    if overwrite:
        path = os.path.join(dirname, fname)
    else:
        index = ""
        file_exists = True
        while file_exists is True:
            path = os.path.join(dirname, fname + index + file_ext)
            if os.path.isfile(path):
                if index:
                    # append 1 to number in brackets:
                    index = '(' + str(int(index[1:-1]) + 1) + ')'
                else:
                    index = '(1)'
            else:
                file_exists = False

    return path


def vep_format(v, e, plims=(-3,5)):
    """
    Use order of magnitude of error to determine number of decimal places to
    show.
    """

    if any(np.isnan((v,e))):
        return "#.00", "#.00"

    s = -1 if v < 0 else 1  # get sign for later
    v = v * s  # Convert to positive value
    e = abs(e)  # Error should always be positive, but just in case.

    # Find number of decimal places required from order of magnitude. E.g.
    # >0 -> 0 decimal places for value and error
    # 0 -> 1
    # -1 -> 2
    # -2 -> 3

    p = math.floor(math.log10(e))
    # If number is within power limits, do not use scientific notation
    if 10 ** plims[0] < v * s < 10 ** plims[1]:
        # find number of decimal places
        if p > 1:
            d = 0
        else:
            d = -1 * p + 1
        fs = print_format_str(d)
        # Use same format string for value and error
        return fs, fs
    else:
        pv = math.floor(math.log10(v))
        q = pv - p
        q = q + 1 if q > 0 else 1
        fse = print_format_str(1, sci=True)
        fsv = print_format_str(q, sci=True)
        return fsv, fse


def single_val_format(v, sf=4, plims=(-3,5)):
    """
    Parameters
    -----------
    sf : int
        Number of significant figures to display (only applies to decimal
        component)
    """

    sf = int(sf)
    if sf < 0:
        raise ValueError("can't have a negative or 0 number of significant figures")
    s = -1 if v < 0 else 1
    v = v * s

    if v == 0.:
        return print_format_str(sf)

    p = math.floor(math.log10(v))

    if 10 ** plims[0] < s * v < 10 ** plims[1]:
        if p >= (sf + 1):
            d = 0
        else:
            d = sf - p - 1
        return print_format_str(d)

    else:
        return print_format_str(sf-1 if sf > 1 else 1, sci=True)


def print_format_str(d_places, sci=False):
    """
    """
    d_places = int(d_places)

    if not sci:
        bs = "#,##0"
        if d_places > 0:
            fs = bs + '.' + d_places * '0'
        else:
            fs = bs
    else:
        bs1 = "0.0"
        bs2 = "E+00"
        if d_places > 0:
            fs = bs1 + (d_places - 1) * "0" + bs2
        else:
            fs = bs1 + bs2

    return fs


def string_to_list(x, dtype='float'):
    """
    Convert string representing a list (e.g. from line entry) to python
    list.
    """
    x = x.strip("( [ ] )").split(",")
    if dtype == 'float':
        return [float(e) for e in x]
    elif dtype == 'int':
        return [float(e) for e in x]
    raise ValueError


def guess_type(x):
    """
    Guess settings type from default value. Used for converting strings
    from QLineEdits to numeric values.
    """
    # Check if bool.
    if str(x).strip().lower() in ('true', 'false') or isinstance(x, bool):
        return bool

    # Check if numeric.
    try:
        y = float(x)
    except ValueError:
        pass
    else:
        if not any(c in x for c in ('.', 'e', 'E')):
            return int
        else:
            return float
    # Otherwise, probably string.
    return str
