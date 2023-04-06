"""
Main gui application code.

"""

import os
import time
import copy
import logging
import warnings
import numpy as np
import xlwings as xw
import matplotlib as mpl

from dqpb import resourceAbsolutePath, version, debug
if not debug:
    mpl.use('Agg')
    
import matplotlib.pyplot as plt
import matplotlib.colors
import matplotlib.lines
import matplotlib.font_manager


from PyQt5.QtCore import (QByteArray, QLocale, QPoint, QSize, Qt, QThread,
                          pyqtSignal, QObject, QTimer, QSettings, pyqtSlot)
from PyQt5.QtGui import (QIcon, QIntValidator, QDoubleValidator, QColor,
                         QTextCursor)
from PyQt5.QtWidgets import (QAction, QApplication, QDialog, QMainWindow,
                             QPlainTextEdit, QLineEdit, QRadioButton,
                             QComboBox, QFileDialog, QButtonGroup,
                             QErrorMessage, QMessageBox, QPushButton,
                             QFontDialog, QColorDialog)
from PyQt5.uic import loadUi

from pysoplot import misc

from dqpb import config
from dqpb import setup_calc
from dqpb import util
from dqpb.combo import (TASKS, REGRESSION_FITS, WAV_FITS, SHORT_TASK_NAMES,
                        SHORT_DATA_TYPES, SHORT_FITS, MPL_V_ALIGNMENTS,
                        MPL_H_ALIGNMENTS, MPL_HISTTYPES, AGE_PREFIXES,
                        FONT_SIZES, DP_ERROR_WARNING_THRESHOLD,
                        MPL_TICK_DIRECTIONS)

from dqpb.loggers import ConsoleHandler, setUpLoggers


logger = logging.getLogger("dqpb.gui")


GUI_SETTINGS = config.QConfig().read()

# Needed to ensure settings dir is created before log file is written for
# first time or after deletion.
GUI_SETTINGS.settings.sync()


# Fix scaling issues on Windows high res?
# if hasattr(Qt, 'AA_EnableHighDpiScaling'):
#     QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
#
# if hasattr(Qt, 'AA_UseHighDpiPixmaps'):
#     QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)


# Activity ratio fields.
U238_ENTRIES = ['A48Entry', 'A08Entry', 'A68Entry']
U238_ERR = ['A48ErrEntry', 'A08ErrEntry', 'A68ErrEntry']
U238_COMBOS = ['A48Combo', 'A08Combo', 'A68Combo']
U238_LABELS = ['A48Label', 'A08Label', 'A68Label']
U235_ENTRIES = ['A15Entry']
U235_ERR = ['A15ErrEntry']
U235_COMBOS = ['A15Combo']
U235_LABELS = ['A15Label']


# =============================================================================
# Control flow exceptions
# =============================================================================

class InputError(Exception):
    """ 
    Raise when a calculation can't proceed due to a problem with user inputs. 
    Usually this means that focus should return to the main window.
    """
    pass


class XlError(Exception):
    """ 
    Raised when there is a problem connecting to an Excel workbook or reading
    data from Excel.
    """
    pass


