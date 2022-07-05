import pandas as pd

from ambient import storet, sites, crosswalk
from ambient.legacystoret import cols, cols_2

from ambient.storet.cols import group as group_cols
from ambient.nwis import _check_lookup_table

censor_codes = ['K','U','M']

def _lookup_storet_cols(df, crosswalk_df):
    """ Return STORET characteristic names and sample fraction from an NWIS record.

    Parameters
    ----------
    df : DataFrame
        An NWIS record.

    crosswalk_df : DataFrame

    Returns
    -------
    A DataFrame with the following columns: characteristic name, sample fraction, and units.
    """
    # ensure there are no duplicates in crosswalk_df
    assert crosswalk_df.duplicated(subset=crosswalk.cols.group).any() == False

    _check_lookup_table(crosswalk_df)
    out = df.merge(crosswalk_df,
                   left_on=cols.parameter_cd,
                   right_on=crosswalk.cols.parameter_cd,
                   how='left')

    return out[crosswalk.cols.group]


def _lookup_nwis_codes(df, crosswalk_df):
    """ Return NWIS parameter code from a legacy STORET 2 record.
    """
    assert crosswalk_df.duplicated(subset=crosswalk.cols.group).any() == False

    _check_lookup_table(crosswalk_df)
    out = df.merge(crosswalk_df,
                   left_on=cols_2.group_cols,
                   right_on=crosswalk.cols.group,
                   how='left')

    return out[cols.parameter_cd]


def to_storet(df, crosswalk_df, storet_site_id=None):
    """ Format an legacy STORET record for STORET

    Parameter
    ---------
    df : DataFrame
        legacy STORET record


    Returns
    -------
    STORET formated record.
    """
    #TODO consider throwing exception for empty DataFrame
    if df.empty:
        return pd.DataFrame()

    out = pd.DataFrame(columns=storet.cols.all_cols)
    out[storet.cols.result] = censored_results(df, inverse=True)
    out[storet.cols.censor] = censored_results(df)
    
    out[storet.cols.org] = df[cols.org].values
    out[storet.cols.site_id] = storet_site_id #TODO make this a series
    out[group_cols] = _lookup_storet_cols(df, crosswalk_df)

    #crosswalk date and time
    out[storet.cols.time] = df[cols.time].apply(_format_time)
    out[storet.cols.date] = df[cols.date]
    #out[storet.cols.tz] = df[cols.tz]

    return out


def to_legacystoret(df, crosswalk_df):
    """ Convert alternate form to legacy storet form
    """
    if df.empty:
        return pd.DataFrame()

    out = pd.DataFrame(columns=cols.all_cols)
    out[cols.result] = df[cols_2.censored_result].values
    out[cols.remark] = df[cols_2.remark].values
    out[cols.site_id] = df[cols_2.site_id].values 
    out[cols.date] = df[cols_2.date].values
    out[cols.time] = df[cols_2.time].apply(_format_legacy_time)
    out[cols.parameter_cd] = _lookup_nwis_codes(df, crosswalk_df)

    return out


def to_storet_2(df):
    """

    Parameter
    ---------
    df : DataFrame
        alternate form of legacy STORET frame. See for example ExportAWQMNwqdataForUSGS tables provided by Matt Short - IEPA
    """
    #TODO consider throwing exception for empty DataFrame
    if df.empty:
        return pd.DataFrame()

    out = pd.DataFrame(columns=storet.cols.all_cols)
    out[storet.cols.result] = df[cols_2.result].values 
    out[storet.cols.censor] = df[cols_2.censor].values
    
    out[storet.cols.org] = df[cols_2.org].values
    out[storet.cols.frac] = df[cols_2.frac].values
    out[storet.cols.char] = df[cols_2.char].values
    out[storet.cols.units] = df[cols_2.units].values
    out[storet.cols.media] = df[cols_2.media].values

    out[storet.cols.site_id] = df[cols_2.site_id]

    #crosswalk date and time
    out[storet.cols.time] = df[cols.time]
    out[storet.cols.date] = df[cols.date]
    #out[storet.cols.tz] = df[cols.tz]

    return out


def _format_time(time):
    """ In: 1000 Out: '10:00'
    """
    time = str(time)

    return '{}:{}'.format(time[:-2], time[-2:])

def _format_legacy_time(time):
    """ In: 09:00:00 Out: 900
    """
    time =str(time)

    return time.rstrip('0').lstrip('0').replace(':','')

def censored_results(df, inverse=False):
    """
    Parameters
    ----------
    df : DataFrame
        A legacy STORET record
    
    inverse : Boolean
        If set True, return uncensored record.

    Returns
    -------
    A Series consisting of censored values and nans in place of uncensored values.
    """
    if not inverse:
        return df[cols.result].where(df[cols.remark].isin(censor_codes)).values

    elif inverse:
        return df[cols.result].where(~df[cols.remark].isin(censor_codes)).values
