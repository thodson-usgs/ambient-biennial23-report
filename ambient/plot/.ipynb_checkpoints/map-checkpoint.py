import pandas as pd
import matplotlib.pyplot as plt

from awqmn import sites, storet
from awqmn.plot import trend_scale, p_analysis_name, plot_watersheds, plot_trend_map
from awqmn.plot import egret_trend_scale, plot_egret_trend_map, to_gdf
from awqmn.trend import get_trend_data, get_egret_trend_data, water_year_end, water_year_start
from awqmn.trend import max_egret_trend

def plot_sen_map(con, site_df, parameter, interval, ax, max_markersize=120,
                 **kwargs):
    alpha=0.15
    alpha2=0.3
    scale = trend_scale(con, parameter, alpha=alpha, 
                        max_markersize=max_markersize)
    
    sen, mk, count = get_trend_data(con, parameter, 
                                    start=interval[0], end=interval[1])
    
    plot_trend_map(sen, mk, count, site_df, parameter, huc8=huc8, 
                   flowline=flowline, state=illinois,
                   ax=ax, 
                   title=False,
                   scale=scale, 
                   alpha=alpha, 
                   alpha2=alpha2,
                   site_markersize=0.4,
                   watershed_lw = 0.1,
                   **kwargs)
    
    ax.set_xlim((-444980.24838310183, 795451.9403487985))
    ax.set_ylim((10360.515460701587, 2237569.5535490126))
        
    
def plot_egret_map(con, site_df, parameter, interval, f_or_c,
                   ax, max_markersize=120, table='nrec.wrtds_out',
                   **kwargs):
    alpha=0.85
    alpha2=0.7
    
    scale = egret_trend_scale(con, parameter, alpha=alpha, f_or_c=f_or_c,
                              max_markersize=max_markersize, trend_test='lbt', table=table)
    trend_df = get_egret_trend_data(con, parameter, start=interval[0], end=interval[1], table=table)

    plot_egret_trend_map(trend_df, site_df, parameter=parameter, huc8=huc8,
                         flowline=flowline, state=illinois,
                         f_or_c=f_or_c,
                         ax=ax, 
                         scale=scale,
                         alpha=alpha, alpha2=alpha2,
                         site_markersize=0.4,
                         watershed_lw=0.1,
                         trend_test='lbt',
                         **kwargs)
    
    ax.set_xlim((-444980.24838310183, 795451.9403487985))
    ax.set_ylim((10360.515460701587, 2237569.5535490126))

def concentration_change(con, parameter_name, start, end, alpha=None):
    """ Multiplies sen slope by the length of the monitoring interval to get total change
    """
    parameter_name = parameter_name[:63] #prep for sql
    start_wy = water_year_start(start)
    end_wy = water_year_end(end)

    query = f"""
    SELECT site, "start", "end", "{parameter_name}" as sen, mk
    FROM nrec.trend_sen
    INNER JOIN (SELECT site, "start", "end", "{parameter_name}" 
    as mk FROM nrec.trend_mk) as trend_mk
    USING (site, "start", "end")
    WHERE "start"={start} and "end"={end}
    """
    if alpha:
        query = query + f'AND "mk"<={alpha};'

    else:
        query = query + ';'

    df = pd.read_sql_query(query, con)

    # get slope interval
    query = f"""
    SELECT "{storet.cols.site_id}" as site, MIN("{storet.cols.date}"), 
    MAX("{storet.cols.date}"), COUNT(*) as count
    FROM nrec.merged_results
    WHERE "{parameter_name}" IS NOT NULL
    AND ("{storet.cols.date}" BETWEEN '{start_wy}' AND '{end_wy}')
    GROUP BY "{storet.cols.site_id}"
    """

    interval_df = pd.read_sql_query(query, con)
    period = interval_df['max'] - interval_df['min']
    interval_df['dec_yr'] = period.dt.days/365.25
    out = df.merge(interval_df, on='site')
    out['change'] = out['sen']*out['dec_yr']
    out = out[['site','change', 'mk','count']]
    
    return out