# =============================================================================
# Main application window
# =============================================================================
class MainWindow(QMainWindow):

    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.dp_workbook = None
        self.dp_worksheet = None
        self.dp_address = None

        self.out_workbook = None
        self.out_worksheet = None
        self.out_address = None

        self.n = None
        self.dp = None
        self.dp_labels = None
        self.cov = None
        self.dp_iso86 = None
        self.dp_iso57 = None
        self.DThU_const = None
        self.ThUmin_data = None
        self.norm_isotope = None
        self.Pb76 = None
        self.Pb76_1s = None
        
        # Data returned from the calc thread.
        self.retval = None

        self.console_handler = ConsoleHandler()

        uiPath = os.path.join("uis", "main.ui")
        loadUi(resourceAbsolutePath(uiPath), baseinstance=self, package="DQPB")

        self.setWindowTitle("DQPB")
        self.iconPath = os.path.join("icons", "DQPB.png")
        self.setWindowIcon(QIcon(resourceAbsolutePath(self.iconPath)))

        # =====================================================================
        # Set up dialogs
        # =====================================================================
        # windows
        self.aboutDialog = AboutDialog(parent=self)
        self.selectDpWindow = RangeSelectDialog(title='Data Point Selection',
                                                parent=self, text="Select data points in spreadsheet file:")
        self.outputAddressDialog = RangeSelectDialog(title='Output Location',
                                                     parent=self, text="Where do you want to output results?",
                                                     button_txt='Set location')
        self.selectLabelsWindow = RangeSelectDialog(title="Label Selection",
                                                    parent=self, text="Select data point labels:", as_string=True)
        self.covMatDialog = RangeSelectDialog(parent=self, title="Covariance Matrix",
                                              text='Select n x n covariance matrix data:')
        self.ThUminDialog = ThUminSelectDialog(self)

        # dialogs
        self.logWindow = LogDialog(self)
        self.progressDialog = ProgressDialog(self)
        self.prefsWindow = PreferencesWindow(self)
        self.fcDialog = FcDataDialog(self)
        self.axisLimsDialog = AxisLimsDialog(self)
        self.axisLabelsDialog = AxisLabelsDialog(self)
        self.comPb76Dialog = CommonPb76Dialog(self)
        self.plotFormatWindow = PlotFormatWindow(self)
        self.plotSettingsWindow = PlotSettingsWindow(self)
        self.taskErrorDialog = TaskErrorDialog()

        #======================================================================
        # Register a handler to display messages log
        # =====================================================================
        # Warnings logger:
        # https://stackoverflow.com/questions/38531786/capturewarnings-set-to-true-doesnt-capture-warnings
        logging.captureWarnings(True)
        warnings_logger = logging.getLogger("py.warnings")

        logger = logging.getLogger("dqpb")
        logger.addHandler(self.console_handler)
        warnings_logger.addHandler(self.console_handler)
        self.console_handler.logUpdated.connect(self.logWindow.updateLogger)

        # =====================================================================
        # Set up file menu
        # =====================================================================
        openAboutDialog = QAction("About DQPB", self, triggered=self.openAboutDialog)
        quitApp = QAction("&Quit", self, triggered=self.close)
        # openPrefs = QAction("&Preferences", self, triggered=self.showPrefsWindow)
        openLog = QAction("&Log Console...", self, triggered=self.showLogWindow)
        turnOnScreenUpdating = QAction("&Unfreeze Excel screen updating...", self,
                            triggered=self.screenUpdating)
        openProgress = QAction("&Progress Window...", self,
                            triggered=self.progressDialog.show)
        openPlotFormat = QAction("&Plot format settings...", self,
                            triggered=lambda: self.plotFormatWindow.show())
        openPlotOptions = QAction("Type-specific plot settings...", self,
                             triggered=lambda: self.plotSettingsWindow.show())
        openPrefs = QAction("&Preferences", self, triggered=self.showPrefsWindow)

        # Add keyboard shortcuts
        openPrefs.setShortcut("Ctrl+P")
        openPlotFormat.setShortcut("Ctrl+F")
        openLog.setShortcut("Ctrl+L")
        openProgress.setShortcut("Ctrl+B")
        openPlotOptions.setShortcut("Ctrl+T")

        # Compose the menu.
        # self.menuBar = self.menuBar()
        self.fileMenu = self.menuBar.addMenu('&File')
        self.fileMenu.addAction(turnOnScreenUpdating)
        self.fileMenu.addSeparator()
        self.fileMenu.addAction(quitApp)

        self.optionsMenu = self.menuBar.addMenu('&Options')
        self.optionsMenu.addAction(openPrefs)
        self.optionsMenu.addAction(openPlotFormat)
        self.optionsMenu.addAction(openPlotOptions)

        self.winMenu = self.menuBar.addMenu('&Window')
        self.winMenu.addAction(openLog)
        self.winMenu.addAction(openProgress)

        self.helpMenu = self.menuBar.addMenu('&Help')
        self.helpMenu.addAction(openAboutDialog)

        # =====================================================================
        # Set up callback functions
        # =====================================================================
        # --- Do this before adding callbacks. DO NOT MODIFY! ----
        self.taskCombo.addItems(list(TASKS.keys()))
        # ---------------------------------------

        # Add callback functions
        self.taskCombo.currentIndexChanged.connect(self.taskChange)
        self.dataTypeCombo.currentIndexChanged.connect(self.dataTypeChange)
        self.covOpt.clicked.connect(self.covChange)
        self.initialEqOpt.clicked.connect(self.initialEqChange)
        self.eqGuessOpt.clicked.connect(self.eqGuessChange)
        self.A08Combo.currentIndexChanged.connect(self.A08TypeChange)
        self.A15Combo.currentIndexChanged.connect(self.A15TypeChange)

        # =====================================================================
        # Set up GUI elements
        # =====================================================================
        # Change radiobutton labels to unicode
        self.err1sOpt.setText("1 \u03C3")
        self.err2sOpt.setText("2 \u03C3")

        # Create radiobutton group
        self.sigmaGroup = QButtonGroup()
        self.sigmaGroup.addButton(self.err1sOpt, 1)
        self.sigmaGroup.addButton(self.err2sOpt, 2)

        # Create age uncertainty radiobutton group
        self.uncertGroup = QButtonGroup()
        self.uncertGroup.addButton(self.mcUncertOpt, 1)
        self.uncertGroup.addButton(self.anUncertOpt, 2)

        # Populate error type combo boxes
        self.errTypeCombo.addItems(("abs.", "percent"))
        self.normPbCombo.addItems(["204Pb", "208Pb"])

        # Populate isochron activity ratio combo boxes:
        for ratio in ("A48", "A08"):
            comboBox = getattr(self, f"{ratio}Combo")
            comboBox.addItems(["initial", "present-day"])
        for ratio in ("A15", "A68"):
            comboBox = getattr(self, f"{ratio}Combo")
            comboBox.addItems(["initial"])

        # Add commands to main buttons
        self.closeButton.pressed.connect(self.close)
        self.selectButton.clicked.connect(self.selectDp)
        self.okButton.clicked.connect(self.okClick)
        # self.resetButton.clicked.connect(self.resetSettings)
        self.prefsButton.clicked.connect(self.showPrefsWindow)

        # Add masks and validators
        self.nTrialsEntry.setValidator(QIntValidator(1000, 10 ** 7))
        self.ageGuessEntry.setValidator(QDoubleValidator())

        # =====================================================================
        # Settings / widget handlers
        # =====================================================================
        # Add pyqtconfig widget handlers
        # N.B. do this after populating combo boxes
        bind_pyqtconfig_handlers(self)
        logger.info(f"settings file located at: {GUI_SETTINGS.settings.fileName()}")

        # Call taskChange to initialise fit / data_type combo values when
        # starting for first time, or after settings file reset:
        if self.dataTypeCombo.currentText() == '' or \
                self.fitCombo.currentText() == '':
            self.taskChange()

    # =====================================================================
    # File menu functions
    # =====================================================================
    def showEvent(self, event):
        self.setActivityRatioOpts()
        self.eqGuessChange()
        super(MainWindow, self).showEvent(event)

    def setConsoleLogLevel(self, level):
        self.console_handler.setLevel(level)

    def screenUpdating(self):
        for app in xw.apps:
            app.screen_updating = True

    def updateInputDp(self):
        self.dp_workbook = self.selectDpWindow.wb
        self.dp_worksheet = self.selectDpWindow.ws
        self.dp_address = self.selectDpWindow.address
        self.dataRangeEntry.setText(f'{self.dp_worksheet}: {self.dp_address}')

    def updateOutAddress(self):
        self.out_workbook = self.refEditOut.wb
        self.out_worksheet = self.refEditOut.ws
        self.out_address = self.refEditOut.address

    # =====================================================================
    # Callback methods
    # =====================================================================

    def taskChange(self):
        task = self.taskCombo.currentText()
        data_type = self.dataTypeCombo.currentText()
        # Set data types.
        self.dataTypeCombo.clear()
        self.dataTypeCombo.addItems(TASKS[task]['data_types'])
        # Set fit options
        self.setFitOptions()
        self.setCovOpts()
        self.setMcOpt()
        # Set task specific activity ratio fields.
        self.initialEqChange()          # this method calls setActivityRaioOpt
        if task in ("Concordant [234U/238U]i", "U-Pb isochron age"):
            self.normPbCombo.setEnabled(True)
        else:
            self.normPbCombo.setEnabled(False)

        # Forced concordance options
        if task == "Concordant [234U/238U]i":
            self.fitCombo.setEnabled(False)
            self.selectButton.setEnabled(False)
            self.dataRangeEntry.setEnabled(False)
            self.initialEqOpt.setChecked(False)
            self.initialEqOpt.setEnabled(False)
        else:
            self.fitCombo.setEnabled(True)
            self.selectButton.setEnabled(True)
            self.dataRangeEntry.setEnabled(True)
            self.initialEqOpt.setEnabled(True)

        if task == "Single aliquot ages":
            self.wavCovOpt.setEnabled(True)
        else:
            self.wavCovOpt.setEnabled(False)

    def dataTypeChange(self):
        """Set fit menu according to task type.
        """
        data_type = self.dataTypeCombo.currentText()
        self.setActivityRatioOpts()
        self.setCovOpts()
        # self.setMcOpt()
        # set initial_eq option
        if data_type in ("other", "other x-y", "multiple"):
            self.initialEqOpt.setEnabled(False)
        else:
            self.initialEqOpt.setEnabled(True)

    def setFitOptions(self):
        task = self.taskCombo.currentText()
        self.fitCombo.clear()
        if task == 'Plot x-y data':
            self.fitCombo.addItems(REGRESSION_FITS + ['no fit'])
        elif TASKS[task]['fit'] == "regression":
            self.fitCombo.addItems(REGRESSION_FITS)
        else:
            self.fitCombo.addItems(WAV_FITS)
            if 'Single aliquot ages' in task:
                self.fitCombo.addItems(['no fit'])

    def setCovOpts(self):
        task = self.taskCombo.currentText()
        if task == 'Weighted average':
            self.covOpt.setEnabled(True)
        else:
            self.covOpt.setEnabled(False)
        self.covChange()

    def covChange(self):
        task = self.taskCombo.currentText()
        if self.covOpt.isChecked() and task == 'Weighted average':
            # deactivate sigma and error types
            self.err1sOpt.setEnabled(False)
            self.err2sOpt.setEnabled(False)
            self.errTypeCombo.setEnabled(False)
        else:
            self.err1sOpt.setEnabled(True)
            self.err2sOpt.setEnabled(True)
            self.errTypeCombo.setEnabled(True)

    def setMcOpt(self):
        """
        Enable Monte Carlo uncertainty option.
        """
        task = self.taskCombo.currentText()
        if task == 'Concordant [234U/238U]i':
            self.anUncertOpt.setEnabled(False)
            self.mcUncertOpt.setEnabled(True)
            self.mcUncertOpt.setChecked(True)
        elif task in ('Concordia-intercept age', 'U-Pb isochron age'):
            if self.initialEqOpt.isChecked():
                self.anUncertOpt.setEnabled(True)
                self.mcUncertOpt.setEnabled(True)
                self.mcUncertOpt.setChecked(True)
            else:
                self.anUncertOpt.setEnabled(False)
                self.mcUncertOpt.setEnabled(True)
                self.mcUncertOpt.setChecked(True)
        elif task in ('Plot x-y data', 'Weighted average'):
            self.anUncertOpt.setEnabled(False)
            self.mcUncertOpt.setEnabled(False)
        else:
            self.anUncertOpt.setEnabled(True)

    def setActivityRatioOpts(self):
        task = self.taskCombo.currentText()
        data_type = self.dataTypeCombo.currentText()

        # get original combo values
        A48_type_0 = self.A48Combo.currentText()
        A08_type_0 = self.A08Combo.currentText()
        A15_type_0 = self.A15Combo.currentText()

        # If initial eq disable all otherwise enable all.
        for x in (U238_ENTRIES + U238_ERR + U235_ENTRIES + U238_LABELS
                  + U235_ERR + U238_COMBOS + U235_COMBOS + U235_LABELS):
            w = getattr(self, x)
            # note eq. ages not allowed for 207Pb-corrected:
            if self.initialEqOpt.isChecked() and task != '207Pb-corrected':
                w.setEnabled(False)
            else:
                w.setEnabled(True)
                w.setEnabled(True)

        if not self.initialEqOpt.isChecked():
            if 'other' in data_type:
                for x in (U238_ENTRIES + U235_ENTRIES + U238_ERR + U235_ERR
                          + U238_COMBOS + U235_COMBOS):
                    w = getattr(self, x)
                    w.setEnabled(False)
            elif  "238U" in data_type:
                for x in (U235_ERR + U235_COMBOS + U235_ENTRIES):
                    w = getattr(self, x)
                    w.setEnabled(False)
            elif "235U" in data_type:
                for x in (U238_ERR + U238_COMBOS + U238_ENTRIES):
                    w = getattr(self, x)
                    w.setEnabled(False)

        if task == "Concordant [234U/238U]i":
            for x in (U238_ENTRIES + U235_ENTRIES + U238_ERR + U235_ERR +
                      U238_COMBOS + U235_COMBOS):
                w = getattr(self, x)
                w.setEnabled(True)
            self.A48Entry.setEnabled(False)
            self.A48ErrEntry.setEnabled(False)
            self.A48Combo.setEnabled(False)

        if task == "Single aliquot ages":
            for x in (U238_ENTRIES + U235_ENTRIES + U238_ERR + U235_ERR
                      + U238_COMBOS + U235_COMBOS):
                if not (x.startswith('A08') or x.startswith('A15')):
                    w = getattr(self, x)
                    w.setEnabled(False)

            self.A48Entry.setEnabled(False)
            self.A48ErrEntry.setEnabled(False)
            self.A48Combo.setEnabled(False)
            self.A68Entry.setEnabled(False)
            self.A68ErrEntry.setEnabled(False)
            self.A68Combo.setEnabled(False)

        # remove all items and then reset in next code block:
        while self.A48Combo.count() > 0:
            self.A48Combo.removeItem(0)
        while self.A08Combo.count() > 0:
            self.A08Combo.removeItem(0)
        while self.A15Combo.count() > 0:
            self.A15Combo.removeItem(0)

        if task == "Single aliquot ages":
            self.A08Combo.addItems(['DTh/U const.', 'Th/U melt const.'])
            # self.A48Combo.addItems(['initial'])
            self.A15Combo.addItems(['DPa/U const.'])
        else:

            self.A48Combo.addItems(['initial', 'present-day'])
            if task == "Concordant [234U/238U]i":
                self.A08Combo.addItems(['initial'])
            else:
                self.A08Combo.addItems(['initial', 'present-day'])
            self.A15Combo.addItems(['initial'])

        # Set back to original values (if legal)
        if A48_type_0 in [self.A48Combo.itemText(n) for n in (0, 1)]:
             n = 0 if A48_type_0 in ('', 'initial') else 1
             self.A48Combo.setCurrentIndex(n)
        if A08_type_0 in [self.A08Combo.itemText(n) for n in (0, 1)]:
             n = 0 if A08_type_0 in ('', 'initial', 'DTh/U const.') else 1
             self.A08Combo.setCurrentIndex(n)
        if A15_type_0 in [self.A15Combo.itemText(n) for n in (0, 1)]:
             n = 0 if A15_type_0 in ('', 'initial', 'DPa/U const.') else 1
             self.A15Combo.setCurrentIndex(n)

    def initialEqChange(self):
        self.setActivityRatioOpts()
        self.setMcOpt()
        if self.initialEqOpt.isChecked():
            self.normPbCombo.model().item(1).setEnabled(False)
            self.normPbCombo.setCurrentIndex(0)
        else:
            self.normPbCombo.model().item(1).setEnabled(True)

    def eqGuessChange(self):
        self.setMcOpt()
        if self.eqGuessOpt.isChecked():
            self.ageGuessEntry.setEnabled(False)
        else:
            self.ageGuessEntry.setEnabled(True)


    def A08TypeChange(self):
        if self.A08Combo.currentText() == 'DTh/U const.':
            self.A08Label.setText('<html><head/><body><p>D<span style=" '
                    'vertical-align:sub;">Th/U</span></p></body></html>')
        elif self.A08Combo.currentText() == 'Th/U melt const.':
            self.A08Label.setText('<html><head/><body><p>Th/U<span style=" '
                    'vertical-align:sub;">melt</span></p></body></html>')
        else:
            self.A08Label.setText('<html><head/><body><p>[<span style=" '
                  'vertical-align:super;">230</span>Th/<span style=" '
                  'vertical-align:super;">238</span>U]</p></body></html>')

    def A15TypeChange(self):
        if self.A15Combo.currentText() == 'DPa/U const.':
            self.A15Label.setText('<html><head/><body><p>D<span style=" '
                                  'vertical-align:sub;">Pa/U</span></p></body></html>')
        elif self.A15Combo.currentText() == 'Pa/U melt const.':
            self.A15Label.setText('<html><head/><body><p>Pa/U<span style=" '
                                  'vertical-align:sub;">melt</span></p></body></html>')
        else:
            self.A15Label.setText('<html><head/><body><p>[<span style=" '
                  'vertical-align:super;">231</span>Pa/<span style=" '
                  'vertical-align:super;">235</span>U]</p></body></html>')

    #=====================================================================
    # Window action methods
    #=====================================================================
    def openAboutDialog(self):
        self.aboutDialog.exec()

    def showLogWindow(self):
        self.logWindow.show()

    def showPrefsWindow(self):
        self.prefsWindow.show()
        # print("open prefs window")

    def hideLogWindow(self):
        self.logWindow.hide()

    def selectDp(self):
        self.hide()
        if self.selectDpWindow.exec():
            self.dataRangeEntry.setText(f"{self.selectDpWindow.ws} "
                    f"{self.selectDpWindow.address.replace('$','')}")
            self.show()

    def closeEvent(self, event):
        # self.saveSettings()
        super(MainWindow, self).closeEvent(event)

    def okClick(self):
        task = SHORT_TASK_NAMES[self.taskCombo.currentText()]
        # Check activity ratio fields aren't blacnk
        if not self.initialEqOpt.isChecked():
            for w in (self.A48Entry, self.A48ErrEntry, self.A08Entry,
                      self.A08ErrEntry, self.A68Entry, self.A68ErrEntry,
                      self.A15Entry, self.A15ErrEntry):
                t = w.text()
                try:
                    float(t)
                except ValueError:
                    msg = 'Activity ratio fields must contain ' \
                          'numeric values only and cannnot be left blank.'
                    self.showErrorDialog(text="Data selection error...",
                                         informative_text=msg)
                    return
        #Ensure data point selection has been made:
        if task != "forced_concordance":
            if any([x.text() == '' for x in (self.selectDpWindow.workbookEntry,
                        self.selectDpWindow.worksheetEntry,
                        self.selectDpWindow.addressEntry)]):
                msg = 'Data points must be selected before continuing.'
                self.showErrorDialog(text="Data selection error...",
                                    informative_text=msg)
                return
        self.hide()
        self.setupTask()

    # =====================================================================
    # Settings
    # =====================================================================
    def resetSettings(self):
        txt = 'Not yet implemented.'
        msg = f"For now, to restore default settings (1) close the application, " \
              f"(2) delete the file at: '{GUI_SETTINGS.settings.fileName()}', " \
              f"and (3) re-open the application."
        self.showErrorDialog(icon=QMessageBox.Warning, text=txt,
                               informative_text=msg)

    # =====================================================================
    # Plotting / calc. task options
    # =====================================================================
    def taskEnd(self, exception):
        self.progressDialog.hide_and_reset()

        # check for returned messages
        if self.retval is not None:
            val = self.retval.split("::")
            for msg in val[:-1]:
                txt, inform_txt = msg.split("|")
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Warning)
                msg.setText(txt)
                msg.setInformativeText(inform_txt)
                msg.setStandardButtons(QMessageBox.Ok)
                msg.exec_()

        if exception:
            self.showErrorDialog(self, text="DQPB encountered an error",
                    informative_text="Check the error log for details on what "
                                     "went wrong.")
        else:
            logger.debug("completed")
            self.show()
            self.activateWindow()

    def updateRetval(self, retval):
        self.retval = retval

    def updateStatusBar(self, data):
        max_char = 60
        message = data.split("::")[1]
        message = f'{message[:max_char-3]}...' if len(message) > max_char \
            else message
        self.statusBar().showMessage(message, 3000)

    def showErrorDialog(self, icon=QMessageBox.Warning, text="text",
                        informative_text=None):
        """Show error dialog.
        """
        dialog = QMessageBox(parent=self)
        dialog.setIcon(QMessageBox.Warning)
        dialog.setText(text)
        if informative_text is not None:
            dialog.setInformativeText(informative_text)
        dialog.setStandardButtons(QMessageBox.Ok)
        dialog.exec()

    def inputError(self, text, informative_text):
        """Show error dialog then raise InputError
        """
        self.showErrorDialog(text=text, informative_text=informative_text)
        raise InputError(informative_text)

    def setupTask(self):
        """
        Set up new plot or calc. task after user clicks OK.
        0. Show dp label selection dialogue.
        1. Checks user inputs and data points.
        2. Ask user for additional inputs if needed.
        3. Compile settings, inputs and data points into dict.
        4. Run task in new thread.
        """
        task = SHORT_TASK_NAMES[self.taskCombo.currentText()]
        data_type = SHORT_DATA_TYPES[self.dataTypeCombo.currentText()]
        self.DThU_const = True if self.A08Combo.currentText() == 'DTh/U const.' else False
        text = 'Data selection error...'

        try:
            # check activity ratio fields
            if data_type in ("206Pb*", "207Pb*", "cor207Pb"):
                # initial equilibrium option not allowed for Modified 207Pb
                # ages, and not yet implemented for Pb/u ages, so raise error.
                if self.initialEqOpt.isChecked():
                    self.inputError('Not yet implemented', 'Equilibrium single aliquot '
                       'age calculations are not yet implemented in DQPB.')
            if task == 'forced_concordance':
                # show forced-concordance dp selecion dialogue:
                if not self.fcDialog.exec():
                    raise InputError()      # return to main window
                # check each data selection
                self.dp_iso86 = validateSelection(self, self.fcDialog.iso86_dp, 'iso-206Pb',
                                    data_name='data points', shape=None,
                                    check_dp_errors=True, dtype="double")
                self.dp_iso57 = validateSelection(self, self.fcDialog.iso57_dp, "iso-207Pb",
                                    data_name='data points', shape=None,
                                    check_dp_errors=True, dtype="double")
                if not (self.dp_iso86.shape[0] == self.dp_iso57.shape[0]):
                    self.inputError(text, 'Isochron data selections must have the '
                                     'same number of data points.')
            else:   # all other task types:
                self.dp = validateSelection(self, self.selectDpWindow.range.value,
                                data_type, data_name='data points', shape=None,
                                check_dp_errors=True, dtype="double")
            # Show data label selection window:
            if self.dpLabelOpt.isChecked():
                if not self.selectLabelsWindow.exec():
                    raise InputError('task cancelled')
                self.dp_labels = self.selectLabelsWindow.data
                if task == 'forced_concordance':
                    dp_shape = (self.dp_iso86.shape[0],)
                else:
                    dp_shape = (self.dp.shape[0],)
                validateSelection(self, self.dp_labels, 'dp_labels',
                                  data_name='data point labels',
                                  check_dp_errors=False, shape=dp_shape,
                                  dtype=str)
            # reset to None so labels aren't recycled for next task:
            else:
                self.dp_labels = None
            # Show Th/U_min dialog
            if data_type in ("206Pb*", "cor207Pb"):
                if not self.DThU_const:
                    if data_type == "cor207Pb" and self.anUncertOpt.isChecked():
                        self.inputError("Option not yet available",
                            "Analytical uncertainties are not yet "
                            "implemented for 207Pb-corrected ages " 
                            "with constant Th/U melt.")
                    self.ThUminDialog.n = self.dp.shape[0]
                    if not self.ThUminDialog.exec():
                        raise InputError()      # task cancelled
                    else:
                        self.ThUmin_data = validateSelection(
                                self, self.ThUminDialog.range.value, "ThU_min",
                                data_name='Th/U_min', check_dp_errors=False,
                                shape=None, dtype='double')
            if not self.initialEqOpt.isChecked() and \
                    data_type not in ('other', 'other_xy'):
                validateDiseqState(self, data_type)
            validateInputs(self, task, data_type)
            # Show common Pb76 dialog
            if data_type == 'cor207Pb':
                if not self.comPb76Dialog.exec():
                    raise InputError()          # task cancelled
            # Show covariance matrix dialog.
            if task == 'wtd_average' and self.covOpt.isChecked():
                self.covMatDialog.nrow = self.dp.size
                self.covMatDialog.ncol = self.dp.size
                if not self.covMatDialog.exec():
                    raise InputError('task cancelled')
                self.cov = validateSelection(self, self.covMatDialog.data,
                            'covmat', data_name='covariance matrix',
                            check_dp_errors=False, shape=(self.dp.size, self.dp.size),
                            dtype="double")
            else:
                self.cov = None
            # Show axis labels dialog.
            if (task == "plot_data" and data_type == "other_xy") \
                    or task == "wtd_average":
                if task == 'wtd_average':
                    self.axisLabelsDialog.xLabelEntry.setEnabled(False)
                    self.axisLabelsDialog.xAxisLabel.setEnabled(False)
                else:
                    self.axisLabelsDialog.xLabelEntry.setEnabled(True)
                    self.axisLabelsDialog.xAxisLabel.setEnabled(True)
                if not self.axisLabelsDialog.exec():
                    raise InputError('task cancelled')
                self.x_label = self.axisLabelsDialog.x_label
                self.y_label = self.axisLabelsDialog.y_label
            # Show axis limits dialog.
            if not self.autoscaleOpt.isChecked():
                if task == 'forced_concordance':
                    msg = 'User set axis limits are not yet implemented for ' \
                          'concordant [234U/238U]i routine. Axis limits will be ' \
                          'autoscaled.'
                    self.showErrorDialog(text='Note:', informative_text=msg)
                else:
                    self.axisLimsDialog.exec()
            # Get output address.
            output_range_ok = False
            while not output_range_ok:
                if task == "forced_concordance":
                    self.outputAddressDialog.setDefault(self.fcDialog.iso86_range.offset(
                        row_offset=self.fcDialog.iso86_range.rows.count + 1).resize(1, 1))
                else:
                    dp_range = self.selectDpWindow.range
                    self.outputAddressDialog.setDefault(dp_range.offset(
                        row_offset=dp_range.rows.count + 1).resize(1, 1))
                if not self.outputAddressDialog.exec():
                    raise InputError('task cancelled')

                output_range_ok = self.overwriteCheck()

            try:
                task_opts = getTaskOpts(self, task, data_type)
            except Exception as e:
                logger.exception(e.__traceback__)
                self.inputError('Unexpected error', 'Error compiling plotting / '
                                'calculation task options. See error log for '
                                'further details.')
        except InputError:
            self.show()     # return to main window
        else:
            self.retval = None          # reset retval
            runTask(self, task_opts)    # execute plot / calc task.

    def overwriteCheck(self):
        """
        Check if printed results are likely to overwrite data, and if so, offer
        to change output location.
        """
        output_range_ok = True
        print_size = estimatePrintRange(self)
        output_range = xw.Range(self.outputAddressDialog.range.get_address())
        output_range = output_range.resize(row_size=print_size[0],
                                           column_size=print_size[1])
        empty = output_range.value is None or all([item is None for sublist 
                    in output_range.value for item in sublist])
        if not empty:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)
            msg.setText("Excel data may be over-written by results")
            msg.setInformativeText("Would you like to change "
                                   "the output location?")
            msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            msg.setDefaultButton(QMessageBox.Yes)
            retval = msg.exec_()
            output_range_ok = (retval == QMessageBox.No)

        return output_range_ok


