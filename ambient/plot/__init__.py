import pandas as pd
import geopandas as gpd
from shapely.geometry import Point

import matplotlib.pyplot as plt

from ambient import sites 
from ambient.trend import max_trend, max_egret_trend, max_egret_yield_trend
from ambient import crosswalk


def plot_watersheds(huc8, flowline=None, state=None, ax=None, 
                    watershed_lw=0.1, **kwargs):
    """ Plot watersheds, flowlines and state boundary

    Parameters
    ----------
    huc8 : GeoDataFrame
    flowline : GeoDataFrame
    state : GeoDataFrame
    ax : ax
    """
    if ax is None:
        fig, ax = plt.subplots()
        
    huc8.plot(ax=ax,
              facecolor='none',
              edgecolor='black',
              linewidth=watershed_lw)
    
    if flowline is not None:
        #rivers = flowline[flowline['StreamOrde'] == 2]
        big_rivers = flowline[flowline['StreamOrde'] > 3]
    
        #rivers.plot(ax=ax,
        #            linewidth=0.1, alpha=0.6)
    
        big_rivers.plot(ax=ax,
                        linewidth=watershed_lw*2, alpha=0.4, color='navy') #l. blue
    
    if state is not None:
        state.plot(facecolor='none', edgecolor='black', alpha=0.5, 
                   lw=watershed_lw*2, ax=ax)
    
    ax.set_aspect('equal')
    ax.set_axis_off()


def plot_trend(trend_gdf, mk_df, column, ax=None, max_markersize=150, 
               site_markersize=3, alpha=0.05, alpha2=None, lw=0.5, **kwargs):
    """Plot a map of trend magnitudes (Sen's slope).
    
    Parameters
    ----------
    trend_gdf : GeoDataFrame
        Table with columns containing parameter trends and rows for each site.
    
    mk_df : DataFrame
    
    column : str
        Column in trend_gdf containing trend data.
    """
    if ax is None:
        fig, ax = plt.subplots()
    trend_gdf.plot(color='black', markersize=site_markersize, ax=ax,
                   edgecolor='none')
    #trend_gdf.plot.scatter(color='black', s=site_markersize, ax=ax)
    mk_df[mk_df.isna()] = 1

    #check alpha2
    if alpha2:
        # find trends within second alpha range
        a2_index = (mk_df[column] > alpha) & (mk_df[column] <= alpha2)
        trend2_gdf = trend_gdf[a2_index]
        pos2_trend = trend2_gdf[trend2_gdf[column] > 0]
        neg2_trend = trend2_gdf[trend2_gdf[column] < 0]

    trend_gdf = trend_gdf[mk_df[column] <= alpha].copy() #XXX check this
    pos_trend = trend_gdf[trend_gdf[column] > 0]
    neg_trend = trend_gdf[trend_gdf[column] < 0]

    max_trend = trend_gdf[column].abs().max()

    if kwargs.get('scale'):
        scale = kwargs.get('scale')
    else:
        scale = max_markersize/max_trend
    
    if not pos_trend.empty:
        pos_trend.plot(markersize=pos_trend[column]*scale, ax = ax, 
                       color='#D7191C', edgecolor='none',alpha=0.6) #reddish
        
    if not neg_trend.empty:
        neg_trend.plot(markersize=neg_trend[column]*scale*-1, ax = ax,
                       color='#2C7BB6', edgecolor='none', alpha=0.6) # blueish

    # plot alpha 2 range
    if alpha2 and not pos_trend.empty:
        pos2_trend.plot(markersize=pos2_trend[column]*scale, ax = ax, 
                       edgecolor='#D7191C',
                       facecolor='none', lw=lw, alpha=0.8) #reddish
        
    if alpha2 and not neg_trend.empty:
        neg2_trend.plot(markersize=neg2_trend[column]*scale*-1, ax = ax,
                       edgecolor='#2C7BB6',
                       facecolor='none', lw=lw, alpha=0.8) # blueish

    ax.set_aspect('equal')
    ax.set_axis_off()
    