def concentration_scale(con, parameter_name, parameter_cd,
                        alpha=0.15, max_markersize=120, egret_test='lbt',
                        omit_egret=None):
    # get max egret change
    #TODO fix
    start = ['1978','2008']
    end = '2017'

    egret_max = max_egret_trend(con, parameter_cd, column='c', 
                                alpha=1-alpha, trend_test=egret_test,
                                omit=omit_egret)

    # get max sen change
    sen_df = concentration_change(con, parameter_name, start[0], end, alpha=alpha)
    sen_max = sen_df.change.abs().max()

    sen2_df = concentration_change(con, parameter_name, start[1], end, alpha=alpha)
    sen2_max = sen2_df.change.abs().max()
    max_change = max(egret_max, sen_max, sen2_max)
    scale = max_markersize/max_change

    return scale


def plot_change(trend_gdf, column, ax=None, max_markersize=150, 
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
    trend_gdf.loc[trend_gdf['mk']==1,'mk'] = 1

    #check alpha2
    if alpha2:
        # find trends within second alpha range
        a2_index = (trend_gdf['mk'] > alpha) & (trend_gdf['mk'] <= alpha2)
        trend2_gdf = trend_gdf[a2_index]
        pos2_trend = trend2_gdf[trend2_gdf['change'] > 0]
        neg2_trend = trend2_gdf[trend2_gdf['change'] < 0]

    trend_gdf = trend_gdf[trend_gdf['mk'] <= alpha].copy() #XXX check this
    pos_trend = trend_gdf[trend_gdf['change'] > 0]
    neg_trend = trend_gdf[trend_gdf['change'] < 0]

    max_trend = trend_gdf['change'].abs().max()

    if kwargs.get('scale'):
        scale = kwargs.get('scale')
    else:
        scale = max_markersize/max_trend
    
    if not pos_trend.empty:
        pos_trend.plot(markersize=pos_trend['change']*scale, ax = ax,
                        color='#D7191C', edgecolor='none', alpha=0.2) #reddish
        
    if not neg_trend.empty:
        neg_trend.plot(markersize=neg_trend['change']*scale*-1, ax = ax,
                       color='#2C7BB6', edgecolor='none', alpha=0.2) # blueish

    # plot alpha 2 range
    if alpha2 and not pos_trend.empty:
        pos2_trend.plot(markersize=pos2_trend['change']*scale, ax = ax, 
                       edgecolor='#D7191C',
                       facecolor='none', lw=lw, alpha=0.15) #reddish
        
    if alpha2 and not neg_trend.empty:
        neg2_trend.plot(markersize=neg2_trend['change']*scale*-1, ax = ax,
                       edgecolor='#2C7BB6',
                       facecolor='none', lw=lw, alpha=0.15) # blueish

    ax.set_aspect('equal')
    ax.set_axis_off()
    

def plot_change_map(change_df, site_df, parameter, huc8, 
                   flowline=None, state=None, daterange=None, ax=None, 
                   title=True, alpha=0.05, alpha2=None, **kwargs):
    """ Plot a map of trend magnitudes, sites, watersheds, and flowlines
    """
    if ax is None:
        fig, ax = plt.subplots()
    
    plot_watersheds(huc8, flowline=flowline, state=state, ax=ax)
    change_df = change_df[change_df['count'] > 50].copy()
    
    if not change_df.empty:
        change_df = change_df.set_index('site')
        df = sites.merge_site_info(change_df, site_df)
        gdf = to_gdf(df)
        plot_change(gdf, parameter, ax, alpha=alpha, alpha2=alpha2, **kwargs)
    
    if title:
        title_text = p_analysis_name(parameter)
        ax.set_title(f'{title_text}:\n{daterange}', **kwargs)
    
    else:
        
        if kwargs.get('fontsize'):
            fontsize=kwargs.get('fontsize')
        else:
            fontsize=10
            
        ax.text(.5, 0, daterange, fontsize=fontsize)