# =============================================================================
# Check user inputs and options are acceptable
# =============================================================================

def validateDiseqState(main, data_type):
    """ """
    # if data_type in ('206Pb*', '207Pb*', 'cor207Pb'):
        # Get partition coefficient ratio data
        # if data_type in ('206Pb*', 'cor207Pb'):
        #     if main.DThU_const:
        #         validateSelection(main, main.selectDpWindow.range.value,
        #                     'ThU_min', data_name='data point',
        #                     check_dp_errors=False, shape=(main.n,), dtype='double')
        #     # Check ThU min values are of correct type and size.
        #     try:
        #         main.ThU_min = np.array(main.ThUminDialog.ThU_min, dtype='double')
        #     except:
        #         main.inputError('Data selection error', "Error reading Th/U "
        #                 "min. values from spreadsheet. Try "
        #                 "double checking data selection.")
    
    # Check that no activity ratio fields are left blank
    if data_type in ('tw', 'wc', '206Pb*', '207Pb*'):    
        for x in (U238_ENTRIES + U238_ERR + U235_ENTRIES + U235_ERR):
            w = getattr(main, x)
            if w.text() == "":
                main.inputError('Data selection error',
                    "Activity ratio fields cannot be left blank")

    # check measured activity ratios are resolvable from equilibrium
    if (data_type in ('tw', 'wc', 'iso-206Pb') and not
        main.initialEqOpt.isChecked()):
        resolvable_234_238 = True
        resolvable_230_238 = True
        if main.A48Combo.currentText() == 'present-day':
            a234_238 = float(main.A48Entry.text())
            a234_238_1s = float(main.A48ErrEntry.text())
            resolvable_234_238 = util.meas_diseq(a234_238, a234_238_1s)
        if main.A08Combo.currentText() == 'present-day':
            a230_238 = float(main.A08Entry.text())
            a230_238_1s = float(main.A08ErrEntry.text())
            resolvable_230_238 = util.meas_diseq(a230_238, a230_238_1s, which='a230_238')

        if not resolvable_234_238 or not resolvable_230_238:
            ratio = 'ratio'
            if not resolvable_230_238 and not resolvable_234_238:
                bad_ratio = '234U/238U and 230Th/238U activity ratios are'
                ratio = 'ratios'
            elif not resolvable_234_238:
                bad_ratio = '234U/238U activity ratio is'
            else:
                bad_ratio = '230Th/238U activity ratio is'

            txt = f"The input measured {bad_ratio} not resolvable from " \
                  f"radioactive equilibrium with 95% confidence. Monte Carlo " \
                  f"simulation will not proceed because the computed " \
                  f"age uncertainties may be unreliable.\n\n " \
                  f"Do you wish to continue with age calculation?"
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)
            msg.setText(f"Measured activity {ratio} not resolvable from equilibrium")
            msg.setInformativeText(txt)
            msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            retval = msg.exec_()

            if retval == QMessageBox.No:
                raise InputError
            

