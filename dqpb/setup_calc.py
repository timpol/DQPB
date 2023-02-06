"""
Prepare and run plotting and calculation tasks.

"""

import time
import logging
import xlwings as xw
import matplotlib as mpl

from dqpb import combo
from dqpb import calcs
from dqpb import spreadsheet


logging.getLogger("matplotlib").setLevel(logging.INFO)
logger = logging.getLogger("dqpb.tasks")


class Task:
    """
    Setup and run a calculation.
    """

    def __init__(self, task_obj,  msg_signal, progress_signal, ret_signal):

        # Dump all settings to log (only displayed in console if set to debug).
        # for k, v in task_obj.items():
        #     logger.debug(f'{k}: {v}')
        
        self.__dict__ = task_obj  # set all task dict items to instance attributes
        self.msg_signal = msg_signal
        self.progress_signal = progress_signal
        self.ret_signal = ret_signal
        self.retval = ''

        logger.info(f'running: {self.task}')

        self.task = combo.SHORT_TASK_NAMES[task_obj["task"]]
        self.data_type = combo.SHORT_DATA_TYPES[task_obj["data_type"]]
        self.fit = combo.SHORT_FITS[task_obj['fit']]

        # connect to workbook
        logger.debug("connecting to workbook...")
        self.wb = xw.Book(self.output_workbook)
        self.ws = self.wb.sheets[self.output_worksheet]
        self.output_range = self.ws.range(self.output_address)
        self.app = self.wb.app

        # set up spreadsheet printer for handling results
        logger.debug("initialising spreadsheet printer...")
        self.printer = spreadsheet.SpreadSheetPrinter(
            self.ws,
            self.output_range.resize(1, 1),
            xl_fig_height=self.xl_fig_height,
            embolden=self.xl_bold_headings,
            apply_font=True,
            apply_number_formats=self.xl_number_formats,
            font=self.xl_font,
            clear_cells=self.clear_xl,
            cell_color=self.xl_cell_color,
            apply_cell_color=self.apply_xl_cell_colors
        )

        # read settings file
        logger.debug("setting DQPB config...")
        calcs.set_dqpb_config(self)

        # Reset maplotlib defaults just in case. Then set font family and
        # preferred fonts.
        mpl.rcParams.update(mpl.rcParamsDefault)
        preferred_fonts = mpl.rcParams[f'font.{self.font_family}']
        preferred_fonts.insert(0, self.font)
        mpl.rcParams[f'font.{self.font_family}'] = preferred_fonts
        mpl.rcParams['font.family'] = self.font_family

        # Set mpl savefig settings.
        mpl.rcParams["savefig.format"] = self.fig_extension
        mpl.rcParams["savefig.dpi"] = 300

        # log plotting font to be used
        # Log actual font to be used. Note: matplotlib doesn't like the
        # '-', so use alias 'sans serif' instead.
        try:
            font = mpl.font_manager.findfont(
                mpl.font_manager.FontProperties(family=[self.font_family]))
            logger.debug(f'plot font set to: {font}')
        except:
            logger.debug('unable to get matplotlib font...')

        # some additional derived settings etc.
        self.concordia_intercept = False
        if self.task == 'concordia_intercept_age':
            self.concordia_intercept = True

        if self.eq_guess:
            self.age_guess = 'eq'

        # uncertainty propagation approach
        if self.mc_uncert:
            self.uncert = 'mc'
        else:
            self.uncert = 'analytical'

        self.error_type = self.error_type + str(self.sigma_level) + "s"

        self.init = [True, True]
        self.init[0] = True if self.A48_type == 'initial' else False
        self.init[1] = True if self.A08_type == 'initial' else False


    def update_progress(self, val, msg):
        """Update gui progress bar.
        """
        self.msg_signal.emit(msg)
        self.progress_signal.emit(val)

    def run(self):
        """
        Run dqpb SpreadSheet task and catch any exceptions for display
        in GUI.
        """
        assert self.task in ('concordia_intercept_age', 'isochron_age',
                        'plot_data', 'pbu_age', 'wtd_average',
                        'forced_concordance')
        start = time.perf_counter()
        try:
            # call task
            if self.task in ('concordia_intercept_age', 'isochron_age'):
                calcs.diagram_age(self)
            elif self.task == 'plot_data':
                calcs.plot_data(self)
            elif self.task == 'pbu_age':
                calcs.pbu_age(self)
            elif self.task == 'wtd_average':
                calcs.wav_other(self)
            elif self.task == 'forced_concordance':
                calcs.forced_concordance(self)

            finish = time.perf_counter()
            logger.debug(f"{self.task} finished in "
                         f"{round(finish - start, 2)} seconds")
        except:
            try:
                self.printer.flush_stack()
            except:
                self.clean_up_xl()
                # raise printing error as well:
                raise
            self.ret_signal.emit(self.retval)
            raise
        else:
            self.clean_up_xl()
            # self.retval += 'text|informative text::'
            self.ret_signal.emit(self.retval)

    def clean_up_xl(self):
        self.app.screen_updating = True

