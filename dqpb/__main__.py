"""
Main entry point for application

"""

import os
import sys
import logging

from PyQt5.QtWidgets import QApplication

from dqpb.gui import GUI_SETTINGS, MainWindow
from dqpb.loggers import setUpLoggers

logger = logging.getLogger("dqpb.app")


def main():
    """
    Launch application.
    """
    app = QApplication([])

    # For now, log file is written to the same directory as the settings file.
    settings_file_path = os.path.abspath(
        os.path.dirname(GUI_SETTINGS.settings.fileName()))
    setUpLoggers(log_file_path=settings_file_path)

    window = MainWindow()
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
