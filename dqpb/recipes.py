"""
'Recipes' for plotting and calculation tasks.

"""

import warnings
import logging
import numpy as np

from pysoplot import cfg
from pysoplot import concordia
from pysoplot import isochron
from pysoplot import plotting
from pysoplot import regression
from pysoplot import wtd_average
from pysoplot import transform
from pysoplot import upb
from pysoplot import uxpb

from dqpb import spreadsheet
from dqpb import combo
from dqpb import util


logger = logging.getLogger("dqpb.recipes")


# ==========================================================================
# Plot arbitrary data task.
# ==========================================================================
def plot_data(task):
    """
    Plot x-y data points (without age calculation) and optionally with
    regression fit and concordia (if diagram type is Tera-Wasserburg
    diagram).
    """
    # Print opts to sheet:
    if task.print_opts:
        opts_frame = spreadsheet.PrintFrame()
        task.printer.stack_frame(opts_frame, yorder=999)
        opts = []
        opts += ['task: %s' % 'Data plot']
        opts += [f'assume initial eq.: {task.eq}']
        opts += [f'regression algorithm: {combo.LONG_FITS[task.fit]}']
        if task.fit.startswith('sp'):
            # Spines model
            opts += [f'Spines h-value: {cfg.h}']
        if task.data_type in ('tw', 'wc'):
            if not task.eq:
                append_arv(opts, task, series='both', fcA48i=False)
            append_upb_const(opts, task, series='both', eq=task.eq)
        elif task.data_type == 'iso-Pb6U8':
            if not task.eq:
                append_arv(opts, task, series='238U', fcA48i=False)
            append_upb_const(opts, task, series='238U', eq=task.eq)
        elif task.data_type == 'iso-Pb7U5':
            if not task.eq:
                append_arv(opts, task, series='235U', fcA48i=False)
            append_upb_const(opts, task, series='235U', eq=task.eq)
        opts_frame.add_table([opts], title='Plot options:')

    # Initialise main print frame and add to printer stack:
    print_frame = spreadsheet.PrintFrame()
    task.printer.stack_frame(print_frame)

    dp = np.array(task.dp, dtype=np.double)
    dp = transform.dp_errors(dp, in_error_type=task.error_type, row_wise=True)

    # fit regression
    if task.fit.startswith('c'):
        fit = regression.classical_fit(*dp, model=task.fit, isochron=False,
                                       plot=False)
    else:
        fit = regression.robust_fit(*dp, model=task.fit, plot=False)

    results, formats = results_for_fit(fit)
    print_frame.add_table(results, title='Linear regression results:',
                          formats=formats)

    task.update_progress(25, "Plotting data... ")

    fig = plotting.plot_dp(*dp, labels=task.dp_labels)
    ax = fig.get_axes()[0]
    plotting.set_axis_limits(ax, xmin=task.dpp_xmin, xmax=task.dpp_xmax,
                             ymin=task.dpp_ymin, ymax=task.dpp_ymax)
    plotting.plot_rfit(ax, fit)
    plotting.apply_plot_settings(
        fig, diagram=task.data_type,
        xlim=(task.dpp_xmin, task.dpp_xmax),
        ylim=(task.dpp_ymin, task.dpp_ymax),
        axis_labels=(task.x_label, task.y_label),
        norm_isotope=task.norm_isotope
    )

    if task.dpp_plot_concordia and task.data_type == 'tw':
        if task.eq:
            concordia.plot_concordia(
                ax, task.data_type,
                env=task.dpp_concordia_envelope,
                age_ellipses=task.dpp_age_ellipse_markers,
                marker_max=task.dpp_marker_max_age,
                marker_ages=task.dpp_manual_age_markers,
                auto_markers=not task.dpp_use_manual_age_markers,
                remove_overlaps=task.dpp_avoid_label_overlaps,
                age_prefix=task.dpp_age_prefix
            )
        else:
            A = [task.A48, task.A08, task.A68, task.A15]
            sA = [task.A48_err, task.A08_err, task.A68_err, task.A15_err],
            init = task.init
            concordia.plot_diseq_concordia(
                ax, A, init, sA=sA, diagram='tw',
                env=task.dpp_concordia_envelope,
                age_ellipses=task.dpp_age_ellipse_markers,
                marker_max=task.dpp_marker_max_age,
                marker_ages=task.dpp_manual_age_markers,
                auto_markers=not task.dpp_use_manual_age_markers,
                remove_overlaps = task.dpp_avoid_label_overlaps,
                spaghetti=task.dpp_conc_spaghetti
            )

    # Add dp plot to print stack. This must be done after adding concordia.
    task.printer.stack_figure(fig, yorder=2)

    # print plot data
    if task.output_plot_data:
        ws_plot_data, next_col = \
            spreadsheet.print_plot_data(fig.get_axes()[0], sheet_name='Plot data',
                            header='Plot data', ws_main=task.ws, next_col=1,
                            labels=task.dp_labels)

    # Save plots.
    if task.save_plots:
        task.update_progress(60, "Saving plots to disk... ")
        path = util.save_plot_to_disk(fig, task.fig_export_dir,
                                      fname="X-y plot")
        logger.info(f"isochron plot saved to: '{path}.{task.fig_extension}'")

    # print results to spread sheet
    task.update_progress(75, "Printing results to spreadsheet...")
    task.printer.flush_stack()