def validateInputs(main, task, data_type):
    """ 
    Check other calc options.
    """
    if task == 'concordia_intercept_age' and not main.initialEqOpt.isChecked():
        min_age = float(main.prefsWindow.concintMinAgeEntry.text())
        max_age = float(main.prefsWindow.concintMaxAgeEntry.text())
        age_guess = float(main.ageGuessEntry.text())
        if not main.eqGuessOpt.isChecked() and not main.initialEqOpt.isChecked():
            if not min_age < age_guess < max_age:
                main.inputError('Data input error.', 'Disequilbrium age guess must be '
                        'between min and max limits. \n\nGo to the Numerical '
                        'tab in the to set disequilbrium age guess options.')



def validateSelection(main, data, array_type, data_name='data point',
            check_dp_errors=True, shape=None, dtype='double'):
    """
    Check data point selection includes appropriate number of rows and columns.
    Returns data as an array.
    """
    assert array_type in ("tw", "wc", "cor207Pb", "iso-207Pb", "iso-206Pb",
                         "206Pb*", "207Pb*", "other_xy", "other", "covmat",
                         "ThU_min", 'dp_labels')
    try:
        data = np.asarray(data, dtype=dtype)
    except:
        main.inputError('Data selection error', f'Could not load {data_name} into '
                       f'numeric array of type {dtype}. Check all elements are '
                       f'of appropriate data type.')
    if data.ndim == 0 and array_type in \
            ("tw", "wc", "cor207Pb", "iso-207Pb", "iso-206Pb"):
        main.inputError("Data selection error", f"Date point selection must "
                    f"include more than one cell.")

    if dtype in ('int', 'double'):
        for x in np.nditer(data):
            if np.isnan(x):
                main.inputError('Data selection error',
                                f'{data_name.capitalize()} selection cannot '
                                f'contain empty cells.')

    if array_type in ("tw", "wc", "cor207Pb", "iso-206Pb", "iso-207Pb",
                     "other_xy"):
        if data.shape[0] < 2:
            main.inputError('Data selection error',
                            'Cannot fit regression line to less than 2 data '
                            'points.')
        if data.ndim != 2 or data.shape[1] not in (4, 5):
            main.inputError('Data selection error',
                            f"4 or 5 columns must be included in a for a "
                            f"{array_type} selection.")
    elif array_type in ('other', '206Pb*', '207Pb*'):
        if array_type == "other" and main.covOpt.isChecked():
                if data.ndim != 1:
                    main.inputError("Data selection error", f"Data point selection "
                                   f"must contain 1 column if inputting errors "
                                   f"as covariance matrix.")
        else:
            if data.ndim != 2 or data.shape[1] != 2:
                # note: inputting errors as a covariance matrix not yet allowed...
                main.inputError("Data selection error", f"Date selection must "
                                f"contain 2 columns for '{array_type}'")

    elif array_type == "covmat":
        # shape should already have been checked during data selection
        if not misc.pos_def(data):
            main.inputError("Data selection error.", "Covariance matrix must "
                     "be symmetric and positive semi-definite.")
            if data.shape != shape:
                main.inputError("Data selection error", f"Number of cells in "
                    f"{array_type} selection should equal number of data points.")
    elif array_type == 'dp_labels':
        if data.shape != shape:
            main.inputError("Data selection error", f"Number of "
                f"data point labels must equal number of data points.")

    if check_dp_errors and data.ndim > 1:
        # Check data point errors are reasonable
        error_type = main.errTypeCombo.currentText()
        sigma = 1 if main.err1sOpt.isChecked() else 2
        if data.shape[1] in (4, 5):
            x, ox, y, oy = data[:, :4].T
            iter = zip((x, y), (ox, oy))
        elif data.shape[1] == 2:
            x, ox = data[:, :2].T
            iter = zip((x,), (ox,))
        for v, e in iter:
            # Convert errors to 1 sigma absolute
            a = 1. if error_type == 'abs.' else v
            b = 0.01 if 'per' in error_type else 1.
            sv = e * a * b / sigma

            if np.any(sv / v > DP_ERROR_WARNING_THRESHOLD):
                dialog = QMessageBox(parent=main)
                dialog.setIcon(QMessageBox.Warning)
                dialog.setText("Data point uncertainties seem quite large.")
                dialog.setInformativeText(
                    f'Assigned uncertainties on one or more data points exceed '
                    f'the expected threshold. Please ensure that the correct '
                    f'input uncertainty type and sigma level was selected. '
                    f'\nAre you sure you wish to continue?')
                dialog.setStandardButtons(QMessageBox.No | QMessageBox.Yes)
                retval = dialog.exec()
                if retval != QMessageBox.Yes:
                    raise InputError

    return data