def plot_trend_map(sen_df, mk_df, count_df, site_df, parameter, huc8, 
                   flowline=None, state=None, daterange=None, ax=None, 
                   title=True, alpha=0.05, alpha2=None, **kwargs):
    """ Plot a map of trend magnitudes, sites, watersheds, and flowlines
    """
    if ax is None:
        fig, ax = plt.subplots()
    
    plot_watersheds(huc8, flowline=flowline, state=state, ax=ax)
    sen_df = sen_df[count_df.values > 50].copy()
    mk_df = mk_df[count_df.values > 50].copy()
    
    if not sen_df.empty:
        df = sites.merge_site_info(sen_df, site_df)
        gdf = to_gdf(df)
        plot_trend(gdf, mk_df, parameter, ax, alpha=alpha, alpha2=alpha2, **kwargs)
    
    if title:
        title_text = p_analysis_name(parameter)
        ax.set_title(f'{title_text}:\n{daterange}', **kwargs)
    
    else:
        
        if kwargs.get('fontsize'):
            fontsize=kwargs.get('fontsize')
        else:
            fontsize=10
            
        ax.text(.5, 0, daterange, fontsize=fontsize)


def plot_sites(gdf, huc8, flowline=None, state=None, ax=None):
    """ Plot site locations with watersheds, flowlines, and state boundary.
    """
    if ax is None:
        fig, ax = plt.subplots()
    
    plot_watersheds(huc8, flowline=flowline, state=state, ax=ax)
    gdf.plot(color='black', markersize=3, marker='.', ax=ax)


#def trend_scale(trend_df, mk_df, column, max_markersize, alpha=0.05):
 #   #trend = trend_df[~mk_df[column].isna()]
 #   trend = trend_df[mk_df[column] < alpha]
 #   max_trend = trend[column].abs().max()
 #   
 #   scale = max_markersize/max_trend
 #   return scale
    

def to_gdf(df):
    df = df.copy()
    crs_string = '+proj=tmerc +lat_0=36.66666666666666 +lon_0=-88.33333333333333 +k=0.9999749999999999 +x_0=152400.3048006096 +y_0=0 +datum=NAD27 +units=us-ft +no_defs'
    #df = sites.merge_site_info(trend_df, site_df)
    df['Coordinates'] = list(zip(df[sites.cols.lon], df[sites.cols.lat]))
    df['Coordinates'] = df['Coordinates'].apply(Point)
    out =  gpd.GeoDataFrame(df, geometry='Coordinates')
    out.crs = {'init': 'epsg:4326', 'no_defs': True}
    return out.to_crs(crs_string)

def _get_egret_nhst_trend(egret_gdf, alpha, alpha2, f_or_c):
    """
    """
    if f_or_c == 'c':
        p_col = 'pvalc' #probability of rejecting No incorrectly
        t_col = 'estc'  #trendi

    elif f_or_c =='f':
        p_col = 'pvalf'
        t_col = 'estf'

    trend = egret_gdf[egret_gdf[p_col] < alpha]
    max_trend = trend[t_col].abs().max() #TODO use appropriate trend test
    
    if alpha2:
        # find trends within second alpha range
        a2_index = (egret_gdf[p_col] > alpha) & (egret_gdf[p_col] <= alpha2)
        #trend2 = egret_gdf[egret_gdf[p_col] > alpha & egret_gdf[p_col] <= alpha2]
        trend2 = egret_gdf[a2_index]
        pos2_trend = trend2[trend2[t_col] > 0]
        neg2_trend = trend2[trend2[t_col] < 0]

    trend = egret_gdf[egret_gdf[p_col] < alpha]

    pos_trend = trend[trend[t_col]>0]
    neg_trend = trend[trend[t_col]<0]

    return pos_trend, neg_trend, pos2_trend, neg2_trend, max_trend