# ==========================================================================
# Compute isochron / concordia-intercept age
# ==========================================================================
def diagram_age(task):
    """ Compute concordia-intercept or classical isochron U-Pb age.
    """
    if task.print_opts:
        opts_frame = spreadsheet.PrintFrame()
        task.printer.stack_frame(opts_frame, yorder=999)
        opts = []
        opts += ['diagram: %s' % combo.LONG_DATA_TYPES[task.data_type]]
        opts += ['assume initial eq.: %s' % task.eq]
        opts += ['regression algorithm: %s' % task.fit]
        if task.fit.startswith('sp'):
            opts += ['Spines h-value: %s' % task.spines_h]
        if task.data_type.startswith('iso'):
            opts += ['normalising isotope: %s' % task.norm_isotope]
        if not task.eq and task.data_type.startswith('tw'):
            opts += ['disequilibrium age guess: %s' % task.age_guess]
            if not any(task.init):
                opts += ['disequilibrium age range: %s' % (
                            cfg.concint_age_min, cfg.concint_age_max)
                         ]
        if task.concordia_intercept:
            series = 'both'
        elif task.data_type == 'iso-Pb6U8':
            series = '238U'
        else:
            series = '235U'
        if not task.eq:
            append_arv(opts, task, series=series)
        append_upb_const(opts, task, series=series, U=True, eq=False)
        append_mc_opts(opts, task)
        if task.save_plots:
            opts.append('figure save location: %s' % task.fig_export_dir)
        opts_frame.add_table([opts], title='Calc. options:')

    # initialise main print frame and add to printer stack
    print_frame = spreadsheet.PrintFrame()
    task.printer.stack_frame(print_frame)

    A = [task.A48, task.A08, task.A68, task.A15]
    sA = [task.A48_err, task.A08_err, task.A68_err, task.A15_err]
    init = task.init

    dp = np.array(task.dp, dtype=np.double)
    dp = transform.dp_errors(dp, in_error_type=task.error_type, row_wise=True)

    set_plot_config(task, 'data_point')

    # fit model
    if task.fit.startswith('c'):
        fit = regression.classical_fit(
            *dp, model=task.fit, plot=True,
            diagram=task.data_type,
            dp_labels=task.dp_labels,
            xlim=(task.dpp_xmin, task.dpp_xmax),
            ylim=(task.dpp_ymin, task.dpp_ymax),
            isochron=not task.concordia_intercept,
            norm_isotope=task.norm_isotope
        )
    else:
        fit = regression.robust_fit(
            *dp, model=task.fit, plot=True,
            diagram=task.data_type, xlim=(task.dpp_xmin,
            task.dpp_xmax), ylim=(task.dpp_ymin, task.dpp_ymax),
            norm_isotope=task.norm_isotope,
            dp_labels=task.dp_labels
        )

    task.update_progress(20, "Plotting data... ")

    fig_dpp = fit['fig']
    results, formats = results_for_fit(fit)
    print_frame.add_table(results, title='Linear regression results:',
                          formats=formats)

    # add concordia to rfit plot:
    if task.concordia_intercept:
        ax = fig_dpp.get_axes()[0]
        if task.eq and task.dpp_plot_concordia:
            concordia.plot_concordia(
                ax, task.data_type,
                plot_markers=True,
                env=task.dpp_concordia_envelope,
                age_ellipses=task.dpp_age_ellipse_markers,
                marker_max=task.dpp_marker_max_age,
                marker_ages=task.dpp_manual_age_markers,
                auto_markers=not task.dpp_use_manual_age_markers,
                remove_overlaps=task.dpp_avoid_label_overlaps,
                age_prefix=task.dpp_age_prefix
            )
        elif task.dpp_plot_concordia:
            concordia.plot_diseq_concordia(
                ax, A, init, sA=sA, diagram='tw',
                plot_markers=True,
                env=task.dpp_concordia_envelope,
                age_ellipses=task.dpp_age_ellipse_markers,
                marker_max=task.dpp_marker_max_age,
                marker_ages=task.dpp_manual_age_markers,
                auto_markers=not task.dpp_use_manual_age_markers,
                remove_overlaps=task.dpp_avoid_label_overlaps,
                spaghetti=task.dpp_conc_spaghetti,
                age_prefix=task.dpp_age_prefix
            )

    # Add dp plot to print stack. This must be done after adding concordia.
    task.printer.stack_figure(fig_dpp, yorder=2)

    task.update_progress(40, "Computing ages and uncertainties... ")

    # Data point plot is complete so now set dqpb.Plot kw settings as
    # intercept plot settings.
    if task.concordia_intercept and task.show_int_plot:
        set_plot_config(task, plot_type='intercept')

    # calculate eq age
    if task.eq or task.eq_guess:
        if task.concordia_intercept:
            eqAge = upb.concint_age(fit, method='Powell', diagram='tw')
        else:
            eqAge = upb.isochron_age(fit, age_type=task.data_type,
                                     dc_errors=task.dc_errors)
        t0 = eqAge['age']

        if task.eq or task.output_eq_age:
            results, formats = results_for_eq(eqAge)
            print_frame.add_table(results, title='Equilibrium age results:',
                                  formats=formats)

        if task.eq and task.do_mc:
            if task.data_type == 'tw':
                mcr = upb.mc_concint(
                    eqAge['age'], fit, diagram='tw',
                    trials=task.mc_trials,
                    dc_errors=task.dc_errors,
                    U_errors=task.u_errors,
                    intercept_plot=task.show_int_plot,
                    xlim=(task.int_xmin, task.int_xmax),
                    ylim=(task.int_ymin, task.int_ymax),
                    hist=task.age_hist,
                    env=task.int_concordia_envelope,
                    age_ellipses=task.int_age_ellipse_markers,
                    marker_max = task.int_marker_max_age,
                    marker_ages = task.int_manual_age_markers,
                    auto_marker_ages = not task.int_use_manual_age_markers,
                    remove_overlaps = task.int_avoid_label_overlaps,
                    intercept_points= task.conc_intercept_points,
                    intercept_ellipse=task.conc_intercept_ellipse,
                    age_prefix=task.int_age_prefix,
                    negative_ages=not task.mc_rnages
                )

            else:
                mcr = isochron.mc_uncert(
                    fit, age_type=task.data_type,
                    dc_errors=task.dc_errors,
                    norm_isotope=task.norm_isotope,
                    trials=task.mc_trials,
                    hist=task.age_hist
                )

            # print concordia intercept plot
            if task.concordia_intercept and task.show_int_plot:
                fig_int = mcr['fig']
                task.printer.stack_figure(fig_int, yorder=2)

            # print Monte Carlo histograms
            if 'age_hist' in mcr.keys():
                task.printer.stack_figure(mcr['age_hist'], yorder=3)

            results, formats = results_for_mc(mcr, summary=task.mc_summary)
            print_frame.add_table(results, title='Monte Carlo age uncertainties:',
                                  formats=formats)

    if not task.eq:
        t0 = eqAge['age'] if task.eq_guess else task.age_guess

        if task.concordia_intercept:
            conc_kw = dict(env=task.int_concordia_envelope,
                           age_ellipses=task.int_age_ellipse_markers,
                           marker_max=task.int_marker_max_age,
                           marker_ages=task.int_manual_age_markers,
                           auto_markers= not task.int_use_manual_age_markers,
                           remove_overlaps=task.int_avoid_label_overlaps,
                           env_trials=1_000, spaghetti=task.int_conc_spaghetti,
                           age_prefix=task.int_age_prefix
                           )
            int_plot_kw = dict(ylim=(task.int_ymin, task.int_ymax),
                               xlim=(task.int_xmin, task.int_xmax),
                               intercept_ellipse=task.conc_intercept_ellipse,
                               intercept_points=task.conc_intercept_points,
                               )
            diseqAge = uxpb.dqpb.concint_age(
                fit, A, sA, init, t0,
                conc_kw=conc_kw,
                intercept_plot_kw=int_plot_kw,
                diagram=task.data_type,
                age_lim=(task.concint_age_min,
                    task.concint_age_max),
                A48i_lim=(task.concint_A48i_min,
                    task.concint_A48i_max),
                A08i_lim=(task.concint_A08i_min,
                    task.concint_A08i_max),
                trials=task.mc_trials,
                dc_errors=task.dc_errors,
                u_errors=task.u_errors,
                negative_ar=not task.mc_rnar,
                negative_ages=not task.mc_rnages,
                hist=(task.age_hist, task.ar_hist)
            )
        else:
            if task.data_type == 'iso-Pb6U8':
                A = A[:-1]
                sA = sA[:-1]
            else:
                A = A[-1]
                sA = sA[-1]
            diseqAge = uxpb.dqpb.isochron_age(
                fit, A, sA, t0, init=init,
                age_type=task.data_type,
                norm_isotope=task.norm_isotope,
                hist = (task.age_hist, task.ar_hist),
                trials=task.mc_trials,
                dc_errors=task.dc_errors,
                negative_ar=not task.mc_rnar,
                negative_ages=not task.mc_rnages
            )

        results, formats = results_for_diseq(diseqAge, mc_summary=task.mc_summary)
        print_frame.add_table(results, title='Disequilibrium age results:',
                              formats=formats)

        # print concordia intercept plot
        if task.concordia_intercept and task.show_int_plot:
            fig_int = diseqAge['mc']['fig']
            task.printer.stack_figure(fig_int, yorder=2)

        # print Monte Carlo histograms
        if task.eq and task.do_mc:
            if 'age_hist' in eqAge['mc'].keys():
                task.printer.stack_figure(eqAge['mc']['age_hist'], yorder=3)
        else:
            for hist in ['age_hist', 'ar_hist', 'bcar_hist']:
                if hist in diseqAge['mc'].keys():
                    task.printer.stack_figure(diseqAge['mc'][hist], yorder=3)



    # Output plot data to spreadsheet:
    if task.output_plot_data:
        ws_plot_data, next_col = \
            spreadsheet.print_plot_data(
                fig_dpp.get_axes()[0],
                sheet_name='Plot data',
                header='Isochron plot data',
                ws_main=task.ws,
                next_col=1,
                labels=task.dp_labels
            )

        if task.concordia_intercept and task.show_int_plot:
            spreadsheet.print_plot_data(
                fig_int.get_axes()[0],
                header='Concordia-intercept plot data',
                ws=ws_plot_data,
                next_col=next_col,
                labels=task.dp_labels
            )

    # Save plots to disk:
    if task.save_plots:
        task.update_progress(60, "Saving plots to disk... ")
        path = util.save_plot_to_disk(fig_dpp, task.fig_export_dir,
                                      fname="Isochron plot")
        logger.info(f"isochron plot saved to: '{path}.{task.fig_extension}'")
        if task.concordia_intercept and task.show_int_plot:
            path = util.save_plot_to_disk(fig_int, task.fig_export_dir,
                                          fname='Concordia-intercept plot')
            logger.info(f"concordia-intercept plot saved to: '{path}.{task.fig_extension}'")

    # print results to spread sheet
    task.update_progress(80, "Printing results to spreadsheet...")
    task.printer.flush_stack()