def estimatePrintRange(parent):
    """
    Estimate the cell dimensions in spreadsheet that will be taken up by printed
    results.

    Notes
    ------
    Figures are not included since they always come at the end and do not
    over-write Excel data.

    """
    task = SHORT_TASK_NAMES[parent.taskCombo.currentText()]
    data_type = SHORT_DATA_TYPES[parent.dataTypeCombo.currentText()]
    fit = SHORT_FITS[parent.fitCombo.currentText()]
    print_settings = parent.printSettingsOpt.isChecked()
    eq = parent.initialEqOpt.isChecked()
    mc = parent.mcUncertOpt.isChecked()
    mc_summary = parent.McSummaryOpt.isChecked()
    meas_a234_238 = parent.A48Combo.currentText() == 'present-day'
    meas_a230_238 = parent.A08Combo.currentText() == 'present-day'
    save_plots = parent.savePlotsOpt.isChecked()

    row = 0
    col = 0

    if task in ('concordia_intercept_age', 'isochron_age', 'plot_data'):
        col = 2
        # print opts
        if print_settings:
            row += 2
            if fit is not None:
                row += 4
                if fit == 'rs':
                    row += 1
            if data_type in ('tw', 'wc'):
                if eq:
                    row += 3
                else:
                    row += 11
            if data_type.startswith('iso'):
                if '206Pb' in data_type:
                    if eq:
                        row += 2
                    else:
                        row += 8
                else:
                    if eq:
                        row += 2
                    else:
                        row += 4
            if task != 'plot_data':
                if not eq:
                    row += 2
                if mc:
                    row += 5
            if fit is not None and save_plots:
                row += 1
        # fit results
        if fit is not None:
            row += 2
            if fit.startswith('c'):
                row += 12
            else:
                row += 9
        # age
        if eq:
            row += 4
            if mc:
                row += 8
                if mc_summary:
                    row += 2
        else:
            if parent.outputEqOpt.isChecked():
                row += 4
            row += 9
            if task == 'concordia_intercept_age' or data_type.endswith('206Pb'):
                if meas_a234_238:
                    row += 5
                if meas_a230_238:
                    row += 5
            if mc_summary:
                row += 4

    # Single aliquot age results
    elif task == 'pbu_age':
        if print_settings:
            row += 5
            if not eq:
                row += 1
            if fit is not None:
                if fit.startswith('rs'):
                    row += 1
            if data_type.startswith('cor'):
                row += 2    # common Pb
                row += 7    # upb const
            elif data_type.startswith('206'):
                row += 4    # upb const
            elif data_type.startswith('207'):
                row += 2    # upb const
            if data_type.startswith(('cor', '206')):
                if parent.DThU_const:
                    row += 3
                else:
                    row += 4
            if data_type.startswith(('cor', '207')):
                row += 2
            if mc:
                row += 5    # mc opts
            if save_plots:
                row += 1

        n = parent.dp.shape[0]

        if eq:
            # TODO: not yet implemented
            pass
        else:
            if parent.outputEqOpt.isChecked():
                # TODO: not yet implemented
                pass
            row += (2 + n)
            col = 4
            if mc:
                col += 2
                if mc_summary:
                    col += 3

        # wav
        if fit is not None:
            if fit.startswith('c'):
                row += 10
        else:
            row += 8

    
    elif task == 'forced_concordance':
        col = 2
        # assumes classical fit for now
        if print_settings:
            row += 7
            row += 4    # activity ratios
            row += 5    # mc opts
            row += 7    # upb const
            if save_plots:
                row += 1
        # iso-207Pb fit
        row += 2
        row += 12
        # iso-206Pb fit
        row += 2
        row += 12
        if parent.outputEqOpt.isChecked():
            row += 4
        # results
        row += 10
        if mc_summary:
            row += 4

    elif task == 'wtd_average':
        col = 2
        if print_settings:
            row += 4
        if fit.startswith('c'):
            row += 10
        else:
            row += 8

    return row, col


def getTaskOpts(main, task, data_type):
    """Compile task options and settings into a dictionary.
    """
    opts = {}
    # Add all settings from GuiSettingsMap to opts.
    for k in GUI_SETTINGS.settings.allKeys():
        v = GUI_SETTINGS.get(k)
        if k == 'user_colors':
            continue
        # convert strings to numeric data types / bools
        type_ = util.guess_type(v)
        if type_ in (int, float):
           v = type_(v)
        elif type_ is bool:
            if str(v).strip().lower() == 'true':
                v = True
            else:
                v = False
        opts[k] = v

    # Options not yet implemented.
    opts['sample_name'] = None
    # Add data points to opts dict.
    if task == "forced_concordance":
        opts['dp_iso86'] = main.dp_iso86
        opts['dp_iso57'] = main.dp_iso57
    else:
        opts['dp'] = main.dp
    opts['dp_labels'] = main.dp_labels
    opts['output_workbook'] = main.outputAddressDialog.wb
    opts['output_worksheet'] = main.outputAddressDialog.ws
    opts['output_address'] = main.outputAddressDialog.address
    # Set font family.
    opts['font_family'] = \
        main.plotFormatWindow.font_families[opts['font']]
    # Convert axis limits to float or None type:
    for name in ("dpp_xmin", "dpp_xmax", "dpp_ymin", "dpp_ymax",
                 "int_xmin", "int_xmax", "int_ymin", "int_ymax",
                 "wav_ymin", "wav_ymax"):
        # If autoscale, get value from limits dialog, otherwise set to None:
        if not main.autoscaleOpt.isChecked():
            val = getattr(main.axisLimsDialog, name)
            if val in (""):
                val = None
            else:
                val = float(val)
        else:
            val = None
        opts[name] = val
    opts['x_label'] = main.axisLabelsDialog.x_label
    opts['y_label'] = main.axisLabelsDialog.y_label
    # Convert string to floats
    if data_type == 'cor207Pb':
        opts['Pb76'] = float(opts['Pb76'])
        if opts['Pb76_1s'] == '':
            opts['Pb76_1s'] = 0.
        else:
            opts['Pb76_1s'] = float(opts['Pb76_1s'])
    else:
        opts['Pb76'] = None
        opts['Pb76_1s'] = None

    # Get partition coefficient inputs:
    opts['DThU_const'] = None
    opts['ThU_melt'] = None
    opts['ThU_melt_1s'] = None
    opts['DThU'] = None
    opts['DThU_1s'] = None
    opts['DPaU'] = None
    opts['DPaU_1s'] = None
    opts['meas_Th232_U238'] = False
    opts['Pb208_206'] = None
    opts['Pb208_206_1s'] = None
    opts['Th232_U238'] = None
    opts['Th232_U238_1s'] = None

    if data_type in ('206Pb*', 'cor207Pb'):
        if not main.DThU_const:
            opts['DThU_const'] = False
            opts['ThU_melt'] = opts['A08']
            opts['ThU_melt_1s'] = opts['A08_err']
            if opts['ThU_min_type'] == '232Th/238U':
                opts['meas_Th232_U238'] = True
                opts['Th232_U238'] = main.ThUmin_data[:, 0]
                opts['Th232_U238_1s'] = main.ThUmin_data[:, 1]
            else:
                opts['meas_Th232_U238'] = False
                opts['Pb208_206'] = main.ThUmin_data[:, 0]
                opts['Pb208_206_1s'] = main.ThUmin_data[:, 1]
        else:
            opts['DThU_const'] = True
            opts['DThU'] = opts['A08']
            opts['DThU_1s'] = opts['A08_err']

    if data_type in ('207Pb*', 'cor207Pb'):
        opts['DPaU'] = opts['A15']
        opts['DPaU_1s'] = opts['A15_err']

    # Add covariance matrix
    if main.cov is not None:
        opts['cov'] = main.cov
    # Reformat some options:
    if str(opts['dpp_marker_max_age']).strip() in ('None', 'none', ''):
        opts['dpp_marker_max_age'] = None
    else:
        opts['dpp_marker_max_age'] = float(opts['dpp_marker_max_age'])
    
    if str(opts['int_marker_max_age']).strip() in ('None', 'none', ''):
        opts['int_marker_max_age'] = None
    else:
        opts['int_marker_max_age'] = float(opts['int_marker_max_age'])
    
    opts['int_manual_age_markers'] = [x for x in opts['int_manual_age_markers'].split()] # keep as list of strings
    opts['dpp_manual_age_markers'] = [x for x in opts['dpp_manual_age_markers'].split()]

    if task == 'forced_concordance':
        opts['fit_iso86'] = SHORT_FITS[main.fcDialog.iso86FitCombo.currentText()]
        opts['fit_iso57'] = SHORT_FITS[main.fcDialog.iso57FitCombo.currentText()]
        opts['A48'] = np.nan
        opts['A48_err'] = np.nan
        opts['A48_type'] = 'initial'
    if opts['fit'] is None:
        opts['fit_regression'] = False
    else:
        opts['fit_regression'] = True
    opts['mc_trials'] = int(opts['mc_trials'])
    opts['concint_age_min'] = float(opts['concint_age_min'])
    opts['concint_age_max'] = float(opts['concint_age_max'])
    # for k, v in opts.items():
        # if k.endswith(("xmin", "x_max", "y_min", "y_max")):
        #     if v == "":
        #         opts[k] = None
    # Compile lists
    # opts['age_range'] = [opts['lower_age_limit'],
    #                           opts['upper_age_limit']]
    # opts['data_label_xy_offset'] = util.string_to_list(
    #     opts['data_label_xy_offset'], dtype='int'
    # )
    # Set error type variables.
    opts['sigma_level'] = 1 if main.err1sOpt.isChecked() else 2
    opts['error_type'] = "per" if main.errTypeCombo.currentText() \
                                       == "percent" else "abs"
    if opts['xl_cell_color'] == '':
        opts['xl_cell_color'] = None
    if opts['rng_seed'] == '':
        opts['rng_seed'] = None

    return opts


def runTask(parent, task_opts):
    """
    Note there are some issues with numpy running on QThreads.
    It seems these can be limited by increasing the QThread default stack size.
    https://github.com/numpy/numpy/issues/13155
    https://github.com/numpy/numpy/issues/11551
    """
    task_opts = copy.deepcopy(task_opts)

    if debug:
        parent.worker = TaskWorker(parent, task_opts, parent.progressDialog)
        parent.worker.run()

    else:
        parent.parent = parent
        parent.thread = QThread()

        # TODO: verify that this stack size is appropriate across different systems.
        # use multiples of 4 bytes
        parent.thread.setStackSize(2 * 2048 * 10 ** 3)
        parent.worker = TaskWorker(parent, task_opts, parent.progressDialog)
        parent.worker.moveToThread(parent.thread)

        # connect signals and slots
        parent.thread.started.connect(parent.worker.run)

        #
        parent.thread.finished.connect(parent.thread.deleteLater)
        parent.worker.finished.connect(parent.thread.quit)
        parent.worker.finished.connect(parent.worker.deleteLater)
        parent.worker.finished.connect(parent.taskEnd)

        # parent.worker.finished.connect(parent.progressDialog.flagComplete)
        # parent.worker.finished.connect(parent.showMain)

        parent.worker.msg_signal.connect(parent.progressDialog.updateMessage)
        parent.worker.progress_signal.connect(parent.progressDialog.updateProgress)
        parent.worker.ret_signal.connect(parent.updateRetval)

        # start the thread
        parent.progressDialog.show()
        parent.thread.start()


def terminateTask(parent):
    """ """
    # Show confirmation dialog
    dialog = QMessageBox(parent=parent)
    dialog.setText("Are you sure you want to terminate this task before "
                   "it has finished?")
    dialog.setInformativeText("Early termination may lead to loss "
                              "of spreadsheet data and other problems.")
    dialog.setStandardButtons(QMessageBox.No | QMessageBox.Yes)

    if not dialog.exec():
        # Confirm thread is still running
        if parent.thread.isRunning():
            #TODO terminate without closing the parent app.
            pass

    # def showMain(parent):
    #     QTimer.singleShot(300, parent.show)