def _get_egret_lbt_trend(egret_gdf, alpha, alpha2, f_or_c):
    """
    """
    p_col_up = 'like' + f_or_c + 'up'
    p_col_down = 'like' + f_or_c + 'down'
    t_col = 'est' + f_or_c

    trend_up = egret_gdf[egret_gdf[p_col_up] > alpha]
    trend_down = egret_gdf[egret_gdf[p_col_down] > alpha]
    max_trend = max(trend_up[t_col].abs().max(),
                    trend_down[t_col].abs().max())
    
    if alpha2:
        # find trends within second alpha range
        #a2_index = (egret_gdf[p_col] > alpha) & (egret_gdf[p_col] <= alpha2)
        a2_up_i = (egret_gdf[p_col_up] < alpha) & (egret_gdf[p_col_up] >= alpha2)
        a2_down_i = (egret_gdf[p_col_down] < alpha) & (egret_gdf[p_col_down] >= alpha2)
        #trend2 = egret_gdf[egret_gdf[p_col] > alpha & egret_gdf[p_col] <= alpha2]
        trend2_up = egret_gdf[a2_up_i]
        trend2_down = egret_gdf[a2_down_i]

    return trend_up, trend_down, trend2_up, trend2_down, max_trend


def plot_egret_trend(egret_gdf, ax=None, max_markersize=150, f_or_c='c',
                     trend_test='nhst',
                     site_markersize=3, alpha=0.1, alpha2=None, lw=0.5, **kwargs):
    """ Plot
    """
    t_col = 'est' + f_or_c
    #import pdb; pdb.set_trace()
    if trend_test == 'nhst':
        pos, neg, pos2, neg2, max_trend = _get_egret_nhst_trend(egret_gdf, alpha,
                                                                alpha2, f_or_c)
    elif trend_test == 'lbt':
        pos, neg, pos2, neg2, max_trend = _get_egret_lbt_trend(egret_gdf, alpha,
                                                               alpha2, f_or_c)
    if ax is None:
        fig, ax = plt.subplots()

    #TODO only select sites with data
    egret_gdf.plot(color='black', markersize=site_markersize,
                   edgecolor='none', ax=ax)

    if kwargs.get('scale'):
        scale = kwargs.get('scale')
    else:
        scale = max_markersize/max_trend
    
    if not pos.empty:
        pos.plot(markersize=pos[t_col]*scale, ax = ax, 
                       color='#D7191C', edgecolor='none', alpha=0.6)
        
    if not neg.empty:
        neg.plot(markersize=neg[t_col]*scale*-1, ax = ax,
                       color='#2C7BB6', edgecolor='none', alpha=0.6)

    # plot alpha 2 range
    if alpha2 and not pos2.empty:
        pos2.plot(markersize=pos2[t_col]*scale, ax = ax, 
                        edgecolor='#D7191C',
                        facecolor='none', lw=lw, alpha=0.8) #reddish
        
    if alpha2 and not neg2.empty:
        neg2.plot(markersize=neg2[t_col]*scale*-1, ax = ax,
                        edgecolor='#2C7BB6',
                        facecolor='none', lw=lw, alpha=0.8) # blueish


    ax.set_aspect('equal')
    ax.set_axis_off()


def plot_trend_type(type_gdf, ax=None, markersize=10, lw=0.2, **kwargs):
    labels = {
    ('mtc', 1): ['red','^'],
    ('mtc', -1): ['red','v'],
    ('qtc', 1) : ['blue','^'],
    ('qtc', -1) : ['blue','v'],
    ('amplifying', 1) : ['purple','^'],
    ('amplifying', -1) : ['purple','v'],
    ('countering', 1) : ['purple','x'],
    ('countering', -1) : ['purple','x'],
    ('balanced', 1) : ['black','x'],
    ('balanced', -1) : ['black','x'],
    ('stable', 1) : ['black','.'],
    ('stable', -1) : ['black','.'],
    }

    if ax is None:
        fig, ax = plt.subplots()

    for name, group in type_gdf.groupby(['gfn_class','sign']):
        color = labels[name][0]
        marker = labels[name][1]
        group.plot(ax=ax, color=color, marker=marker, markersize=markersize, 
                   alpha=0.7, **kwargs)

    #type_gdf.groupby('gfn_class').plot(markersize=markersize, ax=ax, **kwargs)


    ax.set_aspect('equal')
    ax.set_axis_off()