# =========================================================================
# Weighted-average task
# =========================================================================
def wav_other(task):
    """
    Compute weighted average for arbitrary 1d data.
    """
    # print opts to sheet:
    if task.print_opts:
        opts_frame = spreadsheet.PrintFrame()
        task.printer.stack_frame(opts_frame, yorder=999)
        opts = []
        opts.append('task: wtd. average')
        opts.append(f'wtd. average type: {combo.LONG_FITS[task.fit]}')
        if task.fit.startswith('c'):
            opts.append(f'MSWD conf. limits: {cfg.mswd_wav_thresholds}')
        elif task.fit == 'Spine':
            opts.append(f'h-value: {cfg.h}')
        opts_frame.add_table([opts], title='Calc. options:')

    # create main print frame and add to printer stack
    print_frame = spreadsheet.PrintFrame()
    task.printer.stack_frame(print_frame)

    task.update_progress(25, 'Computing wtd. average...')

    # assemble data points
    if task.input_cov:
        x = task.dp.flatten()
        sx = None
        cov = task.cov
    else:
        dp = transform.dp_errors(task.dp, in_error_type=task.error_type,
                                 dim=1, row_wise=True)
        x, sx = dp
        cov = None

    set_plot_config(task, plot_type='wav')

    if task.fit.startswith('c'):
        wav = wtd_average.classical_wav(x, sx=sx, cov=cov, method='ca')
    else:
        wav = wtd_average.robust_wav(x, sx=sx, cov=cov, method='ra')

    results, formats = results_for_wav(wav, age=False)
    print_frame.add_table(results, title='Wtd. average results:',
                          formats=formats)

    if task.show_wav_plot:
        # Make wav plot:
        if cov is not None:
            sx = np.sqrt(np.diag(cov))
        fig = plotting.wav_plot(x, 2. * sx, wav['ave'], wav['ave_95pm'],
                        sorted=task.wav_sort_ages, dp_labels=task.dp_labels)
        ax = fig.get_axes()[0]
        ax.set_ylabel(task.y_label)
        task.printer.stack_figure(fig, yorder=2)

    if task.save_plots:
        task.update_progress(60, "Saving plots to disk... ")
        path = util.save_plot_to_disk(fig, task.fig_export_dir, fname="Wtd average")
        logger.info(f"wtd. average plot saved to: '{path}.{task.fig_extension}'")

    # print results to spread sheet:
    task.update_progress(75, "Printing results to spreadsheet...")
    task.printer.flush_stack()

    if task.output_plot_data:
        logger.warn('output plot data option not yet available for weighted '
                    'average plots')


# =========================================================================
# Pb/U age task
# =========================================================================
def pbu_age(task):
    """
    Calculate Pb/U or modified 207Pb age(s) and optionally compute a
    weighted average.
    """
    # print opts to sheet:
    if task.print_opts:
        opts_frame = spreadsheet.PrintFrame()
        task.printer.stack_frame(opts_frame, yorder=999)
        opts = []
        opts.append(f'task: {combo.LONG_DATA_TYPES[task.data_type]} age(s)')
        opts.append(f'wtd. average algorithm: {combo.LONG_FITS[task.fit]}')
        opts.append(f'assume initial eq.: {task.eq}')
        if not task.eq:
            opts.append(f'initial disequilibrium age guess: {task.age_guess}')
        if task.fit == 'sp':
            opts.append('Huber h-value: %s' % task.spines_h)
        if task.data_type.startswith('mod'):
            opts.append(f'207Pb/206Pb: {task.Pb76}')
            opts.append(f'207Pb/206Pb 1σ errors: {task.Pb76_1s}')
            series = 'both'
        elif task.data_type.startswith('Pb6'):
            series = '238U'
        else:
            series = '235U'
        if not task.eq:
            append_arv(opts, task, series=series, fcA48i=False)
        append_upb_const(opts, task, series=series, U=False, eq=task.eq)
        append_mc_opts(opts, task)
        if task.save_plots:
            opts.append('figure save location: %s' % task.fig_export_dir)
        opts_frame.add_table([opts], title='Calc. options:')

    # create main print frame and add to printer stack
    print_frame = spreadsheet.PrintFrame()
    task.printer.stack_frame(print_frame)

    wav = True if task.fit is not None else False

    # Get partition coefficient data:
    if task.data_type in ('Pb6U8', 'mod-207Pb'):
        if task.DThU_const:
            DThU_const = True
            DThU = task.A08
            DThU_1s = task.A08_err
            ThU_melt = None
            ThU_melt_1s = None
            ThU_min = None
        else:
            DThU_const = False
            ThU_melt = task.A08
            ThU_melt_1s = task.A08_err
            ThU_min = task.ThU_min
            DThU = None
            DThU_1s = None
    else:
        DThU_const = True
        ThU_melt = None
        ThU_melt_1s = None
        ThU_min = None
        DThU = None
        DThU_1s = None

    DPaU = task.A15
    DPaU_1s = task.A15_err

    dim = 2 if task.data_type == 'mod-207Pb' else 1
    dp = transform.dp_errors(task.dp, in_error_type=task.error_type, dim=dim)

    task.update_progress(25, 'Computing ages and errors...')

    set_plot_config(task, plot_type='histogram')

    if task.eq:
        raise ValueError('Equilibrium Pb/U and modified 207Pb age calculations '
                         'are not currently implemented in DQPB.')

    else:   # diseq. ages
        if task.age_guess == 'eq' or task.eq:
            eqAges = upb.pbu_ages(dp, age_type=task.data_type, wav=False, Pb76=task.Pb76)
            if task.output_eq_age:
                logger.warning('Output equilbrium age results not yet implemented.')
            t0 = eqAges['age']
        else:
            t0 = task.age_guess

        if any((task.age_hist, task.ar_hist)):
            logger.error('Age and activity ratio histograms not yet implemented '
                         'for Pb/U ages.')

        if task.data_type == 'mod-207Pb':
            diseqAges = uxpb.dqpb.mod207_age(
                dp, task.Pb76, task.Pb76_1s, t0,
                ThU_min=ThU_min, ThU_melt=ThU_melt,
                ThU_melt_1s=ThU_melt_1s,
                DThU=DThU, DThU_1s=DThU_1s,
                DThU_const=DThU_const,
                DPaU=DPaU, DPaU_1s=DPaU_1s,
                wav=wav,
                wav_method=task.fit,
                method='Ludwig',
                sorted=task.wav_sort_ages,
                rand=True,
                cov=task.wav_cov,
                ylim=(task.wav_ymin, task.wav_ymax),
                wav_plot_prefix=task.wav_age_prefix,
                dp_labels=task.dp_labels
            )
        else:
            diseqAges = uxpb.dqpb.pbu_age(
                *dp, t0,
                ThU_min=ThU_min, ThU_melt=ThU_melt,
                ThU_melt_1s=ThU_melt_1s,
                DThU=DThU, DThU_1s=DThU_1s,
                DThU_const=DThU_const,
                DPaU=DPaU, DPaU_1s=DPaU_1s,
                age_type=task.data_type,
                method='Ludwig',
                wav=wav,
                wav_method=task.fit,
                trials=task.mc_trials,
                sorted=task.wav_sort_ages,
                rand=True,
                cov=task.wav_cov,
                hist=(False, False),
                negative_ages=not task.mc_rnar,
                negative_ar=not task.mc_rnages,
                ylim=(task.wav_ymin, task.wav_ymax),
                wav_plot_prefix=task.wav_age_prefix,
                dp_labels=task.dp_labels
            )

        # print age results
        results, formats = results_for_diseq_pbu(diseqAges, mc_summary=task.mc_summary)
        print_frame = spreadsheet.PrintFrame(n_col=len(results), yorder=1)
        print_frame.add_table(results, title=None, formats=formats,
                              add_line_sep=False)
        task.printer.stack_frame(print_frame)

        if task.show_wav_plot:
            results, formats = results_for_wav(diseqAges['wav'], age=True)
            print_frame.add_table(results,
                                  title=f'Weighted average '
                                        f'{combo.LONG_DATA_TYPES[task.data_type]} age:',
                                  formats=formats)
            fig = diseqAges['fig_wav']
            task.printer.stack_figure(fig, yorder=2)

        # plot data points
        if task.data_type.startswith('mod') and task.dp_plot:
            set_plot_config(task, plot_type='intercept')
            fig_dp = plotting.plot_dp(*dp, labels=task.dp_labels)
            plotting.apply_plot_settings(
                fig_dp,
                diagram='tw',
                xlim=(task.int_xmin, task.int_xmax),
                ylim=(task.int_ymin, task.int_ymax)
            )
            ax = fig_dp.get_axes()[0]

            if not DThU_const:
                logger.warning('cannot plot concordia curve if DThU values are '
                                'not constant')
            else:
                concordia.plot_diseq_concordia(
                    ax,
                    [cfg.A48_eq, DThU, cfg.A68_eq, DPaU],
                    [True, True],
                    sA=[0.0, DThU_1s, 0.0, DPaU_1s],
                    diagram='tw',
                    env=task.int_concordia_envelope,
                    age_ellipses=task.int_age_ellipse_markers,
                    marker_ages=task.int_manual_age_markers,
                    auto_markers=not task.int_use_manual_age_markers,
                    remove_overlaps=task.int_avoid_label_overlaps,
                    negative_ar=not task.mc_rnar
                )
        plotting.plot_mod207_projection(ax, *dp, task.Pb76)
        task.printer.stack_figure(fig_dp, yorder=3)

    if task.output_plot_data:
        logger.warning('output plot data option not yet available for weighted '
                       'average plots')
        spreadsheet.print_plot_data(
            fig_dp.get_axes()[0],
            sheet_name='Plot data',
            header='Mod. 207Pb data point plot',
            ws_main=task.ws, next_col=1,
            labels=task.dp_labels
        )

    # Save plots to disk:
    if task.data_type.startswith('mod') and task.dp_plot and task.save_plots:
        task.update_progress(60, "Saving plots to disk... ")
        path = util.save_plot_to_disk(fig_dp, task.fig_export_dir,
                                      fname="Mod 207Pb data plot")
        logger.info(f"isochron plot saved to: '{path}.{task.fig_extension}'")

    # print results
    task.update_progress(75, 'Printing results to sheet...')
    task.printer.flush_stack()