class TaskWorker(QThread):

    finished = pyqtSignal(bool)
    msg_signal = pyqtSignal(str)
    progress_signal = pyqtSignal(int)
    ret_signal = pyqtSignal(str)

    def __init__(self, parent, task_opts, progressDialog):
        super().__init__()
        self.task_opts = task_opts
        self.progressDialog = progressDialog
        self.parent = parent

    def run(self):
        """
        Run a plotting or computation task in a separate thread.
        """
        try:
            task = setup_calc.Task(self.task_opts, self.msg_signal,
                            self.progress_signal, self.ret_signal)
            task.run()
        except:
            logger.exception(f"exception encountered while executing "
                     f"{self.task_opts['task']}")
            if debug:
                self.parent.taskEnd(True)
            else:
                self.msg_signal.emit("Error...")        # show in progress bar
                time.sleep(1)
                self.finished.emit(True)
        else:
            if debug:
                self.parent.taskEnd(False)
            else:
                self.msg_signal.emit("Completed...")        # show in progress bar
                self.progress_signal.emit(100)
                time.sleep(1)
                self.finished.emit(False)


# =============================================================================
# Progress bar
# =============================================================================

class ProgressDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)

        uiPath = os.path.join("uis", "progress.ui")
        loadUi(resourceAbsolutePath(uiPath), baseinstance=self, package="dqpb")

        self.label.setText("ready")
        self.progressBar.setValue(0)

        # Connect buttons
        # self.terminateButton.clicked.connect(parent.terminateTask)
        self.hideButton.clicked.connect(self.hide)

    def updateProgress(self, value):
        self.progressBar.setValue(value)
        # self.label.setText(text)

    def updateMessage(self, text):
        self.label.setText(text)

    def flagComplete(self, error):
        if not error:
            self.progressBar.setValue(100)
            self.label.setText("Done...")
        else:
            # TODO: tidy this up
            self.label.setText("Error...")
            self.hide_and_reset()

    def hide_and_reset(self):
        self.hide()
        self.progressBar.setValue(0)
        self.label.setText("Ready...")


def get_xl_selection():
    """ Get selected range from Excel worksheet.
    """
    try:
        if xw.apps.count > 0:
            if xw.apps.active.books.count > 0:
                active_wb = xw.books.active
                wb = active_wb.fullname
                range = active_wb.selection
                if range is not None:
                    ws = range.sheet.name
                    address = range.address
                    return wb, ws, address, range
    except Exception as e:
        logger.exception(e.__traceback__)
        pass
    raise XlError


# =============================================================================
# Excel data selection dialogs
# =============================================================================

class RangeSelectDialog(QDialog):
    """
    Base class dialog for spreadsheet address selection. If there is a problem
    with the selection, then reject() is called.
    """
    def __init__(self, parent, text=None, warning_text=None, wb=None, ws=None,
                 address=None, title='Dialog', check_dim=False, as_string=False,
                 button_txt=None):
        super(RangeSelectDialog, self).__init__(parent)

        self.parent = parent
        self.as_string = as_string

        # Local attributes
        self.wb = wb
        self.ws = ws
        self.address = address

        self.range = None
        self.data = None
        self.dialog = None

        self.nrow = None
        self.ncol = None

        uiPath = os.path.join("uis", "range_select.ui")
        loadUi(resourceAbsolutePath(uiPath), baseinstance=self,
               package="dqpb")

        self.Label.setText(text)
        self.setWindowTitle(title)
        if button_txt is not None:
            self.getSelectionButton.setText(button_txt)

        self.getSelectionButton.clicked.connect(self.getSelection)
        self.okButton.clicked.connect(self.okEvent)
        self.cancelButton.clicked.connect(self.close)

    def getSelection(self):
        """ Check spreadsheet selection is accessible.
        """
        try:
            wb, ws, address, range = get_xl_selection()
            self.workbookEntry.setText(wb)
            self.worksheetEntry.setText(ws)
            self.addressEntry.setText(address)
        except XlError:
            msg = 'Unable able to find data selection in an open Excel ' \
                  'workbook. This may mean that no cells have been ' \
                  'selected or it may be the result of a permissions error.'
            self.showErrorDialog("Error accessing spreadsheet data",
                     informative_text=msg)

    def okEvent(self):
        """ When OK is clicked, check data and call accept() if all good, or
        else show error and call reject().
        """
        try:
            # If no selection has been made, then return.
            if any([x in ("", None) for x in (self.workbookEntry.text(),
                    self.worksheetEntry.text(), self.addressEntry.text())]):
                msg = 'Selection fields cannot be left blank.'
                self.showErrorDialog("Problem with spreadsheet data selection",
                                    informative_text=msg)
                raise XlError

            # Check excel app is open
            if xw.apps.count < 1:
                msg = 'No open instances of Excel could be found.'
                self.showErrorDialog("Problem with spreadsheet data selection",
                                     informative_text=msg)
                raise XlError

            if xw.books.count < 1 or self.workbookEntry.text() not in \
                    [x.fullname for x in xw.books] + [x.name for x in xw.books]:
                msg = f'Could not find open workbook: {self.workbookEntry.text()}.'
                self.showErrorDialog("Problem with spreadsheet data selection",
                            informative_text=msg)
                raise XlError

            if self.worksheetEntry.text() not in \
                    [x.name for x in xw.Book(self.workbookEntry.text()).sheets]:
                self.showErrorDialog(
                    "Problem with spreadsheet data selection",
                    informative_text=f'Could not find sheet named '
                    f'{self.worksheetEntry.text()} in workbook: '
                    f'{self.workbookEntry.text()}.')
                raise XlError

            # Read data from spreadsheet
            try:
                self.range = xw.Book(self.workbookEntry.text())\
                                .sheets[self.worksheetEntry.text()]\
                                .range(self.addressEntry.text())
                if self.as_string:
                    self.data = self.range.options(numbers=lambda x: str(int(x))).value
                else:
                    self.data = self.range.value
            except:
                msg = ('Ensure field entries are correct, and that the workbook is open, '
                    'is not being used by another program, and is not passwored protected.')
                self.showErrorDialog("Problem with spreadsheet data selection", informative_text=msg)
            else:
                # TODO: why does this reference covariance matrix specifically? Is it a copy-paste error?
                shape = self.range.shape
                if self.nrow is not None and shape[0] != self.nrow:
                    msg = (f'Mismatch between number of data points ({self.nrow}) '
                           f'and size of covariance matrix ({shape[0]} x '
                           f'{shape[1]}).')
                    self.showErrorDialog("Problem with spreadsheet data selection",
                                         informative_text=msg)
                if self.ncol is not None and shape[1] != self.ncol:
                    msg = (f'Mismatch between number of data points ({self.nrow}) and '
                           f'size of covariance matrix ({shape[0]} x '
                           f'{shape[1]}).')
                    self.showErrorDialog("Problem with spreadsheet data selection",
                                         informative_text=msg)

        except XlError:
            pass
        
        else:
            # update local attributes:
            self.wb = self.workbookEntry.text()
            self.ws = self.worksheetEntry.text()
            self.address = self.addressEntry.text()
            self.accept()

    def closeEvent(self, event):
        # save settings?
        self.reject()
        self.parent.show()

    def showErrorDialog(self, text, informative_text=None,
                        icon=QMessageBox.Warning):
        # Show error dialog
        self.dialog = QMessageBox(parent=self, text=text, icon=icon)
        self.dialog.setInformativeText(informative_text)
        self.dialog.setStandardButtons(QMessageBox.Ok)
        self.dialog.exec()

    def setDefault(self, default):
        # Set defaults.
        try:
            rng = default
        except:
            logger.debug('could not set default range for range select dialog')
        else:
            self.workbookEntry.setText(rng.sheet.book.fullname)
            self.worksheetEntry.setText(rng.sheet.name)
            self.addressEntry.setText(rng.address)


# =============================================================================
# Th/U_min data selection dialog
# =============================================================================
class ThUminSelectDialog(QDialog):
    """

    """
    def __init__(self, parent):
        super(ThUminSelectDialog, self).__init__(parent)

        self.parent = parent

        # Local attributes
        self.n = None
        self.wb = None
        self.ws = None
        self.address = None

        self.range = None
        self.data = None

        uiPath = os.path.join("uis", "ThU_select.ui")
        loadUi(resourceAbsolutePath(uiPath), baseinstance=self,
               package="dqpb")

        self.Label.setText('Select measured data for each aliquot in spreadsheet. '
                           '\nUncertainties should be 1\u03C3 (abs.)')
        self.ThUminCombo.addItems(['232Th/238U',
                                   'radiogenic 208Pb/206Pb'])

        self.getSelectionButton.clicked.connect(self.getSelection)
        self.okButton.clicked.connect(self.okEvent)
        self.cancelButton.clicked.connect(self.close)

        # Add pyqtconfig widget handlers
        bind_pyqtconfig_handlers(self)

    def getSelection(self):
        """ Check spreadsheet selection is accessible.
        """
        try:
            wb, ws, address, range = get_xl_selection()
            self.workbookEntry.setText(wb)
            self.worksheetEntry.setText(ws)
            self.addressEntry.setText(address)
        except XlError:
            msg = 'Unable able to find data selection in an open Excel ' \
                  'workbook. This may mean that no cells have been ' \
                  'selected or it may be the result of a permissions error.'
            self.showErrorDialog("Error getting spreadsheet error.",
                     informative_text=msg)

    def okEvent(self):
        """ When OK is clicked, check data and call accept() if all good, or
        else show error and call reject().
        """
        try:
            # If no selection has been made, then return.
            if any([x in ("", None) for x in (self.workbookEntry.text(),
                    self.worksheetEntry.text(), self.addressEntry.text())]):
                msg = 'Selection fields cannot be left blank.'
                self.showErrorDialog("Problem with spreadsheet data selection",
                                    informative_text=msg)
                raise XlError

            # Check excel app is open
            if xw.apps.count < 1:
                msg = 'No open instances of Excel could be found.'
                self.showErrorDialog("Problem with spreadsheet data selection",
                                     informative_text=msg)
                raise XlError

            if xw.books.count < 1 or self.workbookEntry.text() not in \
                    [x.fullname for x in xw.books] + [x.name for x in xw.books]:
                msg = f'Could not find open workbook: {self.workbookEntry.text()}.'
                self.showErrorDialog("Problem with spreadsheet data selection",
                            informative_text=msg)
                raise XlError

            if self.worksheetEntry.text() not in \
                    [x.name for x in xw.Book(self.workbookEntry.text()).sheets]:
                self.showErrorDialog(
                    "Problem with spreadsheet data selection",
                    informative_text=f'Could not find sheet named '
                    f'{self.worksheetEntry.text()} in workbook: '
                    f'{self.workbookEntry.text()}.')
                raise XlError

            # Read data from spreadsheet
            try:
                self.range = xw.Book(self.workbookEntry.text())\
                                .sheets[self.worksheetEntry.text()]\
                                .range(self.addressEntry.text())
            except:
                msg = ('Ensure field entries are correct, and that the workbook is open, '
                    'is not being used by another program, and is not passwored protected.')
                self.showErrorDialog("Problem with spreadsheet data selection", informative_text=msg)
            else:
                shape = self.range.shape
                if shape != (self.n, 2):
                    msg = (f'Mismatch between the number of data points '
                           f'and the shape of the selected range. The selection '
                           f'should be ({self.n} x 2), with uncertainties '
                           f'(1\u03C3 abs.) in the second column.')
                    self.showErrorDialog("Problem with spreadsheet data selection",
                                         informative_text=msg)
                    return

        except XlError:
            pass

        else:
            # update local attributes:
            self.wb = self.workbookEntry.text()
            self.ws = self.worksheetEntry.text()
            self.address = self.addressEntry.text()
            self.accept()

    def closeEvent(self, event):
        # save settings?
        self.reject()
        self.parent.show()

    def showErrorDialog(self, text, informative_text=None,
                        icon=QMessageBox.Warning):
        # Show error dialog
        self.dialog = QMessageBox(parent=self, text=text, icon=icon)
        self.dialog.setInformativeText(informative_text)
        self.dialog.setStandardButtons(QMessageBox.Ok)
        self.dialog.exec()

    def setDefault(self, default):
        # Set defaults.
        try:
            rng = default
        except:
            logger.debug('could not set default range for refedit dialog')
        else:
            self.workbookEntry.setText(rng.sheet.book.fullname)
            self.worksheetEntry.setText(rng.sheet.name)
            self.addressEntry.setText(rng.address)


