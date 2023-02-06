"""
Saving and loading user-adjustable settings.

"""

import logging

from dqpb import version
from dqpb.pyqtconfig import QSettingsManager


logger = logging.getLogger("dqpb.config")


# GUI settings map for assigning widget values to python variables and vice
# versa.
# Note: all default values must be of type bool or string.
GuiSettingsMap = {
    'one_sigma':               {'default': True,       'widget': 'err1sOpt'},
    'two_sigma':               {'default': False,      'widget': 'err2sOpt'},
    'mc_uncert':               {'default': True,       'widget': 'mcUncertOpt'},
    'an_uncert':               {'default': False,      'widget': 'anUncertOpt'},
    'task':                    {'default': 'Concordia-intercept age',
                                                       'widget': 'taskCombo'},
    'data_type':               {'default': 'Tera-Wasserburg',
                                                       'widget': 'dataTypeCombo'},
    'fit':                     {'default': 'robust',   'widget': 'fitCombo'},
    'error_type':              {'default': 'abs.',     'widget': 'errTypeCombo'},
    'age_guess':               {'default': '1.00',     'widget': 'ageGuessEntry'},
    'eq_guess':                {'default': True,       'widget': 'eqGuessOpt'},
    'output_eq_age':           {'default': False,      'widget': 'outputEqOpt'},
    'mc_summary':              {'default': False,      'widget': 'McSummaryOpt'},
    'dc_errors':               {'default': False,      'widget': 'dcErrOpt'},
    'u_errors':                {'default': False,      'widget': 'uratErrOpt'},
    'mc_rnages':               {'default': True,       'widget': 'rnAgesOpt'},
    'mc_rnar':                 {'default': True,       'widget': 'rnArvOpt'},
    'mc_trials':               {'default': '50000',    'widget': 'nTrialsEntry'},
    'age_hist':                {'default': False,      'widget': 'ageHistOpt'},
    'ratio_hist':                 {'default': False,      'widget': 'arHistOpt'},
    'input_cov':               {'default': False,      'widget': 'covOpt'},
    'norm_isotope':            {'default': '204Pb',    'widget': 'normPbCombo'},
    'ThU_min_type':            {'default': '232Th/238U', 'widget': 'ThUminCombo'},

    'A48':                     {'default': '1.0',      'widget': 'A48Entry'},
    'A48_err':                 {'default': '0.0',      'widget': 'A48ErrEntry'},
    'A48_type':                {'default': 'initial',  'widget': 'A48Combo'},
    'A08':                     {'default': '1.0',      'widget': 'A08Entry'},
    'A08_err':                 {'default': '0.0',      'widget': 'A08ErrEntry'},
    'A08_type':                {'default': 'initial',  'widget': 'A08Combo'},
    'A68':                     {'default': '1.0',      'widget': 'A68Entry'},
    'A68_err':                 {'default': '0.0',      'widget': 'A68ErrEntry'},
    'A15':                     {'default': '1.0',      'widget': 'A15Entry'},
    'A15_err':                 {'default': '0.0',      'widget': 'A15ErrEntry'},
    'eq':                      {'default': False,      'widget': 'initialEqOpt'},

    'font':                    {'default': 'Arial',    'widget': 'fontCombo'},
    'font_weight':             {'default': 'normal',   'widget': 'fontWeightCombo'},
    'fig_export_dir':          {'default': '',         'widget': 'figDirEntry'},
    'fig_extension':           {'default': 'pdf',      'widget': 'figFileTypeCombo'},
    'fig_background_color':    {'default': 'white',    'widget': 'figBackgroundColorCombo'},
    'fig_border_color':        {'default': 'white',    'widget': 'figBorderColorCombo'},
    'xl_font':                 {'default': 'none',     'widget': 'spreadsheetFontCombo'},
    'xl_bold_headings':        {'default': False,      'widget': 'spreadsheetBoldOpt'},
    'xl_number_formats':       {'default': True,       'widget': 'spreadsheetNumberFormatOpt'},
    'clear_xl':                {'default': False,      'widget': 'spreadsheetClearOpt'},
    'apply_xl_cell_colors':    {'default': False,      'widget': 'cellColorOpt'},
    'xl_cell_color':           {'default': 'none',     'widget': 'cellColorEntry'},
    'xl_fig_height':           {'default': '20',       'widget': 'spreadsheetFigHeightEntry'},
    'log_level':               {'default': 'Info',     'widget': 'logLevelCombo'},

    'Pb76':                    {'default': '',         'widget': 'Pb76Entry'},
    'Pb76_1s':                 {'default': '',         'widget': 'Pb76ErrEntry'},
    'show_int_plot':           {'default': True,       'widget': 'showInterceptPlotOpt'},
    'show_wav_plot':           {'default': True,       'widget': 'showWavPlotOpt'},
    'wav_cov':                 {'default': True,       'widget': 'wavCovOpt'},
    'conc_intercept_ellipse':  {'default': False,       'widget': 'interceptEllipseOpt'},
    'conc_intercept_points':   {'default': True,      'widget': 'interceptMarkersOpt'},
    'dp_plot':                 {'default': True,       'widget': 'showXyPlotOpt'},
    'mod207_projection':       {'default': True,       'widget': 'mod207ProjectionLineOpt'},
    'autoscale':               {'default': True,       'widget': 'autoscaleOpt'},
    'save_plots':              {'default': False,      'widget': 'savePlotsOpt'},
    'output_plot_data':        {'default': False,      'widget': 'plotDataOpt'},
    'print_opts':              {'default': False,      'widget': 'printSettingsOpt'},
    'show_dp_labels':          {'default': False,      'widget': 'dpLabelOpt'},

    'concint_age_min':         {'default': '0.0',    'widget': 'concintMinAgeEntry'},
    'concint_age_max':         {'default': '20.0',   'widget': 'concintMaxAgeEntry'},
    'concint_A48i_min':        {'default': '0.0',    'widget': 'concintMinA48iEntry'},
    'concint_A48i_max':        {'default': '20.0',   'widget': 'concintMaxA48iEntry'},
    'concint_A08i_min':        {'default': '0.0',    'widget': 'concintMinA08iEntry'},
    'concint_A08i_max':        {'default': '20.0',   'widget': 'concintMaxA08iEntry'},

    'eq_conc_min_age':         {'default': '0.001',  'widget': 'eqConcMinAgeEntry'},
    'eq_conc_max_age':         {'default': '4600.0', 'widget': 'eqConcMaxAgeEntry'},
    'dq_conc_min_age_1':       {'default': '0.001',  'widget': 'dqConcMinAge1Entry'},
    'dq_conc_max_age_1':       {'default': '100.0',  'widget': 'dqConcMaxAge1Entry'},
    'dq_conc_min_age_2':       {'default': '0.001',  'widget': 'dqConcMinAge2Entry'},
    'dq_conc_max_age_2':       {'default': '2.5',    'widget': 'dqConcMaxAge2Entry'},
    'dq_conc_min_age_3':       {'default': '0.001',  'widget': 'dqConcMinAge3Entry'},
    'dq_conc_max_age_3':       {'default': '1.5',    'widget': 'dqConcMaxAge3Entry'},

    'rng_seed':                {'default': '',         'widget': 'rngSeedEntry'},
    'mswd_lim_lower':          {'default': '0.85',     'widget': 'mswdLowerEntry'},
    'mswd_lim_upper':          {'default': '0.95',     'widget': 'mswdUpperEntry'},
    'wav_mswd_lim_lower':      {'default': '0.85',     'widget': 'wtaMswdLowerEntry'},
    'wav_mswd_lim_upper':      {'default': '0.95',     'widget': 'wtaMswdUpperEntry'},
    'secular_eq':              {'default': True,       'widget': 'secularEqOpt'},
    'spines_h':                {'default': '1.4',      'widget': 'spinesHEntry'},

    'U':                       {'default': '137.818',       'widget': 'uRatEntry'},
    'sU':                      {'default': '0.0225',        'widget': 'uRatErrEntry'},
    'lam238':                  {'default': '1.5512548e-10', 'widget': 'dc238Entry'},
    'lam234':                  {'default': '2.8220307e-06', 'widget': 'dc234Entry'},
    'lam230':                  {'default': '9.170554e-06',  'widget': 'dc230Entry'},
    'lam226':                  {'default': '4.3321e-04',    'widget': 'dc226Entry'},
    'lam235':                  {'default': '9.8484986e-10', 'widget': 'dc235Entry'},
    'lam231':                  {'default': '2.115511e-05',  'widget': 'dc231Entry'},
    's238':                    {'default': '8.33e-14',      'widget': 'dc238ErrEntry'},
    's234':                    {'default': '1.49e-09',      'widget': 'dc234ErrEntry'},
    's230':                    {'default': '6.67e-09',      'widget': 'dc230ErrEntry'},
    's226':                    {'default': '1.90e-06',      'widget': 'dc226ErrEntry'},
    's235':                    {'default': '6.72e-13',      'widget': 'dc235ErrEntry'},
    's231':                    {'default': '7.10e-08',      'widget': 'dc231ErrEntry'},

    'dpp_comma_sep_thousands':          {'default': True,     'widget': 'dppComSepOpt'},
    'dpp_major_gridlines':              {'default': False,    'widget': 'dppMajorGridlinesOpt'},
    'dpp_minor_gridlines':              {'default': False,    'widget': 'dppMinorGridlinesOpt'},
    'dpp_minor_ticks':                  {'default': False,    'widget': 'dppMinorTicksOpt'},
    'dpp_hide_spines':                  {'default': False,    'widget': 'dppHideSpinesOpt'},
    'dpp_lower_exp':                    {'default': '-3',     'widget': 'dppLowerExpEntry'},
    'dpp_upper_exp':                    {'default': '4',      'widget': 'dppUpperExpEntry'},
    'dpp_dpi':                          {'default': '300',    'widget': 'dppDpiEntry'},
    'dpp_height':                       {'default': '4.012',  'widget': 'dppHeightEntry'},
    'dpp_width':                        {'default': '4.72',   'widget': 'dppWidthEntry'},
    'dpp_plot_concordia':               {'default': False,    'widget': 'dppPlotConcordiaOpt'},
    'dpp_concordia_envelope':           {'default': False,    'widget': 'dppConcordiaEnvelopeOpt'},
    'dpp_conc_spaghetti':               {'default': False,    'widget': 'dppConcSpaghettiOpt'},
    'dpp_age_ellipse_markers':          {'default': False,    'widget': 'dppAgeEllipseOpt'},
    'dpp_marker_max_age':               {'default': 'None',   'widget': 'dppMarkerMaxAgeEntry'},
    'dpp_use_manual_age_markers':       {'default': False,    'widget': 'dppManualAgeMarkersOpt'},
    'dpp_manual_age_markers':           {'default': '0.5 1 10 100 250 500 750 1000',
                                                              'widget': 'dppManualAgeMarkersEntry'},
    'dpp_age_prefix':                   {'default': 'Ma',     'widget': 'dppAgePrefixCombo'},
    'dpp_age_prefix_in_label':          {'default': True,     'widget': 'dppAgePrefixOpt'},
    'dpp_rotate_labels':                {'default': False,    'widget': 'dppRotateLabelsOpt'},
    'dpp_rotate_perpendicular':         {'default': False,    'widget': 'dppRotatePerpendicularOpt'},
    'dpp_avoid_label_overlaps':         {'default': False,    'widget': 'dppLabelOverlapsOpt'},
    'dpp_individual_labels':            {'default': True,     'widget': 'dppIndividualLabelsOpt'},
    'dpp_label_offset_factor':          {'default': '0.7',    'widget': 'dppLabelOffsetEntry'},
    'dpp_label_every_second':           {'default': '8',      'widget': 'dppLabelEverySecondEntry'},

    'int_comma_sep_thousands':          {'default': True,     'widget': 'intComSepOpt'},
    'int_major_gridlines':              {'default': False,    'widget': 'intMajorGridlinesOpt'},
    'int_minor_gridlines':              {'default': False,    'widget': 'intMinorGridlinesOpt'},
    'int_minor_ticks':                  {'default': False,    'widget': 'intMinorTicksOpt'},
    'int_hide_spines':                  {'default': False,    'widget': 'intHideSpinesOpt'},
    'int_lower_exp':                    {'default': '-3',     'widget': 'intLowerExpEntry'},
    'int_upper_exp':                    {'default': '4',      'widget': 'intUpperExpEntry'},
    'int_dpi':                          {'default': '300',    'widget': 'intDpiEntry'},
    'int_height':                       {'default': '4.012',  'widget': 'intHeightEntry'},
    'int_width':                        {'default': '4.72',   'widget': 'intWidthEntry'},

    'int_concordia_envelope':           {'default': False,    'widget': 'intConcordiaEnvelopeOpt'},
    'int_conc_spaghetti':               {'default': False,    'widget': 'intConcSpaghettiOpt'},
    'int_age_ellipse_markers':          {'default': False,    'widget': 'intAgeEllipseOpt'},
    'int_marker_max_age':               {'default': 'None',   'widget': 'intMarkerMaxAgeEntry'},
    'int_use_manual_age_markers':       {'default': False,    'widget': 'intManualAgeMarkersOpt'},
    'int_manual_age_markers':           {'default': '0.5 1 10 100 250 500 750 1000',
                                                              'widget': 'intManualAgeMarkersEntry'},
    'int_age_prefix':                   {'default': 'Ma',     'widget': 'intAgePrefixCombo'},
    'int_age_prefix_in_label':          {'default': True,     'widget': 'intAgePrefixOpt'},
    'int_rotate_labels':                {'default': False,    'widget': 'intRotateLabelsOpt'},
    'int_rotate_perpendicular':         {'default': False,    'widget': 'intRotatePerpendicularOpt'},
    'int_avoid_label_overlaps':         {'default': False,    'widget': 'intLabelOverlapsOpt'},
    'int_individualised_labels':        {'default': True,     'widget': 'intIndividualisedLabelsOpt'},
    'int_label_offset_factor':          {'default': '0.7',    'widget': 'intLabelOffsetEntry'},
    'int_label_every_second':           {'default': '8',      'widget': 'intLabelEverySecondEntry'},

    'hist_comma_sep_thousands':         {'default': True,      'widget': 'histComSepOpt'},
    'hist_major_gridlines':             {'default': False,     'widget': 'histMajorGridlinesOpt'},
    'hist_minor_gridlines':             {'default': False,     'widget': 'histMinorGridlinesOpt'},
    'hist_minor_ticks':                 {'default': False,     'widget': 'histMinorTicksOpt'},
    'hist_lower_exp':                   {'default': '-3',      'widget': 'histLowerExpEntry'},
    'hist_upper_exp':                   {'default': '4',       'widget': 'histUpperExpEntry'},
    'hist_dpi':                         {'default': '300',     'widget': 'histDpiEntry'},
    'hist_height':                      {'default': '4.8',     'widget': 'histHeightEntry'},
    'hist_width':                       {'default': '6.4',     'widget': 'histWidthEntry'},

    'wav_comma_sep_thousands':          {'default': True,     'widget': 'wavComSepOpt'},
    'wav_dpi':                          {'default': '300',    'widget': 'wavDpiEntry'},
    'wav_height':                       {'default': '4.012',  'widget': 'wavHeightEntry'},
    'wav_hide_spines':                  {'default': False,    'widget': 'wavHideSpinesOpt'},
    'wav_lower_exp':                    {'default': '-2',     'widget': 'wavLowerExpEntry'},
    'wav_major_gridlines':              {'default': True,    'widget': 'wavMajorGridlinesOpt'},
    'wav_minor_gridlines':              {'default': False,    'widget': 'wavMinorGridlinesOpt'},
    'wav_minor_ticks':                  {'default': False,    'widget': 'wavMinorTicksOpt'},
    'wav_sort_ages':                    {'default': False,    'widget': 'wavSortAgesOpt'},
    'wav_upper_exp':                    {'default': '6',      'widget': 'wavUpperExpEntry'},
    'wav_width':                        {'default': '4.72',   'widget': 'wavWidthEntry'},
    'wav_age_prefix':                   {'default': 'Ma',     'widget': 'wavAgePrefixCombo'},

    'axis_label_font_color':             {'default': 'black', 'widget': 'axLabelFontColorCombo'},
    'axis_label_font_size':              {'default': '10',    'widget': 'axLabelFontSizeCombo'},

    'axis_spine_color':                  {'default': 'k',     'widget': 'axSpineColorCombo'},
    'axis_spine_width':                  {'default': '0.80',  'widget': 'axSpineLineWidthEntry'},

    'conc_age_ellipse_alpha':            {'default': '1.0',     'widget': 'ageEllipseAlphaEntry'},
    'conc_age_ellipse_edge_color':       {'default': 'black',   'widget': 'ageEllipseEdgeColorCombo'},
    'conc_age_ellipse_face_color':       {'default': 'white',   'widget': 'ageEllipseFillColorCombo'},
    'conc_age_ellipse_edge_width':       {'default': '0.5',     'widget': 'ageEllipseEdgeWidthEntry'},
    'conc_age_ellipse_z':                {'default': '10',      'widget': 'ageEllipseZEntry'},

    'conc_env_alpha':                    {'default': '0.8',     'widget': 'concEnvAlphaEntry'},
    'conc_env_edge_color':               {'default': 'none',    'widget': 'concEnvLineColorCombo'},
    'conc_env_face_color':               {'default': 'none',   'widget': 'concEnvFaceColorCombo'},
    'conc_env_line_style':               {'default': '-',       'widget': 'concEnvLineStyleCombo'},
    'conc_env_line_width':               {'default': '0.0',     'widget': 'concEnvLineWidthEntry'},
    'conc_env_z':                        {'default': '8',      'widget': 'concEnvZEntry'},

    'conc_env_line_alpha':               {'default': '1.0',     'widget': 'concEnvLineAlphaEntry'},
    'conc_env_line_color':               {'default': 'black',   'widget': 'concEnvLineColorCombo'},
    'conc_env_line_line_style':          {'default': '--',      'widget': 'concEnvLineLineStyleCombo'},
    'conc_env_line_line_width':          {'default': '1.0',    'widget': 'concEnvLineLineWidthEntry'},
    'conc_env_line_z':                   {'default': '8',      'widget': 'concEnvLineZEntry'},

    'conc_intercept_ellipse_alpha':      {'default': '0.60',    'widget': 'interceptEllipseAlphaEntry'},
    'conc_intercept_ellipse_edge_color': {'default': 'black',   'widget': 'interceptEllipseEdgeColorCombo'},
    'conc_intercept_ellipse_face_color': {'default': 'lightgrey', 'widget': 'interceptEllipseFillColorCombo'},
    'conc_intercept_ellipse_line_width': {'default': '1.0',     'widget': 'interceptEllipseEdgeWidthEntry'},
    'conc_intercept_ellipse_z':          {'default': '30',      'widget': 'interceptEllipseZEntry'},

    'conc_intercept_marker_alpha':      {'default': '0.5',      'widget': 'mcMarkerAlphaEntry'},
    'conc_intercept_marker_edge_color': {'default': 'none',     'widget': 'mcMarkerEdgeColorCombo'},
    'conc_intercept_marker_face_color': {'default': 'black',    'widget': 'mcMarkerFaceColorCombo'},
    'conc_intercept_marker_edge_width': {'default': '0.0',      'widget': 'mcMarkerEdgeWidthEntry'},
    'conc_intercept_marker_type':       {'default': ',',        'widget': 'mcMarkerTypeCombo'},
    'conc_intercept_marker_size':       {'default': '4',        'widget': 'mcMarkerSizeEntry'},
    'conc_intercept_marker_z':          {'default': '30',       'widget': 'mcMarkerZEntry'},

    'conc_line_alpha':            {'default': '1.0',      'widget': 'concLineAlphaEntry'},
    'conc_line_color':            {'default': 'black',    'widget': 'concLineColorCombo'},
    'conc_line_style':            {'default': '-',        'widget': 'concLineStyleCombo'},
    'conc_line_width':            {'default': '0.80',     'widget': 'concLineWidthEntry'},
    'conc_line_z':                {'default': '9',       'widget': 'concLineZEntry'},

    'conc_marker_alpha':          {'default': '1.0',      'widget': 'concMarkerAlphaEntry'},
    'conc_marker_edge_color':     {'default': 'black',    'widget': 'concMarkerEdgeColorCombo'},
    'conc_marker_edge_width':     {'default': '0.8',      'widget': 'concMarkerEdgeWidthEntry'},
    'conc_marker_face_color':     {'default': 'white',    'widget': 'concMarkerFillColorCombo'},
    'conc_marker_size':           {'default': '4',        'widget': 'concMarkerSizeEntry'},
    'conc_marker_type':           {'default': 'o',        'widget': 'concMarkerTypeCombo'},
    'conc_marker_z':              {'default': '10',       'widget': 'concMarkerZEntry'},

    'conc_text_color':            {'default': 'black',         'widget': 'concLabelFontColorCombo'},
    'conc_text_font_size':        {'default': '8',             'widget': 'concLabelFontSizeCombo'},
    'conc_text_h_alignment':      {'default': 'left',          'widget': 'concLabelHAlignmentCombo'},
    'conc_text_textcoords':       {'default': 'offset points', 'widget': 'concLabelTextCoordsCombo'},
    'conc_text_v_alignment':      {'default': 'center',        'widget': 'concLabelVAlignmentCombo'},
    'conc_text_x_offset':         {'default': "-5",            'widget': 'concLabelXoffsetEntry'},
    'conc_text_y_offset':         {'default': "2",             'widget': 'concLabelYoffsetEntry'},
    'conc_text_z':                {'default': '11',            'widget': 'concLabelZEntry'},

    'data_ellipse_alpha':         {'default': '1.0',           'widget': 'ellipseAlphaEntry'},
    'data_ellipse_edge_color':    {'default': 'black',         'widget': 'ellipseEdgeColorCombo'},
    'data_ellipse_face_color':    {'default': 'white',       'widget': 'ellipseFillColorCombo'},
    'data_ellipse_edge_width':    {'default': '0.8',           'widget': 'ellipseEdgeWidthEntry'},
    'data_ellipse_z':             {'default': '40',            'widget': 'ellipseZEntry'},

    'data_label_font_color':      {'default': 'black',         'widget': 'dpLabelFontColorCombo'},
    'data_label_font_size':       {'default': '8',             'widget': 'dpLabelFontSizeEntry'},
    'data_label_h_alignment':     {'default': 'center',        'widget': 'dpLabelHAlignmentCombo'},
    'data_label_offset_coord':    {'default': 'offset points', 'widget': 'dpLabelTextOffsetCoordCombo'},
    'data_label_v_alignment':     {'default': 'center',        'widget': 'dpLabelVAlignmentCombo'},
    'data_label_x_offset':        {'default': "10",            'widget': 'dpLabelXoffsetEntry'},
    'data_label_y_offset':        {'default': "0",             'widget': 'dpLabelYoffsetEntry'},
    'data_label_z':               {'default': '40',            'widget': 'dpLabelZEntry'},

    # fig properties - set via plot specific dialog

    'gridlines_alpha':            {'default': '1.0',       'widget': 'majorGridlinesAlphaEntry'},
    'gridlines_color':            {'default': 'black',     'widget': 'majorGridlinesColorCombo'},
    'gridlines_line_style':       {'default': ':',         'widget': 'majorGridlinesStyleCombo'},
    'gridlines_line_width':       {'default': '0.50',      'widget': 'majorGridlinesWidthEntry'},

    'histogram_alpha':            {'default': '0.75',      'widget': 'histogramAlphaEntry'},
    'histogram_edge_color':       {'default': 'red',       'widget': 'histogramEdgeColorCombo'},
    'histogram_face_color':       {'default': 'green',     'widget': 'histogramFillColorCombo'},
    'histogram_hist_type':        {'default': 'step',      'widget': 'histogramHistTypeCombo'},
    'histogram_line_width':       {'default': '0.75',      'widget': 'histogramLineWidthEntry'},

    'major_ticks_color':          {'default': 'black',     'widget': 'majorTicksColorCombo'},
    'major_ticks_direction':      {'default': 'in',        'widget': 'majorTicksDirectionCombo'},
    'major_ticks_size':           {'default': '4',         'widget': 'majorTicksSizeEntry'},
    'major_ticks_width':          {'default': '0.5',       'widget': 'majorTicksWidthEntry'},
    'major_ticks_zorder':         {'default': 100,         'widget': 'majorTicksZorder'},

    'minor_ticks_color':          {'default': 'black',     'widget': 'minorTicksColorCombo'},
    'minor_ticks_direction':      {'default': 'in',        'widget': 'minorTicksDirectionCombo'},
    'minor_ticks_size':           {'default': '2',         'widget': 'minorTicksSizeEntry'},
    'minor_ticks_width':          {'default': '0.5',       'widget': 'minorTicksWidthEntry'},
    'minor_ticks_zorder':         {'default': 100,         'widget': 'minorTicksZorder'},

    'pb76_line_alpha':            {'default': '0.50',      'widget': 'pb76LineAlphaEntry'},
    'pb76_line_color':            {'default': 'blue',      'widget': 'pb76LineColorCombo'},
    'pb76_line_style':            {'default': '--',        'widget': 'pb76LineStyleCombo'},
    'pb76_line_width':            {'default': '1.0',       'widget': 'pb76LineWidthEntry'},
    'pb76_line_z':                {'default': '10',        'widget': 'pb76LineZEntry'},

    'regression_env_alpha':           {'default': '0.3',   'widget': 'regressionEnvelopeAlphaEntry'},
    'regression_env_edge_color':      {'default': 'none',  'widget': 'regressionEnvelopeLineColorCombo'},
    'regression_env_face_color':      {'default': 'none',  'widget': 'regressionEnvelopeFaceColorCombo'},
    'regression_env_line_width':      {'default': '0.',    'widget': 'regressionEnvelopeLineWidthEntry'},
    'regression_env_line_style':      {'default': '--',    'widget': 'regressionEnvelopeLineStyleCombo'},
    'regression_env_z':               {'default': '20',     'widget': 'regressionEnvelopeZEntry'},

    'regression_env_line_alpha':      {'default': '1.0',   'widget': 'regressionEnvLineAlphaEntry'},
    'regression_env_line_color':      {'default': 'red',   'widget': 'regressionEnvLineColorCombo'},
    'regression_env_line_line_width': {'default': '0.8',   'widget': 'regressionEnvLineLineWidthEntry'},
    'regression_env_line_line_style': {'default': '--',     'widget': 'regressionEnvLineLineStyleCombo'},
    'regression_env_line_z':          {'default': '20',     'widget': 'regressionEnvLineZEntry'},

    'regression_line_alpha':          {'default': '1.0',   'widget': 'regressionLineAlphaEntry'},
    'regression_line_color':          {'default': 'red',  'widget': 'regressionLineColorCombo'},
    'regression_line_style':          {'default': '-',     'widget': 'regressionLineStyleCombo'},
    'regression_line_width':          {'default': '1.0',  'widget': 'regressionLineWidthEntry'},
    'regression_line_z':              {'default': '21',    'widget': 'regressionLineZEntry'},

    'scatter_plot_marker_alpha':      {'default': '0.3',   'widget': 'scatterPlotMarkerAlphaEntry'},
    'scatter_plot_marker_edge_color': {'default': 'none',  'widget': 'scatterPlotMarkerEdgeColorCombo'},
    'scatter_plot_marker_edge_width': {'default': '0.0',   'widget': 'scatterPlotMarkerEdgeWidthEntry'},
    'scatter_plot_marker_face_color': {'default': 'black', 'widget': 'scatterPlotMarkerFaceColorCombo'},
    'scatter_plot_marker_type':       {'default': ',',     'widget': 'scatterPlotMarkerTypeCombo'},
    'scatter_plot_marker_size':       {'default': '4',     'widget': 'scatterPlorMarkerSizeEntry'},
    'scatter_plot_marker_z':          {'default': '1',     'widget': 'scatterPlotMarkerZEntry'},

    'wav_envelope_alpha':         {'default': '0.80',      'widget': 'wavEnvAlphaEntry'},
    'wav_envelope_face_color':    {'default': 'lightgrey',   'widget': 'wavEnvFaceColorCombo'},
    'wav_envelope_edge_color':    {'default': 'none',      'widget': 'wavEnvEdgeColorCombo'},
    'wav_envelope_line_style':    {'default': '-',        'widget': 'wavEnvStyleCombo'},
    'wav_envelope_line_width':    {'default': '0.0',       'widget': 'wavEnvLineWidthEntry'},
    'wav_envelope_z':             {'default': '19',        'widget': 'wavEnvZEntry'},

    'wav_line_alpha':             {'default': '1.0',       'widget': 'wavLineAlphaEntry'},
    'wav_line_color':             {'default': 'black',     'widget': 'wavLineColorCombo'},
    'wav_line_style':             {'default': '-',         'widget': 'wavLineStyleCombo'},
    'wav_line_width':             {'default': '1.0',       'widget': 'wavLineWidthEntry'},
    'wav_line_z':                 {'default': '20',        'widget': 'wavLineZEntry'},

    'wav_marker_alpha':           {'default': '1.0',       'widget': 'wavMarkerAlphaEntry'},
    'wav_marker_face_color':      {'default': 'white',     'widget': 'wavMarkerFaceColorCombo'},
    'wav_marker_edge_color':      {'default': 'blue',      'widget': 'wavMarkerEdgeColor'},
    'wav_marker_width':           {'default': '0.8' ,      'widget': 'wavMarkerWidthEntry'},
    'wav_marker_linewidth':       {'default': '0.8',       'widget': 'wavMarkerLineWidth'},
    'wav_marker_z':               {'default': '41',        'widget': 'wavMarkerZEntry'},

    'wav_rand_marker_alpha':      {'default': '1.0',       'widget': 'wavRandMarkerAlphaEntry'},
    'wav_rand_marker_face_color': {'default': 'blue',      'widget': 'wavRandMarkerFaceColorCombo'},
    'wav_rand_marker_edge_color': {'default': 'blue',      'widget': 'wavRandMarkerEdgeColor'},
    'wav_rand_marker_linewidth':  {'default': '0.8',         'widget': 'wavRandMarkerLineWidth'},
    'wav_rand_marker_z':          {'default': '40',        'widget': 'wavRandMarkerZEntry'},

}


class QConfig:
    """ """
    @property
    def gui_settings(self):

        # name = "DQPB" if sys.platform == "win32" else "dqpb"
        settings = QSettingsManager()

        if not settings.settings.allKeys():
            for k in GuiSettingsMap.keys():
                settings.set(k, GuiSettingsMap[k]["default"])
            # gui_settings.sync()

            settings.set('DQPB_version', version)

            # TODO: set defaults for all so that data is read from settings
            #  file as appropriate dtype?
            # TODO: implement custom user options properly:
            # add container to store user colors
            settings.set_default('user_colors', ['a', 'b'])
            # add default hex rgb colors
            settings.set('user_colors', ['#FFFFC0', '#C5F7C5', '#1FB714'])

        return settings

    def read(self):
         return self.gui_settings