# =========================================================================
# Forced concordant [234U/238U]_i task
# =========================================================================

def forced_concordance(task):
    """
    Compute forced "isochron-concordance" initial [234U/238U] following
    Engel et al., (2019).
    """
    if task.print_opts:
        opts_frame = spreadsheet.PrintFrame()
        task.printer.stack_frame(opts_frame, yorder=999)
        opts = []
        opts += ['task: forced-concordance [234U/238U]i']
        opts += [f'regression algorithms: {combo.LONG_FITS[task.fit_iso57]}, \
                                    {combo.LONG_FITS[task.fit_iso86]}']
        if task.fit_iso57.startswith('rs') or task.fit_iso86.startswith('rs'):
            opts += ['Spines h-value: %s' % task.spines_h]
        opts += ['normalising isotope: %s' % task.norm_isotope]
        opts += ['207Pb age guess: %s' % task.age_guess]
        append_arv(opts, task, series='both')
        append_mc_opts(opts, task)
        opts += ['use secular eq. equations: %s' % task.secular_eq]
        append_upb_const(opts, task, series='both', U=True, eq=False)
        if task.save_plots:
            opts.append('figure save location: %s' % task.fig_export_dir)
        opts_frame.add_table([opts], title='Calc. options:')

    # create main print frame and add to printer stack
    print_frame = spreadsheet.PrintFrame()
    task.printer.stack_frame(print_frame)

    A = [np.nan, task.A08, task.A68, task.A15]
    sA = [np.nan, task.A08_err, task.A68_err, task.A15_err]
    init = [True, task.init[1]]

    dp57 = transform.dp_errors(task.dp_iso57, in_error_type=task.error_type)
    dp86 = transform.dp_errors(task.dp_iso86, in_error_type=task.error_type)

    # iso-Pb7U5 regression
    task.update_progress(25, "Fitting regression models... ")
    if task.fit_iso57.startswith('c'):
        fit57 = regression.classical_fit(*dp57, model=task.fit_iso57, plot=True,
                                         diagram='iso-Pb7U5')
    else:
        fit57 = regression.robust_fit(*dp57, model=task.fit_iso57, plot=True,
                                      diagram='iso-Pb7U5')

    fig_iso57 = fit57['fig']
    results, formats = results_for_fit(fit57)
    print_frame.add_table(results, title='235U-207Pb regression:',
                          formats=formats)
    task.printer.stack_figure(fig_iso57, yorder=2)

    # iso-Pb6U8 regression
    if task.fit_iso86.startswith('c'):
        fit86 = regression.classical_fit(*dp57, model=task.fit_iso57, plot=True,
                                         diagram='iso-Pb6U8')
    else:
        fit86 = regression.robust_fit(*dp86, model=task.fit_iso86, plot=True,
                                      diagram='iso-Pb6U8')
    fig_iso86 = fit86['fig']
    results, formats = results_for_fit(fit86)
    print_frame.add_table(results, title='238U-206Pb regression:',
                          formats=formats)

    # print regression fit plots
    task.printer.stack_figure(fig_iso86, yorder=2)

    # calculate "concordant" 234U/238U activity ratio and age
    if task.eq_guess:
        eqAge = upb.isochron_age(fit57, age_type='iso-Pb7U5')
        if task.output_eq_age:
            results, formats = results_for_eq(eqAge)
            print_frame.add_table(results, title='Equilibrium age results:',
                                  formats=formats)
        t0 = eqAge['age']
    else:
        t0 = task.age_guess

    concA48i =  uxpb.dqpb.fc_A48i(
        fit57, fit86, A, sA, t0=t0,
        norm_isotope='204Pb',
        negative_ar=not task.mc_rnar,
        negative_ages=not task.mc_rnages,
        hist=(task.age_hist, task.ar_hist),
        trials=task.mc_trials
    )
    results, formats = results_for_fcA48i(concA48i)
    print_frame.add_table(results, title='Forced-concordance results:',
                          formats=formats)

    # set plot settings to hist for gridlines etc.
    set_plot_config(task, 'histogram')

    # plot Monte Carlo histograms
    if task.ar_hist:
        fig = concA48i['mc']['age_hist']
        plotting.apply_plot_settings(fig, plot_type='hist')
        task.printer.stack_figure(fig, yorder=2)

    if task.age_hist:
        fig = concA48i['mc']['ar_hist']
        plotting.apply_plot_settings(fig, plot_type='hist')
        task.printer.stack_figure(fig, yorder=2)

    # Output plot data to spreadsheet:
    if task.output_plot_data:
        ws_plot_data, next_col = \
            spreadsheet.print_plot_data(
                fig_iso57.get_axes()[0],
                sheet_name='Plot data',
                header='235U-207Pb isochron plot',
                ws_main=task.ws,
                next_col=1,
                labels=task.dp_labels
            )

        spreadsheet.print_plot_data(
            fig_iso86.get_axes()[0],
            header="238U-206Pb isochron plot",
            ws=ws_plot_data,
            next_col=next_col,
            labels=task.dp_labels
        )

    # Save plots to disk:
    if task.save_plots:
        task.update_progress(60, "Saving plots to disk... ")
        path = util.save_plot_to_disk(fig_iso57, task.fig_export_dir,
                                      fname='235U-207Pb isochron plot')
        logger.info(f"235U-207Pb isochron plot saved to: '{path}.{task.fig_extension}'")
        path = util.save_plot_to_disk(fig_iso86, task.fig_export_dir,
                                      fname="238U-206Pb isochron plot")
        logger.info(f"238U-206Pb isochron plot saved to: '{path}.{task.fig_extension}'")

    # print results to spread sheet
    task.update_progress(75, "Printing results to spreadsheet...")
    task.printer.flush_stack()


