from trend import seasonal_sen_slope, seasonal_mann_kendall
from awqmn import storet
import pandas as pd

def water_year_start(year):
    year = str(int(year) - 1)
    return year + '-10-1'


def water_year_end(year):
    year = str(year)
    return year + '-9-30'


def run_trend_analysis(con, start_yr=None, end_yr=None):
    """
    """
    # generate a list of sites
    sites = get_site_list(con=con)

    for site in sites:
        _run_trend_analysis_for_site(con, site,
                                     start_yr=start_yr,
                                     end_yr=end_yr)


def _run_trend_analysis_for_site(con, site, 
                                 start_yr, end_yr,
                                 table='merged_results'):
    """
    """
    start = water_year_start(start_yr)
    end = water_year_end(end_yr)

    query=f"""
    SELECT * FROM nrec.{table}
    WHERE "{storet.cols.site_id}" = '{site}'
    AND ("{storet.cols.date}" BETWEEN '{start}' AND '{end}') ORDER BY "{storet.cols.date}";
    """

    df = pd.read_sql_query(query, con=con)
    df = df.set_index(pd.to_datetime(df[storet.cols.date]))
    df = df.sort_index()
    df = df.drop([storet.cols.site_id, storet.cols.date], axis=1)
    # keep only the first sample in a given month
    df = df.resample('M').first()
    #only run trend test on columns with data
    data_cols = df.columns[df.any().values] #list columns with data
    sen_temp = df[data_cols].apply(seasonal_sen_slope)
    mk_temp = df[data_cols].apply(seasonal_mann_kendall)
    count = df.count()
    sen = pd.Series(index=df.columns)
    mk = sen.copy()
    sen[data_cols] = sen_temp
    mk[data_cols] = mk_temp

    # XXX Assuming no columns are removed for lack of data
    # ,otherwise we need to create table in advance,
    # add trend results to database

    if type(sen) == pd.Series:
        # this should be true as long as the trend site is applied
        # to a single site
        sen = _trend_series_to_df(sen, site, start_yr, end_yr)
        mk = _trend_series_to_df(mk, site, start_yr, end_yr)
        count = _trend_series_to_df(count, site, start_yr, end_yr)

    sen.to_sql('trend_sen', con=con, schema='nrec', if_exists='append')
    mk.to_sql('trend_mk', con=con, schema='nrec', if_exists='append')
    count.to_sql('trend_count', con=con, schema='nrec', if_exists='append')


def _trend_series_to_df(series, site, start, end):
        series.name = site
        df = pd.DataFrame().append(series)
        df.index.name = 'site'
        df['start'] = start
        df['end'] = end
        return df


def get_site_list(con, table='merged_results'):
    """ Generates a list of sites ready for trend analysis
    """
    query=f"""
    SELECT DISTINCT "{storet.cols.site_id}" FROM nrec.{table};
    """

    df = pd.read_sql_query(query, con=con)
    return df[storet.cols.site_id].values


def list_trending(con, min_n=50, alpha=0.05):
    ignore_cols = ['site','start','end']
    query ="""
    SELECT * FROM nrec.trend_{};
    """
    count_df = pd.read_sql_query(query.format('count'), con)
    count_df = count_df.drop(ignore_cols, axis=1)
    mk_df = pd.read_sql_query(query.format('mk'), con)
    mk_df = mk_df.drop(ignore_cols, axis=1)

    #find all columns with min obs
    c1 = (count_df > min_n).any()
    c2 = (mk_df <= alpha).any()
    return count_df.columns[(c1 & c2).values]


def max_trend(con, parameter, alpha):
    query = f"""
    SELECT MAX(ABS(sen."{parameter}")) FROM nrec.trend_mk as mk
    INNER JOIN nrec.trend_sen as sen
    ON mk.site = sen.site AND mk.start = sen.start AND mk.end = sen.end
    WHERE mk."{parameter}" <= {alpha};
    """
    df = pd.read_sql_query(query, con)
    return df.values[0][0]


