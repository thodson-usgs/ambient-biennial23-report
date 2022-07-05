import pandas as pd

from ambient import storet
from ambient import sites
from ambient import crosswalk
from ambient.nwis import cols
from ambient.storet.cols import group as group_cols


def to_storet(df, crosswalk_df, storet_site_id=None):
    """ Format an NWIS record for STORET

    Parameter
    ---------
    df : DataFrame
        NWIS record

    storet_site_id : list-like
        List of STORET site id's corresponding with each record in df

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
    out[group_cols] = _lookup_storet_cols(df, crosswalk_df)

    out[storet.cols.site_id] = storet_site_id #TODO make this a series
    # otherwise it won't work if it is called before the df is populated

    #crosswalk date and time
    out[storet.cols.time] = df[cols.time]
    out[storet.cols.date] = df[cols.date]
    out[storet.cols.tz] = df[cols.tz]

    # Drop any NaT values
    # TODO: investigate origin of NaT in NWIS records
    out = out[out[storet.cols.time] != 'NaT']

    return out


def conversion_factor(df, units_df, parameter_col):
    """ Returns conversion factor to match units in NWIS record with STORET.

    Examples
    --------
    >>> factor, parm_cd = conversion_factor(df, units_df)
    >>> df['result_va'] = df['result_va'] * factor 
    """
    out = df.merge(units_df, how='left',
                   left_on = parameter_col,
                   right_on = cols.parm_cd_NWIS)


    factor = out[cols.factor].copy()
    factor[factor.isna()] = 1

    parm_cd = out[cols.parm_cd_STORET].copy()
    parm_cd[parm_cd.isna()] = out.loc[parm_cd.isna(), cols.parameter_cd]

    return factor.values, parm_cd.values


def crosswalkable(df, crosswalk_df, inverse=False):
    """List all NWIS parameter codes in ambient.misc.param_dict.

    Parameters
    ----------
    df : DataFrame
        NWIS record
    
    param_lookup_table : DataFrame

    inverse : Boolean
        If True, list parameter codes not in param_dict.

    Returns
    -------
    List of parameter codes
    """
    miss = df.merge(crosswalk_df,
                    how='left',
                    left_on=cols.parameter_cd,
                    right_on=crosswalk.cols.parameter_cd,
                    ).isna().values

    if not inverse:
        return df[~miss].unique().tolist()
    
    else:
        return df[miss].unique().tolist()


def censored_results(df, inverse=False):
    """
    Parameters
    ----------
    df : DataFrame
        An NWIS record
    
    inverse : Boolean
        If set True, return uncensored record.

    Returns
    -------
    A Series consisting of censored values and nans in place of uncensored values.
    """
    if not inverse:
        return df[cols.result].where(df[cols.remark] == '<').values

    elif inverse:
        return df[cols.result].where(df[cols.remark] != '<').values


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

def _lookup_storet_id(df, site_df):
    """
    XXX: this function is not called
    """
    out = df.merge(site_df,
                   left_on=cols.site_id,
                   right_on=sites.cols.usgs_id,
                   how='left')

    return ('IL_EPA_WQX-' + out[sites.cols.storet_id].values)

def _check_lookup_table(crosswalk_df):
    """XXX not sure this is still necessary
    """
    # check if any columns contain nan
    #if crosswalk_df[storet.cols.group].isna().any().any():
    #    raise ValueError("Must import crosswalk table with pd.read_csv(filename, keep_default_na=False)")
    # XXX commented on 20181214, but may introduce bugs
    if cols.parameter_cd not in crosswalk_df.columns:
        raise KeyError("Crosswalk table must have 'parm_cd' column")