#==============================================================================
# Compile results for printing to spreadsheet
#==============================================================================

def results_for_wav(wav, age=False):
    """
    """
    name = []
    value = []
    format = []

    # Get formats
    x = wav['ave']
    sx = wav['ave_95pm']
    fx, fsx = util.vep_format(x, sx, plims=(-3, 5))

    s = 'age' if age else 'ave.'
    cov_bool = 'TRUE' if wav['cov'] else 'FALSE'

    if wav['type'] == 'classical':
        name += ['type'];     value += ['classical'];      format += [None]
        name += ['n'];            value += [wav['n']];         format += ["#"]
        name += ['covariance'];   value += [cov_bool];         format += [None]
        name += ['ave'];          value += [wav['ave']];       format += [fx]
        name += [f'{s} 1σ'];      value += [wav['ave_1s']];    format += [fsx]
        name += [f'{s} 95% conf.'];  value += [wav['ave_95pm']];  format += [fsx]
        name += ['mswd'];         value += [wav['mswd']];      format += ["#0.00"]
        name += ['p'];        value += [wav['p']];     format += ["#0.00"]
        name += ['excess scatter']; value += [str(wav['excess_scatter']).upper()]; format += [None]
    else:
        name += ['type'];     value += [wav['model']];           format += [None]
        name += ['n'];            value += [wav['n']];         format += ["#"]
        name += ['covariance'];   value += [cov_bool];         format += [None]
        name += ['ave'];          value += [wav['ave']];       format += [fx]
        name += [f'{s} 95% conf.'];  value += [wav['ave_95pm']];  format += [fsx]
        name += ['s'];            value += [wav['s']];         format += ["#0.00"]
        name += ['s upper 95% CL']; value += [wav['s_upper_95ci']]; format += ["#0.00"]

    return [name, value], format


def results_for_fit(fit):
    """ Compile regression fit results into list of lists.
    """
    name = []
    value = []
    format = []

    # Get formats
    a, b = fit['theta']
    sa, sb = fit['theta_95ci']
    fa, fsa = util.vep_format(a, sa, plims=(-3, 5))
    fb, fsb = util.vep_format(b, sb, plims=(-3, 5))

    if fit['type'] == 'classical':
        name += ['fit type'];      value += [fit['model']];         format += [None]
        name += ['n'];             value += [fit['n']];             format += ["#"]
        name += ['slope'];         value += [fit['theta'][1]];      format += [fb]
        name += ['slope ±95% conf.']; value += [fit['theta_95ci'][1]]; format += [fsb]
        name += ['y-int'];         value += [fit['theta'][0]];      format += [fa]
        name += ['y-int ±95% conf.']; value += [fit['theta_95ci'][0]]; format += [fsa]
        name += ['corr. coeff.'];   value += [fit['r_ab']];          format += ["#0.0000"]
        name += ['xbar'];          value += [fit['xbar']];          format += ["#0.00"]
        name += ['ybar'];          value += [fit['ybar']];          format += ["#0.00"]
        name += ['mswd'];          value += [fit['mswd']];          format += ["#0.00"]
        name += ['p'];             value += [fit['p']];             format += ["#0.00"]
        if fit['model'] == 'model 3':
            name += ['initial Pb/Pb var. (2σ)']; value += [2. * fit['sy_excess_1s']];
            format += [fsa]
    else:
        name += ['fit type'];       value += [fit['model']];         format += [None]
        name += ['n'];              value += [fit['n']];             format += ["#"]
        name += ['slope'];          value += [fit['theta'][1]];      format += [fb]
        name += ['slope ±95% conf.'];  value += [fit['theta_95ci'][1]]; format += [fsb]
        name += ['y-int'];          value += [fit['theta'][0]];      format += [fa]
        name += ['y-int ±95% conf.'];  value += [fit['theta_95ci'][0]]; format += [fsa]
        name += ['corr. coeff.'];    value += [fit['r_ab']];          format += ["#0.00"]
        if fit['model'] == 'spine':
            name += ['s'];              value += [fit['s']];             format += ["#0.00"]
            name += ['s upper 95% CL']; value += [fit['slim']];          format += ["#0.00"]

    return [name, value], format


def results_for_eq(results, mcr=None, mc_summary=False):
    """ Compile results for eq age.
    """
    name = []
    value = []
    format = []

    # Get formats
    t = results['age']
    st = results['age_95pm']
    ft, fst = util.vep_format(t, st, plims=(-3, 5))

    name += ['age (Ma)']; value += [results['age']]; format += [ft]
    name += ['age +/- 95% CI']; value += [results['age_95pm']]; format += [fst]

    return [name, value], format


def results_for_fcA48i(results):
    """ """
    name = []
    value = []
    format = []

    mc = results['mc']

    t = results['207Pb_age'];
    st = mc['207Pb_age_1sd']
    ft, fst = util.vep_format(t, 2. * st, plims=(-3, 5))

    ark = '[234U/238U]i'
    A48i = results[ark]
    sA48i = mc['[234U/238U]i_1sd']
    fA, fsA = util.vep_format(A48i, 2. * sA48i, plims=(-3, 5))

    mc = results['mc']
    name += ['age (Ma)'];     value += [results['207Pb_age']];     format += [ft]
    name += ['1σ (Ma)'];      value += [mc['207Pb_age_1sd']];      format += [fst]
    name += ['lower 95% CI']; value += [mc['207Pb_age_95ci'][0]]; format += [ft]
    name += ['upper 95% CI']; value += [mc['207Pb_age_95ci'][1]]; format += [ft]
    name += ['init. [234U/238U]']; value += [results[ark]]; format += [fA]
    name += ['1σ'];           value += [mc[f'{ark}_1sd']];     format += [fsA]
    name += ['lower 95% CI']; value += [mc[f'{ark}_95ci'][0]]; format += [fA]
    name += ['upper 95% CI']; value += [mc[f'{ark}_95ci'][1]]; format += [fA]

    name += ['trials']; value += [mc['trials']]; format += ["#"]
    name += ['failed']; value += [mc['fails']]; format += ["#,##0"]

    return [name, value], format


