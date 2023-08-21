from matplotlib.offsetbox import AnchoredText

import numpy as np
import pandas as pd
import xarray as xr
import matplotlib.pyplot as plt

def title_axes(ax):
    ax.set_xlabel( ax.get_xlabel().title())
    ax.set_ylabel( ax.get_ylabel().title())
    
def percentage_scale(baseline, ax):
    lim = ax.get_ylim()
    ax2 = ax.twinx()
    delta = (lim - baseline)/ baseline * 100
    ax2.set_ylabel('[percentage]')
    ax2.set_ylim(delta)
    return ax2
    
def annotate_percentage_difference(recent_mean, baseline_mean, loc, ax):
    if loc is None:
        loc='upper right'
        
    delta = (recent_mean - baseline_mean)/ baseline_mean * 100
    annotate_text = "Change: {:.1f}%".format(delta.values)
    #at = AnchoredText(annotate_text, prop=dict(size=10), frameon=False, loc=loc)
    at = AnchoredText(annotate_text, frameon=False, loc=loc)
    ax.add_artist(at)
    
    
    
def mean_and_se(ds, dim):
    mean = ds.mean(dim=dim)
    se = ds.std(dim=dim) / np.sqrt(ds.sizes[dim])
    return mean, se

    
def plot_mean_error(ds, period, color, ax, linewidth=2, extend=None):
    # ds.sel(river=labels(network1)).sum(dim='river').sel(year=ds.year.dt.year.isin(period))    
    mean, se = mean_and_se(ds, dim='year')

    xmin = pd.to_datetime(str(period[0]))
    xmax = pd.to_datetime(str(period[-1]))
    ax.hlines(y=mean, xmin=xmin, xmax=xmax, linewidth=linewidth, color=color)
    ax.hlines(y=mean+1.96*se, xmin=xmin, xmax=xmax, linewidth=1, ls='-', color=color)
    ax.hlines(y=mean-1.96*se, xmin=xmin, xmax=xmax, linewidth=1, ls='-', color=color)
    
    if extend:
        extend =  pd.to_datetime(str(extend))
        ax.hlines(y=mean, xmin=xmax, xmax=extend, linewidth=linewidth, ls='dotted', color=color)


def running_average_plot(ds1,
                         period1,
                         period2,
                         ds2=None, 
                         ax=None,
                         loc=None):
    if ax is None:
        fig, ax = plt.subplots()
    
    p1_ds = ds1.sel(year=ds1.year.dt.year.isin(period1))
    p1_mean = p1_ds.mean()

    if ds2 is None:
        ds2 = ds1

    p2_ds = ds2.sel(year=ds2.year.dt.year.isin(period2))
    p2_mean = p2_ds.mean()
   
    plot_mean_error(ds=p1_ds,
                    period=period1,
                    color='red',
                    extend=period2[0],
                    ax=ax)
    
    plot_mean_error(ds=p2_ds,
                    period=period2,
                    color='black',
                    ax=ax)

    ds1.plot(marker='o', color='k', linestyle='None', markeredgecolor='k', markerfacecolor='None', ax=ax)
    ds2.plot(marker='o', color='k', linestyle='None', markeredgecolor='k', markerfacecolor='k', ax=ax)

    annotate_percentage_difference(p2_mean, p1_mean, loc, ax)
    #annotate_difference(p2_mean, loc, ax)
    title_axes(ax)

    

def append_total(ds, label='Statewide', mode='load', da=None):
    if mode=='load':
        total = ds.sum(dim='river')
    
    elif mode=='yield':
        total = ds.sum(dim='river')/da.sum()
        ds = ds/da
    
    return xr.concat([total.assign_coords({"river":label}), ds], dim='river')


#def plot_change_by_basin(period1_ds, period2_ds, ax=None, color='k', statewide=False):
def plot_change_by_basin(period1_ds, period2_ds,
                         ax=None, color='k',
                         mode='load', da=None):
    '''
    ds1 = ambient_loads[parameter].sel(year=ambient_loads.year.dt.year.isin(baseline_years)).mean(dim='year')
    ds2 = supergage_loads[parameter].sel(year=supergage_loads.year.dt.year.isin(study_years)).mean(dim='year')
    '''
    if ax is None:
        fig, ax = plt.subplots()
        
        
    # compute standard error of baseline
    #(p1-p2) / p3
    # first compute error in p1-p2
    #div = period1_ds.mean(dim='year')
    #if statewide:
    #    div = div.sum()
    title = period1_ds.name
    
    # append total
    period1_ds = append_total(period1_ds, mode=mode, da=da)
    period2_ds = append_total(period2_ds, mode=mode, da=da)
    
    #if not statewide:
    #    div = period1_ds.mean(dim='year')

    mean1, se1 = mean_and_se(period1_ds, dim='year')
    mean2, se2 = mean_and_se(period2_ds, dim='year')#ds.mean()
        
    difference = (mean2 - mean1).to_series()
    difference_se = np.sqrt(se1**2 + se2**2).to_series()

        
    #difference = difference/div.values * 100
    #difference_se = difference_se/div.values * 100
    
    # append total
    #period1_ds = append_total(period1_ds, mode=mode, da=da)
    #period2_ds = append_total(period2_ds, mode=mode, da=da)
    
    
    # compute percent contribution to statewide change
    #if statewide:
    #    difference /= difference['Statewide'] * 0.01
    #    difference_se /= difference_se['Statewide'] * 0.01

    #title = period1_ds.name.title()
    
    difference.plot.bar(ax=ax, yerr=difference_se*1.96, color=color, edgecolor='k', capsize=4)
    
    units = period1_ds.pint.units
    ax.set_ylabel(f'{title} [{units}]'.capitalize())
    ax.set_xlabel('')
    ax.axhline(y=0, lw=1, color='k')
    