# =============================================================================
# Forced concordance dialog
# =============================================================================

class FcDataDialog(QDialog):
    def __init__(self, parent):
        super(FcDataDialog, self).__init__(parent)
        self.parent = parent

        # Range used for setting default output address.
        self.iso86_workbook = None
        self.iso86_worksheet = None
        self.iso86_address = None
        self.iso86_range = None
        self.iso86_dp = None

        self.iso57_workbook = None
        self.iso57_worksheet = None
        self.iso57_address = None
        self.iso57_range = None
        self.iso57_dp = None

        uiPath = os.path.join("uis", "forced_concordance_dialog.ui")
        loadUi(resourceAbsolutePath(uiPath), baseinstance=self, package="dqpb")

        # Add commands to buttons.
        self.okButton.clicked.connect(self.okEvent)
        self.cancelButton.clicked.connect(self.reject)
        self.getSelectionButton.clicked.connect(self.getSelection)

        # Populate combo boxes.
        self.iso86FitCombo.addItems(REGRESSION_FITS)
        self.iso57FitCombo.addItems(REGRESSION_FITS)
        # self.normPbCombo.addItems(["204Pb", "208Pb"])

    def okEvent(self):

        for w in (self.iso86WorkbookEntry,
                  self.iso86WorksheetEntry, self.iso86AddressEntry,
                  self.iso57WorksheetEntry, self.iso57WorkbookEntry,
                  self.iso57AddressEntry):

            if w.text() in (None, ""):
                self.showErrorDialog(
                    "Problem with spreadsheet data selection",
                    informative_text='Selection field cannot be left blank.')
                return

        # Check excel app is open
        if xw.apps.count < 1:
            self.showErrorDialog(
                "Problem with spreadsheet data selection",
                informative_text='No open instances of Excel could be found.')
            return

        if xw.books.count < 1:
            self.showErrorDialog(
                "Problem with spreadsheet data selection",
                informative_text='No open Excel workbooks could be found.')
            return

        for diagram in ('iso86', 'iso57'):

            if getattr(self, f'{diagram}WorkbookEntry').text() not \
                in [x.fullname for x in xw.books] + [x.name for x in xw.books]:

                self.showErrorDialog(
                    "Problem with spreadsheet data selection",
                    informative_text=f'Could not find open workbook: '
                                     f'{self.workbookEntry.text()}.')
                return

            if getattr(self, f'{diagram}WorksheetEntry').text() not in \
                [x.name for x in
                 xw.Book(getattr(self, f'{diagram}WorkbookEntry').text())\
                 .sheets]:

                self.showErrorDialog(
                    "Problem with spreadsheet data selection",
                    informative_text=f'Could not find sheet named '
                    f'{self.worksheetEntry.text()} in workbook: '
                    f'{self.workbookEntry.text()}.')
                return

            # Double check workbook connection
            try:
                range_ = xw.Book(getattr(self, f'{diagram}WorkbookEntry').text())\
                    .sheets[getattr(self, f'{diagram}WorksheetEntry').text()]\
                    .range(getattr(self, f'{diagram}AddressEntry').text())
                setattr(self, f'{diagram}_dp', range_.value)
            except:
                self.showErrorDialog(
                    "Problem with spreadsheet data selection",
                    informative_text='Error reading Excel address. Ensure '
                    'field entries are correct and that the workbook is open, and '
                    'not being used by another program nor passwored protected.')
                self.reject()
            else:
                # updata local attr
                setattr(self, f'{diagram}_workbook',
                        getattr(self, f'{diagram}WorkbookEntry').text())
                setattr(self, f'{diagram}_worksheet',
                        getattr(self, f'{diagram}WorksheetEntry').text())
                setattr(self, f'{diagram}_address',
                        getattr(self, f'{diagram}AddressEntry').text())
                setattr(self, f'{diagram}_range', range_)

        self.accept()

    def getSelection(self):
        """
        Data selection is done with one tabWidget tab open at a time.
        """
        tabWidgetTabs = ["iso86", "iso57"]
        diagram = tabWidgetTabs[self.tabWidget.currentIndex()]

        try:
            wb, ws, address, range = get_xl_selection()

            if diagram == "iso86":
                self.iso86WorkbookEntry.setText(wb)
                self.iso86WorksheetEntry.setText(ws)
                self.iso86AddressEntry.setText(address)
            elif diagram == "iso57":
                self.iso57WorkbookEntry.setText(wb)
                self.iso57WorksheetEntry.setText(ws)
                self.iso57AddressEntry.setText(address)

        except XlError:
            self.showErrorDialog("Spreadsheet data selection error.",
                                 informative_text='Unable able to find data '
                                                  'selection in an open Excel workbook.')
            return

        setattr(self, f"{diagram}_workbook", wb)
        setattr(self, f"{diagram}_worksheet", ws)
        setattr(self, f"{diagram}_address", address)

    def showErrorDialog(self, text, informative_text=None,
                        icon=QMessageBox.Warning):
        self.hide()
        dialog = QMessageBox(text=text, icon=icon)
        if informative_text is not None:
            dialog.setInformativeText(informative_text)
        dialog.setStandardButtons(QMessageBox.Ok)
        dialog.exec()
        self.reject()


# =============================================================================
# About dialog
# =============================================================================

class AboutDialog(QDialog):
    def __init__(self, parent):
        super(AboutDialog, self).__init__(parent)

        uiPath = os.path.join("uis", "about.ui")
        loadUi(resourceAbsolutePath(uiPath), baseinstance=self, package="dqpb")

        self.nameLabel.setText(f"DQPB {version}")
        # self.iconLabel.setPixmap(QPixmap(self.parent().iconPath))

        docsUrl = "See online <a href=\"https://timpol.github.io/DQPB/\"> documentation </a>"
        self.docsLabel.setText(docsUrl)
        self.docsLabel.setOpenExternalLinks(True)


# =============================================================================
# Axis limits / label dialogs
# =============================================================================

class AxisLabelsDialog(QDialog):
    """
    Dialog for entering user specified axis labels.
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        self.parent = parent
        self.x_label = None
        self.y_label = None

        uiPath = os.path.join("uis", "axis_labels.ui")
        loadUi(resourceAbsolutePath(uiPath), baseinstance=self, package="dqpb")

        # Add commands to buttons.
        self.okButton.clicked.connect(self.okEvent)
        self.cancelButton.clicked.connect(self.reject)

    def okEvent(self):
        self.x_label = self.xLabelEntry.text()
        self.y_label = self.yLabelEntry.text()
        self.accept()


class AxisLimsDialog(QDialog):
    """
    User inputs will be retained for session but not stored in settings file.
    """
    axis_widgets = {
        'dpp_xmin': 'dpXminEntry',
        'dpp_xmax': 'dpXmaxEntry',
        'dpp_ymin': 'dpYminEntry',
        'dpp_ymax': 'dpYmaxEntry',
        'int_xmin': 'intXminEntry',
        'int_xmax': 'intXmaxEntry',
        'int_ymin': 'intYminEntry',
        'int_ymax': 'intYmaxEntry',
        'wav_ymin': 'wavYMinEntry',
        'wav_ymax': 'wavYMaxEntry'
    }

    def __init__(self, parent=None):
        super(AxisLimsDialog, self).__init__(parent)
        self.parent = parent

        uiPath = os.path.join("uis", "axis_lims.ui")
        loadUi(resourceAbsolutePath(uiPath), baseinstance=self, package="dqpb")

        # Add commands to buttons.
        self.okButton.clicked.connect(self.okEvent)
        self.cancelButton.clicked.connect(self.reject)

        # Set defaults to empty string. This will be converted to None later.
        for v in self.axis_widgets.keys():
            setattr(self, v, '')

    def okEvent(self):
        for k, v in self.axis_widgets.items():
            w = getattr(self, v)
            setattr(self, k, w.text())
        self.accept()


class CommonPb76Dialog(QDialog):
    """
    Dialog for entering user specified axis labels.
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        self.parent = parent
        self.Pb76 = None
        self.Pb76_1s = None

        uiPath = os.path.join("uis", "common_pb76_dialog.ui")
        loadUi(resourceAbsolutePath(uiPath), baseinstance=self, package="dqpb")

        # Add commands to buttons.
        self.okButton.clicked.connect(self.okEvent)
        self.cancelButton.clicked.connect(self.reject)

        bind_pyqtconfig_handlers(self)

    def okEvent(self):
        # TODO: perform check on entered values:
        self.Pb76 = self.Pb76Entry.text()
        self.Pb76_1s = self.Pb76ErrEntry.text()
        self.accept()