def results_for_diseq(results, mc_summary=False):
    """
    'Diagram' disequilibrium ages.
    """
    name = []
    value = []
    format = []

    t = results['age']
    st = results['age_1s']
    ft, fst = util.vep_format(t, 2. * st, plims=(-3, 5))

    A48_init = True if results['[234U/238U]i'] is not None else False
    A08_init = True if results['[230Th/238U]i'] is not None else False

    mcr = results['mc']
    name += ['age (Ma)'];     value += [results['age']];     format += [ft]
    name += ['1σ (Ma)'];      value += [mcr['age_1s']];      format += [fst]
    name += ['lower 95% CI']; value += [mcr['age_95ci'][0]]; format += [ft]
    name += ['upper 95% CI']; value += [mcr['age_95ci'][1]]; format += [ft]

    if A48_init:
        ark = '[234U/238U]i'  # key
        A = results[ark]; sA = mcr[f'{ark}_1sd']
        fA48, fsA48 = util.vep_format(A, 2. * sA, plims=(-3, 5))
        name += ['init. [234U/238U]']; value += [results[ark]]; format += [fA48]
        name += ['1σ'];           value += [mcr[f'{ark}_1sd']];     format += [fsA48]
        name += ['lower 95% CI']; value += [mcr[f'{ark}_95ci'][0]]; format += [fA48]
        name += ['upper 95% CI']; value += [mcr[f'{ark}_95ci'][1]]; format += [fA48]

    if A08_init:
        ark = '[230Th/238U]i'  # key
        A = results[ark]; sA = mcr[f'{ark}_1sd']
        fA08, fsA08 = util.vep_format(A, 2. * sA, plims=(-3, 5))
        name += ['1σ'];           value += [mcr[f'{ark}_1sd']];     format += [fsA08]
        name += ['lower 95% CI']; value += [mcr[f'{ark}_95ci'][0]]; format += [fA08]
        name += ['upper 95% CI']; value += [mcr[f'{ark}_95ci'][1]]; format += [fA08]

    # other Monte Carlo stats
    name += ['median age (Ma)']; value += [mcr['median_age']];    format += [ft]
    if A48_init:
        name += [f'median [234U/238U]']; value += [mcr['median_[234U/238U]_i']]; format += [fA48]
    if A08_init:
        name += [f'median [230Th/238U]']; value += [mcr['median_[230Th/238U]_i']]; format += [fA08]

    name += ['MC trials']; value += [mcr['trials']]; format += ["#,##0"]
    name += ['MC failed']; value += [mcr['fails']]; format += ["#,##0"]

    if mc_summary:
        name += ['MC not converged']; value += [mcr['not_converged']]; format += ["#,##0"]
        name += ['MC negative age']; value += [mcr['negative_ages']]; format += ["#,##0"]
        name += ['MC negative ar']; value += [mcr['negative_ar']]; format += ["#,##0"]
        name += ['MC negative ar solution']; value += [mcr['negative_ar_soln']]; format += ["#,##0"]


    return [name, value], format


def results_for_mc(mcr, summary=False):
    """
    """
    name = []
    value = []
    format = []
    t = mcr['mean_age']
    st = mcr['age_95pm']
    ft, fst = util.vep_format(t, st, plims=(-3, 5))

    name += ['1σ (Ma)']; value += [mcr['age_1s']]; format += [fst]
    name += ['lower 95% CI']; value += [mcr['age_95ci'][0]]; format += [ft]
    name += ['upper 95% CI']; value += [mcr['age_95ci'][1]]; format += [ft]
    name += ['median age (Ma)']; value += [mcr['median_age']]; format += [ft]
    name += ['trials']; value += [mcr['trials']]; format += ["#,##0"]
    name += ['failed']; value += [mcr['fails']]; format += ["#,##0"]

    if summary:
        name += ['MC not converged']
        value += [mcr['not_converged']]
        format += ["#,##0"]
        name += ['MC negative ages']
        value += [mcr['negative_ages']]
        format += ["#,##0"]

    return [name, value], format


def results_for_bcar(mcr, arv='[234U/238U]_i'):
    """ """
    assert arv in ('[234U/238U]_i', '[230Th/238U]_i')
    name = []
    value = []
    format = []

    A = mcr[f'mean_{arv}']
    sA = mcr[f'1sd_{arv}']
    ft, fst = util.vep_format(A, 2. * sA, plims=(-3, 5))
    name += ['1σ'];      value += [mcr[f'1sd_{arv}']];      format += [fst]
    name += ['lower 95% CI']; value += [mcr[f'95ci_{arv}'][0]]; format += [ft]
    name += ['upper 95% CI']; value += [mcr[f'95ci_{arv}'][1]]; format += [ft]
    name += [f'mean {arv}']; value += [mcr[f'mean_{arv}']];    format += [ft]

    return [name, value], format


def results_for_diseq_pbu(results, mc_summary=False):
    """ """
    if results['age_type'] == 'mod-207Pb':
        age = ['Mod. 207Pb ages (Ma)']
    else:
        age = [f"Diseq. {combo.LONG_DATA_TYPES[results['age_type']]} age (Ma)"]

    age_1s = ['1σ (Ma)']
    upper_95ci = ['Lower 95% CI']
    lower_95ci = ['Upper 95% CI']

    format = [[None], [None], [None], [None]]
    n = len(results['age'])

    trials = ['MC trials']
    fails = ['MC fails']
    format += [[None], [None]]

    if mc_summary:
        num_cf = ['MC non-converged']
        num_rf = ['MC negative arv']
        num_af = ['MC negative age']
        format += [[None], [None], [None]]

    for i in range(n):
        age += [results['age'][i]]
        age_1s += [results['age_1s'][i]]
        upper_95ci += [results['age_95ci'][i][0]]
        lower_95ci += [results['age_95ci'][i][1]]

        fa, fe = util.vep_format(results['age'][i], 2. * results['age_1s'][i],
                                 plims=(-3, 5))
        format[0] += [fa]
        format[1] += [fe]
        format[2] += [fa]
        format[3] += [fa]

        trials += [results['mc']['trials']]
        fails += [results['mc']['fails'][i]]
        format[4] += ["#,##0"]
        format[5] += ["#,##0"]

        if mc_summary:
            num_cf += [results['mc']['not_converged'][i]]
            num_rf += [results['mc']['negative_ages'][i]]
            num_af += [results['mc']['negative_distr_coeff'][i]]
            format[6] += ["#,##0"]
            format[7] += ["#,##0"]
            format[8] += ["#,##0"]

    if mc_summary:
        return [age, age_1s, upper_95ci, lower_95ci, trials, fails,
                num_cf, num_rf, num_af], format
    return [age, age_1s, upper_95ci, lower_95ci, trials, fails], format


#==============================================================================
# Handle printing of user settings
#==============================================================================

def append_upb_const(opts, task_obj, series='both', U=True, eq=False):
    """ """
    if U:
        opts.append('238U/235U ratio: %s (%s)' % (task_obj.U, task_obj.sU))
    if series in ('both', '238U'):
        opts.append('𝝀238: %s (%s)' % (task_obj.lam238, task_obj.s238))
        if not eq:
            opts.append('𝝀234: %s (%s)' % (task_obj.lam234, task_obj.s234))
            opts.append('𝝀230: %s (%s)' % (task_obj.lam230, task_obj.s230))
            opts.append('𝝀226: %s (%s)' % (task_obj.lam226, task_obj.s226))
    if series in ('both', '235U'):
        opts.append('𝝀235: %s (%s)' % (task_obj.lam235, task_obj.s235))
        if not eq:
            opts.append('𝝀231: %s (%s)' % (task_obj.lam231, task_obj.s231))


