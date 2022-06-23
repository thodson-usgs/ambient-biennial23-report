import pandas as pd
import numpy as np

from dataretrieval.utils import format_datetime
from awqmn.storet import cols
from awqmn import nwis, sites, crosswalk

def to_wrtds(df, crosswalk_df, site_df):
    """ Format a STORET record for WRTDS

    Parameters
    ----------
    df : DataFrame
        A record in STORET format.
    """
    out = pd.DataFrame()
    out[nwis.cols.date] = df[cols.date]

    #populate results field
    out[nwis.cols.result] = df[[cols.result, cols.censor]].max(axis=1)

    # populate remark field
    censored = ~df[cols.censor].isna() \
    & ~(df[cols.censor] < df[cols.result])
    
    out.loc[censored, nwis.cols.remark] = '<'
    out.loc[~censored, nwis.cols.remark] = ''
    # fill in parameter codes 
    out[nwis.cols.parameter_cd] = _lookup_nwis_param(df, crosswalk_df).values #XXX this funciton should probably return values
    # fill in USGS site
    out[nwis.cols.site_id] = _lookup_nwis_id(df, site_df, gage=True)

    #drop where site or parameter cd are missing
    out = out.dropna(subset=[nwis.cols.parameter_cd,
                             nwis.cols.site_id])
    

    #two pivots and merge
    # pivot on results
    # rename columns
    result = out.pivot_table(index=[nwis.cols.site_id, nwis.cols.date],
                             values=nwis.cols.result,
                             columns=nwis.cols.parameter_cd,
                             aggfunc='first')


    result.columns = 'p' + result.columns.values

    remark = out.pivot_table(index=[nwis.cols.site_id, nwis.cols.date],
                             values=nwis.cols.remark,
                             columns=nwis.cols.parameter_cd,
                             aggfunc=lambda x: ''.join(x))

    remark.columns = 'r' + remark.columns.values
    return result, remark


def site_to_wrtds(df, crosswalk_df, site):
    """ Format a STORET record from a single site to WRTDS

    Parameters
    ----------
    df : DataFrame
        A record in STORET format.
    """
    # make a site_df
    site_df = pd.DataFrame()
    site_df = site_df.append(site)

    # first check for gage
    if site[sites.cols.gage_id] is np.nan:
        out = pd.DataFrame()
        return out, out
    
    else:
        result, remark = to_wrtds(df, crosswalk_df, site_df)
        return result, remark


def _lookup_nwis_param(df, crosswalk_df):
    """ Return NWIS parameter code from a STORET record.

    Parameters
    ----------
    df : DataFrame
        A STORET record.

    crosswalk_df : DataFrame

    Returns
    -------
    A DataFrame with the following columns: characteristic name, sample fraction, and units.
    """
    # ensure there are no duplicates in crosswalk_df
    assert crosswalk_df.duplicated(subset=crosswalk.cols.group).any() == False

    #_check_lookup_table(crosswalk_df)
    out = df.merge(crosswalk_df,
                   left_on=cols.group,
                   right_on=crosswalk.cols.group,
                   how='left')


    return out[nwis.cols.parameter_cd].apply(lambda x: str(int(x)).zfill(5) if ~np.isnan(x) else np.nan)


def _lookup_nwis_id(df, site_df, gage=False):
    """
    Parameters
    ----------
    df : DataFrame
        A STORET record.
    
    site : DataFrame

    gage : boolean
        If True, uses the gage ID rather than sampling site ID
    """
    site_df = site_df.copy()
    site_df[sites.cols.storet_id] = 'IL_EPA_WQX-' + site_df[sites.cols.storet_id].values
    #df[cols.site_id] = df[cols.site_id].values
    out = df.merge(site_df,
                   left_on=cols.site_id,
                   right_on=sites.cols.storet_id,
                   how='left')

    if gage == False:
        return out[sites.cols.usgs_id]
    
    else:
        return out[sites.cols.gage_id]


def to_values_df(df, quantile=None, flags=False):
    """ Return the censored values from a STORET record.

    Parameters
    ----------
    df : DataFrame
        A record in STORET format.

    quantile : float

    flags : Boolean
        If True, returns censorship status in addition to censored value.
    
    Returns
    -------
    A pivoted table containing a column for each analysis and a row
    for each sample.

    TODO: check if this alters df 
    TODO: if no site_id, add a dummy or else we can't pivot
    """
    df = df.copy() # copying the df is slower than modifying in place but safer
    df[cols.frac] = df[cols.frac].replace(np.nan,'')
    df[cols.name] = analysis_name(df)
    #df[cols.datetime] = activity_datetime(df)
    censor_limits = find_censor_limits(df, quantile=quantile)
    df = cull_most_censored(df, censor_limits)

    if flags:
        # return values and flags
        df[cols.censored], df[cols.flag] = censor(df, 
                                                  censor_limits, 
                                                  flags=flags)


        values = df.pivot_table(index=[cols.site_id, cols.date],
                                columns=cols.name,
                                values=cols.censored,
                                dropna=False,
                                aggfunc='first')

        flags = df.pivot_table(index=[cols.site_id, cols.date],
                               columns=cols.name,
                               values=cols.flag,
                               dropna=False,
                               aggfunc='first')

        return values, flags

    else:
        # only return values
        df[cols.censored] = censor(df, censor_limits, flags=flags)

        return df.pivot_table(index=[cols.site_id, cols.date], 
                              columns=cols.name, 
                              values=cols.censored,
                              aggfunc='first')