def plot_egret_trend_map(egret_df, site_df, parameter, huc8, flowline=None, state=None,
                         subtitle=None, ax=None, title=None, type_map=False, **kwargs):
    """ Plots EGRETci output, sites, hucs, flowlines, and date boundary
    """
    if ax is None:
        fig, ax = plt.subplots()
    
    plot_watersheds(huc8, flowline=flowline, state=state, ax=ax)
    egret_df = egret_df.set_index('site_no')
    df = sites.merge_site_info(egret_df, site_df, org='USGS')
    #import pdb; pdb.set_trace()
    gdf = to_gdf(df)

    if not type_map:
        plot_egret_trend(gdf, ax, **kwargs)
    
    else:
        #return gdf
        plot_trend_type(gdf, ax, **kwargs)

    if title:
        title_text = p_analysis_name(parameter)
        ax.set_title(f'{title_text}:\n{subtitle}', **kwargs)
    
    else:
        if kwargs.get('fontsize'):
            fontsize=kwargs.get('fontsize')
        else:
            fontsize=10
            
        ax.text(.5, 0, subtitle, fontsize=fontsize)


def p_analysis_name_from_parm_cd(parm_cd, con):
    query = f"""
    SELECT * FROM nrec.srsnames WHERE parm_cd={parm_cd};
    """
    df = pd.read_sql_query(query, con)
    parameter_name = crosswalk.analysis_name(df.iloc[0])
    return p_analysis_name(parameter_name)


def p_analysis_name(analysis_name):
    """ Format analysis name for printing

    Parameters
    ----------
    analysis_name : string
        The name of the analysis as it appears in columns of the trend tables
    """
    i_space = analysis_name.find(' ')
    analysis_name = list(analysis_name)
    analysis_name[i_space + 1] = analysis_name[i_space + 1].lower()
    analysis_name = ''.join(analysis_name)
    # replace parantheses
    analysis_name = analysis_name.replace('<','(').replace('>',')')

    if analysis_name == 'Dissolved total dissolved solids':
        analysis_name = 'Total dissolved solids'

    elif analysis_name == 'Total kjeldahl nitrogen':
        analysis_name = 'Total Kjeldahl nitrogen'
    
    elif analysis_name == 'Total alkalinity, total':
        analysis_name = 'Total alkalinity'
    
    elif analysis_name == 'Temperature, water':
        analysis_name = 'Water temperature'
    
    elif analysis_name == 'Hardness, ca, Mg':
        analysis_name = 'Hardness, Ca, Mg'

    elif analysis_name == 'Total pH':
        analysis_name = 'pH'

    elif analysis_name == 'Non-filterable total suspended solids':
        analysis_name = 'Total suspended solids'

    elif analysis_name == 'Non-filterable volatile suspended solids':
        analysis_name = 'Volatile suspended solids'

    return analysis_name


def trend_scale(con, parameter, max_markersize=600, alpha=0.05, egret=False):
    """
    """
    if egret:
        trend = max_egret_trend(con, parameter, alpha)
    else:
        trend = max_trend(con, parameter, alpha)
    #trend = trend_df[mk_df[column] < alpha] 
    if trend == 0:
        scale = 0
    else:
        scale = max_markersize/trend

    return scale


def egret_trend_scale(con, parameter, max_markersize=600, alpha=0.05, f_or_c='c',
                      trend_test='nhst', yld=False,
                      table='nrec.wrtds_out', omit=None):
    """
    """
    if yld:
        trend = max_egret_yield_trend(con, parameter, alpha=alpha, omit=omit,
                                      table=table)
    else:
        trend = max_egret_trend(con, parameter, column=f_or_c, alpha=alpha,
                                trend_test=trend_test, omit=omit, table=table)
    if trend is None:
        return 0
    else:
        scale = max_markersize/trend
        return scale