def append_arv(opts, task_obj, series='both', fcA48i=False):
    """
    """
    if series in ('238U', 'both'):
        ar = [task_obj.A48, task_obj.A08, task_obj.A68]
        err = [task_obj.A48_err, task_obj.A08_err, task_obj.A68_err]
        types = [task_obj.A48_type, task_obj.A08_type]
        if fcA48i:
             ar[0] = err[0] = types[0] = 'n/a'
        opts.append(f'[234U/238], [230Th/238U], [226Ra/238U]: {tuple(ar)}')
        opts.append(f'[X/238] 1σ errors: {tuple(err)}')
        opts.append(f"[234U/238], [230Th/238U] types: (" + "".join(['initial '
                    if x == 'initial' else 'present ' for x in list(types)]) + ")")
    if series in ('[231Pa/235U]', 'both'):
        opts.append('[231Pa/235U]: %s' % task_obj.A15)
        opts.append('[231Pa/235U] 1σ error: %s' % task_obj.A15_err)


def append_mc_opts(opts, task_handler):
    """
    """
    opts.append('Monte Carlo trials: %s' % task_handler.mc_trials)
    opts.append('propogate decay const errors: %s' % task_handler.dc_errors)
    opts.append('propogate 238U/235U errors: %s' % task_handler.u_errors)
    opts.append('reject negative ages: %s' % task_handler.mc_rnages)
    opts.append('reject negative activity ratios: %s' % task_handler.mc_rnar)


#==============================================================================
# Apply user settings
#==============================================================================

def set_dqpb_config(obj, plot_type='data_point'):
    """
    plot_type : initial plot settings to load
    """

    # set constants
    cfg.U = obj.U
    cfg.sU = obj.sU

    # Decay constant values in 1/Ma and decay constant errors (1/Ma in 1σ
    # absolute).
    cfg.lam238 = obj.lam238 * 1e06
    cfg.lam234 = obj.lam234 * 1e06
    cfg.lam230 = obj.lam230 * 1e06
    cfg.lam226 = obj.lam226 * 1e06
    cfg.lam235 = obj.lam235 * 1e06
    cfg.lam231 = obj.lam231 * 1e06
    cfg.s238 = obj.s238 * 1e06
    cfg.s234 = obj.s234 * 1e06
    cfg.s230 = obj.s230 * 1e06
    cfg.s226 = obj.s226 * 1e06
    cfg.s235 = obj.s235 * 1e06
    cfg.s231 = obj.s231 * 1e06

    # set computation settings
    cfg.sec_eq = obj.secular_eq
    cfg.seed = np.random.default_rng(obj.rng_seed)

    cfg.h = obj.spines_h
    cfg.mswd_regression_thresholds = (obj.mswd_lim_lower, obj.mswd_lim_upper)
    cfg.mswd_wav_thresholds = (obj.wav_mswd_lim_lower, obj.wav_mswd_lim_upper)

    cfg.conc_age_bounds = (obj.eq_conc_min_age, obj.eq_conc_max_age)
    cfg.diseq_conc_age_bounds = [(obj.dq_conc_min_age_1, obj.dq_conc_max_age_1),
                                 (obj.dq_conc_min_age_2, obj.dq_conc_max_age_2),
                                 (obj.dq_conc_min_age_3, obj.dq_conc_max_age_3)]

    # non-kw, non-plot-specific settings
    cfg.sort_ages = obj.wav_sort_ages
    cfg.wav_marker_width = obj.wav_marker_width

    cfg.subplot_kw = {
        'facecolor': obj.fig_background_color,
    }

    # Plot format settings
    # -----------------------

    cfg.axis_labels_kw = {
        'color': obj.axis_label_font_color,
        'fontsize': obj.axis_label_font_size,
    }

    cfg.conc_age_ellipse_kw = {
        'alpha': obj.conc_age_ellipse_alpha,
        'edgecolor': obj.conc_age_ellipse_edge_color,
        'facecolor': obj.conc_age_ellipse_face_color,
        'linewidth': obj.conc_age_ellipse_edge_width,
        'zorder': obj.conc_age_ellipse_z
    }

    cfg.conc_env_kw = {
        'alpha': obj.conc_env_alpha,
        'edgecolor': obj.conc_env_edge_color,
        'facecolor': obj.conc_env_face_color,
        'linewidth': obj.conc_env_line_width,
        'linestyle': obj.conc_env_line_style,
        'zorder': obj.conc_env_z
    }

    cfg.conc_env_line_kw = {
        'alpha': obj.conc_env_line_alpha,
        'color': obj.conc_env_line_color,
        'linestyle': obj.conc_env_line_line_style,
        'linewidth': obj.conc_env_line_line_width,
        'zorder': obj.conc_env_line_z,
    }

    cfg.conc_intercept_ellipse_kw = {
        'alpha': obj.conc_intercept_ellipse_alpha,
        'facecolor': obj.conc_intercept_ellipse_face_color,
        'edgecolor': obj.conc_intercept_ellipse_edge_color,
        'linewidth': obj.conc_intercept_ellipse_line_width,
        'zorder': obj.conc_intercept_ellipse_z,
    }

    cfg.conc_intercept_markers_kw = {
        'alpha': obj.conc_intercept_marker_alpha,
        'markeredgecolor': obj.conc_intercept_marker_edge_color,
        'markerfacecolor': obj.conc_intercept_marker_face_color,
        'linewidth': 0,
        'markeredgewidth': obj.conc_intercept_marker_edge_width,
        'marker': obj.conc_intercept_marker_type,
        'markersize': obj.conc_intercept_marker_size,
        'zorder': obj.conc_intercept_marker_z,
    }

    # concordia line
    cfg.conc_line_kw = {
        'alpha': obj.conc_line_alpha,
        'color': obj.conc_line_color,
        'linestyle': obj.conc_line_style,
        'linewidth': obj.conc_line_width,
        'zorder': obj.conc_line_z,
    }

    # keep linewidth set to 0!
    cfg.conc_markers_kw = {
        'alpha': obj.conc_marker_alpha,
        'markeredgecolor': obj.conc_marker_edge_color,
        'markeredgewidth': obj.conc_marker_edge_width,
        'markerfacecolor': obj.conc_marker_face_color,
        'marker': obj.conc_marker_type,
        'markersize': obj.conc_marker_size,
        'linewidth': 0,
        'zorder': obj.conc_marker_z,
    }

    # Note: anootation_clip and clip_on options are crucial to avoid problems
    cfg.conc_text_kw = {
        'annotation_clip': False,
        'clip_on': True,
        'color':    obj.conc_text_color,
        'fontsize': obj.conc_text_font_size,
        'horizontalalignment': obj.conc_text_h_alignment,
        'textcoords': obj.conc_text_textcoords,
        'verticalalignment': obj.conc_text_v_alignment,
        'xytext': (obj.conc_text_x_offset, obj.conc_text_y_offset),
        'zorder':   obj.conc_text_z,
    }
    # with printing figures to Excel.

    cfg.dp_ellipse_kw = {
        'alpha': obj.data_ellipse_alpha,
        'edgecolor': obj.data_ellipse_edge_color,
        'facecolor': obj.data_ellipse_face_color,
        'linewidth': obj.data_ellipse_edge_width,
        'zorder': obj.data_ellipse_z
    }

    cfg.dp_label_kw = {
        'color': obj.data_label_font_color,
        'fontsize': obj.data_label_font_size,
        'horizontalalignment': obj.data_label_h_alignment,
        'verticalalignment': obj.data_label_v_alignment,
        'xytext': (obj.data_label_x_offset, obj.data_label_y_offset),
        'textcoords': obj.data_label_offset_coord,
        'zorder': obj.data_label_z,
    }

    cfg.gridlines_kw = {
        'alpha': obj.gridlines_alpha,
        'color': obj.gridlines_color,
        'linestyle': obj.gridlines_line_style,
        'linewidth': obj.gridlines_line_width,
    }

    cfg.hist_bars_kw = {
        "alpha": obj.histogram_alpha,
        "edgecolor": obj.histogram_edge_color,
        "facecolor": obj.histogram_face_color,
        "histtype": obj.histogram_hist_type,
        "linewidth": obj.histogram_line_width,
    }

    cfg.major_ticks_kw = {
        'color': obj.major_ticks_color,
        'direction': obj.major_ticks_direction,
        'size': obj.major_ticks_size,
        'width': obj.major_ticks_width,
    }

    cfg.minor_ticks_kw = {
        'color': obj.minor_ticks_color,
        'direction': obj.minor_ticks_direction,
        'size': obj.minor_ticks_size,
        'width': obj.minor_ticks_width,
    }

    cfg.pb76_line_kw = {
        'alpha': obj.pb76_line_alpha,
        'color': obj.pb76_line_color,
        'linestyle': obj.pb76_line_style,
        'linewidth': obj.pb76_line_width,
        'zorder': obj.pb76_line_z,
    }

    # fill between kwargs: https://matplotlib.org/stable/api/_as_gen/matplotlib.pyplot.fill_between.html
    cfg.renv_kw = {
        'alpha': obj.regression_env_alpha,
        'edgecolor': obj.regression_env_edge_color,
        'facecolor': obj.regression_env_face_color,
        'linewidth': obj.regression_env_line_width,
        'linestyle': obj.regression_env_line_style,
        'zorder': obj.regression_env_z
    }

    cfg.renv_line_kw = {
        'alpha': obj.regression_env_line_alpha,
        'color': obj.regression_env_line_color,
        'linewidth': obj.regression_env_line_line_width,
        'zorder': obj.regression_env_line_z,
    }

    cfg.rline_kw = {
        'alpha': obj.regression_line_alpha,
        'color': obj.regression_line_color,
        'linestyle': obj.regression_line_style,
        'linewidth': obj.regression_line_width,
        'zorder': obj.regression_line_z
    }

    # keep linewidth set to 0!
    cfg.scatter_markers_kw = {
        'alpha': obj.scatter_plot_marker_alpha,
        'linewidth': 0,
        'markeredgecolor': obj.scatter_plot_marker_edge_color,
        'markeredgewidth': obj.scatter_plot_marker_edge_width,
        'markerfacecolor': obj.scatter_plot_marker_face_color,
        'marker': obj.scatter_plot_marker_type,
        'markersize': obj.scatter_plot_marker_size,
        'zorder': obj.scatter_plot_marker_z,
    }

    cfg.wav_envelope_kw = {
        'alpha': obj.wav_envelope_alpha,
        'edgecolor': obj.wav_envelope_edge_color,
        'facecolor': obj.wav_envelope_face_color,
        'linestyle': obj.wav_envelope_line_style,
        'linewidth': obj.wav_envelope_line_width,
        'zorder': obj.wav_envelope_z
    }

    cfg.wav_line_kw = {
        'alpha': obj.wav_line_alpha,
        'color': obj.wav_line_color,
        'linestyle': obj.wav_line_style,
        'linewidth': obj.wav_line_width,
        'zorder': obj.wav_line_z,
    }

    # wav_marker_width parameter is implemented above.
    cfg.wav_markers_kw = {
        'alpha': obj.wav_marker_alpha,
        'color': obj.wav_marker_face_color,
        'zorder': obj.wav_marker_z,
    }

    cfg.wav_markers_rand_kw = {
        'alpha': obj.wav_rand_marker_alpha,
        'color': obj.wav_rand_marker_face_color,
        'zorder': obj.wav_marker_z,
    }

    cfg.wav_fig_kw = {
        'dpi': obj.wav_dpi,
        'facecolor': obj.fig_border_color,
        'figsize': (obj.wav_width, obj.wav_height),
    }

    set_plot_config(obj, plot_type=plot_type)