def _make_analysis_name(record):
    """ Return the full analysis name of a STORET record.

    Combine the characteristic name and the result sample fraction to form the
    name of the analysis.

    Parameters
    ----------
    record : Series
        An individual STORET

    Return
    
    Full name of analysis
    """
    if type(record[cols.frac]) == float:
        # nan value
        return record[cols.char]

    elif record[cols.frac] == '':
        return record[cols.char]
    
    elif not record[cols.frac]:
        return record[cols.char]

    else:
        return '{} {}'.format(record[cols.frac],
                              record[cols.char])

def analysis_name(df):
    """ Return the full analysis name of a STORET record.

    Combine the characteristic name and the result sample fraction to form the
    name of the analysis.

    Parameters
    ----------
    df : DataFrame
        A record in STORET format.

    Return
    ------
    Full name of analysis
    """
    return df.apply(_make_analysis_name, axis=1)

def clip_interval(df, start, end):
    """ Clip a interval from a STORET record.

    Parameters
    ----------
    df : DataFrame
        A record in STORET format.

    start : str
    end : str

    Return
    ------
    DataFrame clipped to interval.
    """
    start = pd.to_datetime(start)
    end = pd.to_datetime(end)
    dates = pd.to_datetime(df[cols.date])
    return df[(dates > start) & (dates < end)]

def sort_by_date(df):
    """ Sort a STORET reecord by date.

    Parameters
    ----------
    df : DataFrame
        A record in STORET format.
    """
    dates = pd.to_datetime(df[cols.date])

    return df[dates.argsort()]

def activity_datetime(df):
    """ Return the starting datetime of a STORET record.

    TODO: incorporate timezone
    """
    if pd.to_datetime(df[cols.date]).isnull().any():
        import pdb; pdb.set_trace()

    return pd.to_datetime(df[cols.date] + ' ' + df[cols.time],
                          format='%Y%m%d %H:%M:%S')


def find_censor_limits(df, quantile=None):
    """ Return the censor limits of a STORET record.

    Parameters
    ----------
    df : DataFrame
        A record in STORET format.
    
    quantile : float

    """
    # groupby characteristic name and resultsample fraction text
    df[cols.frac] = df[cols.frac].replace(np.nan,'')
    group = df.groupby(by=cols.group)
    # if no quantile given, return the max censor level of each group
    if quantile is None:
        return group[cols.censor].max()

    else:
        return group[cols.censor].quantile(quantile, interpolation='lower')


def test(df, censor_limit):
    censor_max = df.merge(censor_limit.reset_index().rename({cols.censor:cols.censormax}, axis='columns'),
                          on=cols.group,
                          how='left')[cols.censormax]
    return censor_max


def cull_most_censored(df, censor_limit):
    """ Culls any censored data above threshold
    """
    # Create a series of censor levels to correspond with a STORET record
    censor_max = df.merge(censor_limit.reset_index().rename({cols.censor:cols.censormax}, axis='columns'),
                          on=cols.group,
                          how='left')[cols.censormax]

    # set the censor max of any uncensored analysis to 0.
    # could avoid using .values as long as indexes match
    return df[~(df[cols.censor] > censor_max)]


def censor(df, censor_limit, flags=False):
    """Return the censored value of a STORET record.

    Parameters
    ----------
    df : DataFrame
        A record in STORET format.
    
    flags : Boolean
        If True, also returns a Series of booleans indicating censorship.

    Return
    ------
    A Series of censored values.
    """
    # Create a series of censor levels to correspond with a STORET record
    censor_max = df.merge(censor_limit.reset_index().rename({cols.censor:cols.censormax}, axis='columns'),
                          on=cols.group,
                          how='left')[cols.censormax]

    # set the censor max of any uncensored analysis to 0.
    #censor_max[censor_max.isnull()] = -9999  
    # could avoid using .values as long as indexes match
    #censored_values = df[cols.result].where(df[cols.result] > censor_max.values,
    censored_values = df[cols.result].where( ~(censor_max.values > df[cols.result]),
                                            censor_max.values)

    # apply censors
    if not flags:
        return censored_values
    
    else:
        # should use a where instead because this could wrongly censor a value at the limit
        censored_flags = censor_max.values >= censored_values
        return censored_values, censored_flags