# =============================================================================
# Error log dialog
# =============================================================================

class LogDialog(QMainWindow):

    font_color_map = {
        'CRITICAL': QColor('red'),
        'ERROR': QColor('red'),
        'WARNING': QColor('orange'),
        'INFO': QColor('black'),
        'DEBUG': QColor('grey')
    }

    log_levels = ['Debug', 'Info', 'Warning']

    def __init__(self, parent):
        super().__init__(parent=parent)

        uiPath = os.path.join("uis", "log_console.ui")
        loadUi(resourceAbsolutePath(uiPath), baseinstance=self, package="dqpb.gui")
        self.parent = parent

        # Setup widgets.
        self.loggerWidget.setFont(util.fixedFont())
        # self.loggerWidget.setLineWrapMode(QPlainTextEdit.NoWrap)
        self.hideButton.clicked.connect(self.hide)
        self.logLevelCombo.addItems(self.log_levels)
        self.logLevelCombo.currentIndexChanged.connect(self.levelChange)

        GUI_SETTINGS.add_handler('log_level', self.logLevelCombo)

    def updateLogger(self, data):
        # self.loggerWidget.appendPlainText(data)
        level, message = data.split("::")
        self.loggerWidget.setTextColor(self.font_color_map[level])
        self.loggerWidget.append(message)
        self.loggerWidget.moveCursor(QTextCursor.End)

    def levelChange(self):
        if self.logLevelCombo.currentText() == 'Debug':
            self.parent.setConsoleLogLevel(logging.DEBUG)
            logger.debug('Console log level set to debug - verbose log messages '
                         'will be displayed.')
        elif self.logLevelCombo.currentText() == 'Info':
            self.parent.setConsoleLogLevel(logging.INFO)
            logger.info('Console log level set to INFO - important log messages '
                        'and warnings will be displayed.')
        elif self.logLevelCombo.currentText() == 'Warning':
            self.parent.setConsoleLogLevel(logging.WARNING)
            logger.warning('Console log level set to WARNING - only warnings '
                           'and errors will be displayed.')


# =============================================================================
# Error dialogs
# =============================================================================

class ErrorDialog(QMessageBox):
    def __init__(self, text, icon_type=QMessageBox.Warning,
                 title="DQPB warning"):
        super().__init__()
        self.setIcon(icon_type)
        self.setText(text)
        self.setWindowTitle(title)
        self.setStandardButtons(QMessageBox.Ok)

    def closeEvent(self, event):
        self.reject()


class TaskErrorDialog(ErrorDialog):
    def __init__(self, text="DQPB encountered an error"):
        super().__init__(text, icon_type=QMessageBox.Critical)
        # Would be good to add a button to show log here...


# =============================================================================
# Preferences window
# =============================================================================

class PreferencesWindow(QMainWindow):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent

        uiPath = os.path.join("uis", "Preferences.ui")
        loadUi(resourceAbsolutePath(uiPath), baseinstance=self, package="dqpb")

        self.setWindowTitle('Preferences')

        # Connect main buttons
        self.okButton.clicked.connect(self.hide)
        self.resetButton.clicked.connect(self.parent.resetSettings)
        self.dirSelectButton.clicked.connect(self.getOutputDirectory)
        self.cellColorSelectButton.clicked.connect(self.getCellColor)

        # Populate combo boxes.
        self.figFileTypeCombo.addItems(get_mpl_filetypes())
        self.spreadsheetFontCombo.addItems(['none'] + get_mpl_fonts()[0])

        # Add pyqtconfig widget handlers
        bind_pyqtconfig_handlers(self)

    def getCellColor(self):
        # TODO: set initial color
        col = QColorDialog.getColor()
        self.cellColorEntry.setText(col.name())

    def getOutputDirectory(self):
        # TODO: set initial dir
        dir = QFileDialog.getExistingDirectory()
        self.figDirEntry.setText(dir)

        # TODO: is this necessary with pyqtconfig??
        self.fig_exp_dir = dir
        # Set data point range


# =============================================================================
# Plot settings windows
# =============================================================================

class PlotSettingsWindow(QMainWindow):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent

        uiPath = os.path.join("uis", "plot_specific_settings.ui")
        loadUi(resourceAbsolutePath(uiPath), baseinstance=self, package="dqpb")

        self.doneButton.clicked.connect(self.doneEvent)
        # self.resetButton.clicked.connect(self.resetEvent)

        # populate combo boxes
        self.dppAgePrefixCombo.addItems(['Ma', 'ka'])
        self.intAgePrefixCombo.addItems(['Ma', 'ka'])
        self.wavAgePrefixCombo.addItems(['ka', 'Ma'])

        # Add pyqtconfig widget handlers
        bind_pyqtconfig_handlers(self)

    def doneEvent(self):
        self.hide()

    def resetEvent(self):
        # code this
        return


class PlotFormatWindow(QMainWindow):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent

        uiPath = os.path.join("uis", "plot_formating.ui")
        loadUi(resourceAbsolutePath(uiPath), baseinstance=self, package="dqpb")
        self.setWindowTitle("Plot Format Settings")
        self.font_names, self.font_families = get_mpl_fonts()

        self.doneButton.clicked.connect(self.doneEvent)
        self.resetButton.clicked.connect(self.parent.resetSettings)

        # Populate combo boxes
        for k, v in self.__dict__.items():
            k = k.lower()
            if 'color' in k and 'combo' in k:
                v.addItems(get_all_colors())
            elif 'marker' in k and 'type' in k and 'combo' in k:
                v.addItems(get_mpl_markers())
            elif 'line' in k and 'style' in k:
                v.addItems(get_mpl_linestyles())
            elif 'marker' in k and 'type' in k:
                v.addItems(get_mpl_markers())
            elif 'font' in k and 'size' in k and 'combo' in k:
                v.addItems(FONT_SIZES)
                v.setValidator(QIntValidator(0,100))
            elif 'direction' in k and 'combo' in k:
                v.addItems(MPL_TICK_DIRECTIONS)
            elif 'valignment' in k and 'combo' in k:
                v.addItems(MPL_V_ALIGNMENTS)
            elif 'halignment' in k and 'combo' in k:
                v.addItems(MPL_H_ALIGNMENTS)
            elif 'textcoord' in k and 'combo' in k:
                v.addItems(['offset points'])
                v.setCurrentText('offset points')
            elif 'xyoffset' in k and 'entry' in k:
                v.setInputMask('(#09,#09)')

        # Populate font combo box
        self.fontCombo.addItems(self.font_names)

        # Set table header labels
        self.dictTable.setHorizontalHeaderLabels(
            ['Dictionary name', 'Key', 'Value'])

        # Other combo boxes
        self.fontWeightCombo.addItems(['Normal'])
        self.histogramHistTypeCombo.addItems(MPL_HISTTYPES)
        # self.concLabelTextCoordsCombo.addItems(['offset points'])

        # Add pyqtconfig widget handlers
        bind_pyqtconfig_handlers(self)


    def doneEvent(self):
        # store user inputted colors for future use
        for k, v in self.__dict__.items():
            k = k.lower()
            if 'color' in k and 'combo' in k:
                c = v.currentText()
                add_user_color(c)

                # add to all color combo boxes
                for l, w in self.__dict__.items():
                    l = l.lower()
                    if 'color' in l and 'combo' in l:
                        w.addItems(get_all_colors())

                v.setCurrentText(c)

        self.hide()


# =============================================================================
# Bind settings in config to pyqt widgets
# =============================================================================

def bind_pyqtconfig_handlers(obj):
    """ """
    for k in config.GuiSettingsMap.keys():
        w = config.GuiSettingsMap[k]["widget"]

        if w in obj.__dict__.keys():

            if 'marker' in w.lower() and 'type' in w.lower() and 'combo' in \
                w.lower():
                GUI_SETTINGS.add_handler(k, getattr(obj, w),
                                          mapper=mpl_marker_type_map())
            else:
                GUI_SETTINGS.add_handler(k, getattr(obj, w))


# =============================================================================
# mpl options
# =============================================================================

def add_user_color(c):
    """
    """
    # Check if color is valid
    rgb = matplotlib.colors.to_rgb(c)
    if rgb is None:
        warnings.warn(f"color '{c}' appears invalid and was not stored for future use")
        return
    # Add to user colors if not already there
    user_colors = GUI_SETTINGS.get('user_colors')
    if c not in get_all_colors():
        user_colors.append(c)
    GUI_SETTINGS.set('user_colors', user_colors)


def get_all_colors():
    """
    Return list of all colors.
    """
    mpl_colors = get_mpl_colors()
    user_colors = GUI_SETTINGS.get('user_colors')
    return mpl_colors + user_colors


def get_mpl_colors():
    """
    Return list of named matplotlib colors.
    """
    return ['none'] + list(matplotlib.colors.BASE_COLORS.keys()) \
                          + list(matplotlib.colors.CSS4_COLORS.keys())


def get_mpl_markers():
    """
    """
    names = list(matplotlib.lines.Line2D.markers.values())
    names = [n for n in names if n != 'nothing']
    return ["None"] + names


def mpl_marker_type_map():
    return {v: k for (k, v) in matplotlib.lines.Line2D.markers.items()}


def get_mpl_linestyles():
    """
    """
    lines = []
    for k, v in matplotlib.lines.Line2D.lineStyles.items():
        if v != '_draw_nothing':
            lines.append(k)
    return ["None"] + lines


def get_mpl_filetypes():
    """
    """
    return list(plt.gcf().canvas.get_supported_filetypes().keys())


def get_mpl_fonts():
    """
    """
    available_fonts = []
    available_font_families = {}
    file_list = matplotlib.font_manager.findSystemFonts()

    for file in file_list:
        try:
            fp = matplotlib.font_manager.FontProperties(fname=file)
            name = fp.get_name()
            family = fp.get_family()[0]
        except RuntimeError:
            pass
        else:
            if not name.startswith("."):
                available_fonts.append(name)
                available_font_families[name] = family
    available_fonts = list(set(available_fonts))
    available_fonts.sort()
    return available_fonts, available_font_families