def max_egret_trend(con, parameter, column='c', alpha=0.1, trend_test='nhst', 
                    table='nrec.wrtds_out', omit=None):
    """
    Parameters
    ----------
    con : db connection
    parameter : str
    column : str (c or f)
        c for fn concentration and f for fn flux.
    alpha : float
    omit : list
        list of sites to omit
    """
    query = f"""
    SELECT MAX(ABS(est{column})) FROM {table} WHERE parameter_cd='{parameter}'
    """
    if trend_test=='lbt':
        query = query + f' AND (like{column}up > {alpha} OR like{column}down > {alpha})'

    elif trend_test=='nhst':
        query = query + f' AND pval{column} <= {alpha}'

    else:
        raise ValueError("Trend test not recognized")

    if not omit is None:
        if type(omit) is list:
            omit = (',').join([f"'{i}'" for i in omit])
        query = query + f' AND site_no NOT IN ({omit})'

    query = query + ';'

    df = pd.read_sql_query(query, con)
    return df.values[0][0]


def max_egret_yield_trend(con, parameter, alpha=0.1, omit=None,
                          table='nrec.wrtds_out'):
    query = f"""
    SELECT site_no, estf, likefup, likefdown FROM {table} WHERE parameter_cd='{parameter}';
    """
    df = pd.read_sql_query(query, con)
    site_df = get_site_data(con)
    site_df = site_df[['site_no','drain_area_va']]

    df = df.merge(site_df, on='site_no', how='left')

    df['estf'] = df['estf'] * 10e6 / df['drain_area_va']

    max_pos_trend = df.loc[df['likefup'] > alpha, 'estf'].max()
    max_neg_trend = df.loc[df['likefdown'] > alpha, 'estf'].min()
    return max(max_pos_trend, abs(max_neg_trend))


def get_egret_trend_data(con, parameter, start, end, table='nrec.wrtds_out'):
    query = f"""
    SELECT * FROM {table} WHERE parameter_cd='{parameter}' AND yr_start={start} AND yr_end={end}; 
    """
    return pd.read_sql_query(query, con)


def get_egret_yield_trend_data(con, parameter, start, end,
                               table='nrec.wrtds_out'):
    site_df = get_site_data(con)

    data_df = get_egret_trend_data(con, parameter, start, end, table)

    out_df = data_df.merge(site_df, on='site_no')
    
    cols = ['estf','lowf', 'upf', 'lowf50',
            'upf50', 'lowf95', 'upf95']

    out_df[cols] = out_df[cols].values * 10e6 / out_df[['drain_area_va']].values

    return out_df[data_df.columns]


def get_site_data(con, table='nrec.site_info'):
    query = f"""
    SELECT * FROM {table};
    """
    return pd.read_sql_query(query, con)


def get_trend_data(con, parameter, start, end, min_n=50):
    query = """
    SELECT "site", "{parameter}" FROM nrec.trend_{table} WHERE "start"={start} AND "end"={end}; 
    """
    sen = pd.read_sql_query(query.format(table='sen', parameter=parameter, start=start, end=end),
                            con=con, index_col='site')
    
    mk = pd.read_sql_query(query.format(table='mk', parameter=parameter, start=start, end=end),
                            con=con, index_col='site')
    
    count = pd.read_sql_query(query.format(table='count', parameter=parameter, start=start, end=end),
                              con=con, index_col='site')

    return sen, mk, count

#def get_egret_trend_types(con, parameter, start, end):
#    """ Return a table of gfn trend types
#    """
#    #import pdb; pdb.set_trace()
#    query = f"""
#    SELECT * FROM nrec.wrtds_class WHERE parameter_cd='{parameter}'
#    AND yr_start={start} AND yr_end={end};
#    """
#
#    df = pd.read_sql_query(query, con)
#
#    return df
#

def get_egret_trend_types(con, start, end, parameter=None):
    """ Return a table of gfn trend types
    """
    #import pdb; pdb.set_trace()
    query = f"""
    SELECT cls.*, SIGN(gfn.f_tc) FROM nrec.wrtds_class as cls
    INNER JOIN nrec.wrtds_gfn as gfn
    USING (site_no, parameter_cd, yr_start, yr_end)
    WHERE yr_start={start} AND yr_end={end}
    """
    if parameter:
        query = query + f"AND parameter_cd='{parameter}';"
    else:
        query = query + ';'

    df = pd.read_sql_query(query, con)

    return df


def get_egret_gfn(con, start, end):
    """
    """
    query = f"""
    SELECT * FROM nrec.wrtds_class_in
    WHERE yr_start={start} and yr_end={end};
    """

    return pd.read_sql_query(query, con)