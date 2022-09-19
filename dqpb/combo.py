"""
Application combo box data.

"""

MPL_V_ALIGNMENTS = ['center', 'top', 'bottom', 'baseline', 'center_baseline']
MPL_H_ALIGNMENTS = ['center', 'left', 'right']
MPL_TICK_DIRECTIONS = ['in', 'out', 'inout']
MPL_HISTTYPES = ['bar', 'barstacked', 'step', 'stepfilled']
AGE_PREFIXES = ['ka', 'Ma']
FONT_SIZES = ['6', '7', '8', '9', '10', '11', '12', '13', '14', '15', '16',
              '18', '20', '22', '24', '26', '28', '30', '36', '48', '72']

# TODO: move this to config?
DP_ERROR_WARNING_THRESHOLD = 0.5

PBU_EQUATION_TYPES = [
    "Ludwig",
    "Sakata / Guillong"]

# task options map
TASKS = {"Concordia-intercept age": {
    "fit": "regression",
    "series": "both",
    "age": True,
    "data_types": ["Tera-Wasserburg"]
    },
    "U-Pb isochron age": {
        "fit": "regression",
        "series": "238U",
        "age": True,
        "data_types": ["238U-206Pb", "235U-207Pb"]
    },
    "Pb/U ages": {
        "fit": "wtm",
        "series": "both",
        "age": True,
        "data_types": ["206Pb/238U", "207Pb/235U", "Mod. 207Pb"]
    },
    "Concordant [234U/238U]i": {
        "fit": "regression",
        "series": "both",
        "age": True,
        "data_types": ["multiple"]
    },
    "Plot x-y data": {
        "fit": "regression",
        "series": "both",
        "age": False,
        "data_types": ["other x-y",
                       "Tera-Wasserburg"]
    },
    "Weighted average": {
        "fit": "wtm",
        "series": "both",
        "age": False,
        "data_types": ["other"]
    }
}

AGE_FULLNAMES = {'tw': 'Tera-Wasserburg',
                 'iso-Pb6U8': '206Pb/238U isochron',
                 'iso-Pb7U5': '207Pb/235U isochron'}


SHORT_TASK_NAMES = {
    "Concordia-intercept age": "concordia_intercept_age",
    "U-Pb isochron age": "isochron_age",
    "Pb/U ages": "pbu_age",
    "Concordant [234U/238U]i": "forced_concordance",
    "Plot x-y data": "plot_data",
    "Weighted average": "wtd_average"}
SHORT_DATA_TYPES = {
    "Tera-Wasserburg": "tw",
    "238U-206Pb": "iso-Pb6U8",
    "235U-207Pb": "iso-Pb7U5",
    "206Pb/238U": "Pb6U8",
    "207Pb/235U": "Pb7U5",
    "Mod. 207Pb": "mod-207Pb",
    "other x-y": "other_xy",
    "other": "other",
    "multiple": None,
    "covariance matrix": "covmat"}
SHORT_FITS = {
    # "robust": "ra",
    "Robust model 2": "r2",
    "Spine": "rs",
    # "Spine x": "rx",
    "classical": "ca",
    "Model 1": "c1",
    "Model 2": "c2",
    "Model 3": "c3",
    # "classical wav.": "ca",
    # "Spine wav.": "rs",
    "no fit": None}
REGRESSION_FITS = [
    # "robust",
    "Spine",
    "classical",
    "Robust model 2",
    "Model 1",
    "Model 2",
    "Model 3"
]
WAV_FITS = [
    "Spine",
    "classical"
    # "Spine wav.",
    # "classical wav."
]    # 'none' added later where relevant

# Invert combo box data
LONG_FITS = dict((v, k) for k, v in SHORT_FITS.items())
LONG_TASK_NAMES = dict((v, k) for k, v in SHORT_TASK_NAMES.items())
LONG_DATA_TYPES = dict((v, k) for k, v in SHORT_DATA_TYPES.items())