def set_plot_config(obj, plot_type='data_point'):
    """
    """
    assert plot_type in ('data_point', 'intercept',  'wav', 'histogram')

    if plot_type == 'data_point':  # isochron/data point plot
        cfg.comma_sep_thousands = obj.dpp_comma_sep_thousands
        cfg.exp_font_size = 9  # axis exponent multiplier label
        cfg.hide_right_spine = obj.dpp_hide_spines
        cfg.hide_top_spine = obj.dpp_hide_spines
        cfg.sci_limits = (obj.dpp_lower_exp, obj.dpp_upper_exp)
        cfg.show_major_gridlines = obj.dpp_major_gridlines
        cfg.show_minor_gridlines = obj.dpp_minor_gridlines
        cfg.show_minor_ticks = obj.dpp_minor_ticks
        cfg.tick_label_size = 9

        cfg.age_prefix = obj.dpp_age_prefix
        cfg.every_second_threshold = obj.dpp_label_every_second
        cfg.individualised_labels = obj.dpp_individual_labels
        cfg.offset_factor = obj.dpp_label_offset_factor
        cfg.perpendicular_rotation = obj.dpp_rotate_perpendicular
        cfg.prefix_in_label = obj.dpp_age_prefix_in_label
        cfg.remove_overlaps = obj.dpp_avoid_label_overlaps
        cfg.rotate_conc_labels = obj.dpp_rotate_labels

        cfg.fig_kw = {
            'figsize': (obj.dpp_width, obj.dpp_height),
            'dpi': obj.dpp_dpi,
            'facecolor': obj.fig_border_color,
        }

    elif plot_type == 'intercept':
        cfg.comma_sep_thousands = obj.int_comma_sep_thousands
        cfg.exp_font_size = 9  # axis exponent multiplier label
        cfg.hide_right_spine = obj.int_hide_spines
        cfg.hide_top_spine = obj.int_hide_spines
        cfg.sci_limits = (obj.int_lower_exp, obj.int_upper_exp)
        cfg.show_major_gridlines = obj.int_major_gridlines
        cfg.show_minor_gridlines = obj.int_minor_gridlines
        cfg.show_minor_ticks = obj.int_minor_ticks
        cfg.tick_label_size = 9

        cfg.age_prefix = obj.int_age_prefix
        cfg.every_second_threshold = obj.int_label_every_second
        cfg.individualised_labels = obj.int_individualised_labels
        cfg.offset_factor = obj.int_label_offset_factor
        cfg.perpendicular_rotation = obj.int_rotate_perpendicular
        cfg.prefix_in_label = obj.int_age_prefix_in_label
        cfg.remove_overlaps = obj.int_avoid_label_overlaps
        cfg.rotate_conc_labels = obj.int_rotate_labels

        cfg.fig_kw = {
            'figsize': (obj.int_width, obj.int_height),
            'dpi': obj.int_dpi,
            'facecolor': obj.fig_border_color,
        }

    elif plot_type == 'wav':
        cfg.comma_sep_thousands = obj.wav_comma_sep_thousands
        cfg.hide_right_spine = obj.wav_hide_spines
        cfg.hide_top_spine = obj.wav_hide_spines
        cfg.sci_limits = (obj.wav_lower_exp, obj.wav_upper_exp)
        cfg.show_major_gridlines = obj.wav_major_gridlines
        cfg.show_minor_gridlines = obj.wav_minor_gridlines
        cfg.show_minor_ticks = obj.wav_minor_ticks

    elif plot_type.startswith('hist'):
        cfg.comma_sep_thousands = obj.hist_comma_sep_thousands
        cfg.hide_right_spine = False
        cfg.hide_top_spine = False
        cfg.sci_limits = (obj.hist_lower_exp, obj.hist_upper_exp)
        cfg.show_major_gridlines = obj.hist_major_gridlines
        cfg.show_minor_gridlines = obj.hist_minor_gridlines
        cfg.show_minor_ticks = obj.hist_minor_ticks


    else:
        raise ValueError('plot type not recognised')