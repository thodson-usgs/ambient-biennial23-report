from ambient import storet, sites, legacystoret, nwis

import pandas as pd
import numpy as np
from math import nan
from sqlalchemy.types import Float, Boolean, Date, String


def fill_merged_result_table(con, site_df, crosswalk_df, units_df, schema, wrtds=False, results=True):
    """
    """
    for i, site in site_df.iterrows():
        _fill_merged_result_table_for_site(con, site, crosswalk_df,
                                           units_df,
                                           schema=schema,
                                           wrtds=wrtds, results=results)

def _fill_merged_result_table_for_site(con, site,
                                       crosswalk_df, units_df,
                                       wrtds=False,
                                       results=True,
                                       schema=None):
    # TODO assert that merged_storet exists with generic check function
    site_name = 'IL_EPA_WQX-' + site[sites.cols.storet_id]
    query = f"""
    SELECT * FROM {schema}.merged_storet
    WHERE "MonitoringLocationIdentifier" = '{site_name}';
    """
    storet_df = pd.read_sql_query(query, con)
    #storet_df = pd.read_sql_table('merged_storet', con=con, schema='nrec')
        #throw out any columns not found in STORET
    #try this if fails message that table may need to be deleted from db
    if results:
        values_df, flags_df = storet.to_values_df(storet_df,
                                                  quantile=0.7, flags=True)
        #remove illegal characters from column names
        old_columns = values_df.columns.tolist()
        new_columns = [column.replace('(','<').replace(')','>') for column in old_columns]
        values_df.columns = new_columns
        flags_df.columns = new_columns
        used_columns = only_columns_in_merged_table(values_df, con=con)
        values_df = values_df[used_columns]
        flags_df = flags_df[used_columns]

        values_df.to_sql('merged_results', con=con, schema=schema, if_exists='append')
        flags_df.to_sql('merged_flags', con=con, schema=schema, if_exists='append')
    
    if wrtds and site[sites.cols.gage_id] is not np.nan:
        values2, flags2 = storet.site_to_wrtds(storet_df, crosswalk_df, site)

        output = values2.merge(flags2,
                               left_index=True,
                               right_index=True)

        output.to_sql('wrtds', con=con, schema=schema, if_exists='append')

def create_wrtds_table(con, crosswalk_df, schema):
    """ Creates wrtds table in db
    """

    query = f"""
    SELECT DISTINCT "{storet.cols.char}","{storet.cols.frac}","{storet.cols.units}"
    FROM {schema}.merged_storet;
    """
    df = pd.read_sql_query(query, con=con)
    params = storet._lookup_nwis_param(df, crosswalk_df)
    params = params.dropna().values
    p_cols = ('p' + params).tolist()
    r_cols = ('r' + params).tolist()

    columns = [nwis.cols.site_id, nwis.cols.date]
    columns  = columns + p_cols + r_cols

    dtype = {i:Float for i in p_cols}
    r_dtype = {i:String for i in r_cols}
    dtype.update(r_dtype)
    dtype[nwis.cols.date] = Date
    dtype[nwis.cols.site_id] = String

    out = pd.DataFrame(columns = columns)
    out.to_sql('wrtds', con=con, schema=schema,
               if_exists='replace', index=False,
               dtype=dtype)

def create_merged_result_table(con, schema):
    """Create merged_results and merged_flags tables.
    Must make merged_storet first
    """
    query = f"""
    SELECT DISTINCT "CharacteristicName","ResultSampleFractionText" FROM {schema}.merged_storet;
    """
    df = pd.read_sql_query(query, con=con)
    df[storet.cols.frac] = df[storet.cols.frac].replace(np.nan,'')
    df = storet.analysis_name(df)

    columns = [storet.cols.site_id, storet.cols.date]
    columns = columns + df.values.tolist()
    if None in columns:
        columns.remove(None) # this indicates some kind of bug
    columns = [column.replace('(','<').replace(')','>') for column in columns]

    results_dtype = {i:Float for i in columns}
    results_dtype[storet.cols.date] = Date
    results_dtype[storet.cols.site_id] = String

    flags_dtype = {i:Boolean for i in columns}
    flags_dtype[storet.cols.date] = Date
    flags_dtype[storet.cols.site_id] = String

    #create empty tables
    out = pd.DataFrame(columns=columns)
    out.to_sql('merged_results', con=con, schema=schema, if_exists='replace', index=False, dtype=results_dtype)
    out.to_sql('merged_flags', con=con, schema=schema, if_exists='replace', index=False, dtype=flags_dtype)


def update_merged_storet_table(con, site_df, crosswalk_df, units_df, schema, legacy=False):
    """append all data sources into a STORET formated table
    NOTE: create table first
    """

    merged_table_name = 'merged_storet' #declare in header

    for i, site in site_df.iterrows():
        storet_df = _merge_storet_for_site(con, 
                                           schema,
                                           site,
                                           crosswalk_df,
                                           units_df,
                                           legacy=legacy)
        
        #import pdb; pdb.set_trace()
        if not storet_df.empty:
            storet_df.to_sql(merged_table_name, con=con, schema=schema,
                             if_exists='append', index=False)

    _update_merged_storet_with_PP(con, schema=schema, table=merged_table_name)
    _update_merged_storet_with_TN(con, schema=schema, table=merged_table_name)


def _update_merged_storet_with_PP(con, schema, table='merged_storet', censor_limit=0.01):
    """Add particulate P to merged storet
    Note: this creates duplicate entries if TN already in database
    """
    schema_pre = schema + '.'

    query = f"""
    SELECT * FROM {schema_pre}{table} WHERE "CharacteristicName"='Phosphorus' AND "ResultSampleFractionText"='Total'
    """
    tp_df = pd.read_sql_query(query, con=con)

    query2 = f"""
    SELECT * FROM {schema_pre}{table} WHERE "CharacteristicName"='Phosphorus' AND "ResultSampleFractionText"='Dissolved'
    """
    on_df = pd.read_sql_query(query2, con=con)

    test = tp_df.merge(on_df, how='inner',
                      on=['ActivityStartDate', 'ActivityMediaName',
                          'MonitoringLocationIdentifier','ResultMeasure/MeasureUnitCode'],
                      suffixes=('','_y'))

    #XXX Why is ResultMEasureValue a str not a float by default. 
    susP = test['ResultMeasureValue'].astype(float) - test['ResultMeasureValue_y'].astype(float)

    out = pd.DataFrame(columns=tp_df.columns)
    out[storet.cols.result] = susP.values

    to_censor = out[storet.cols.result].isna()
    to_censor = to_censor | (out[storet.cols.result] < censor_limit)
    out.loc[to_censor, storet.cols.result] = nan
    out.loc[to_censor, storet.cols.censor] = censor_limit

    shared_cols = [storet.cols.date,
                   storet.cols.time,
                   storet.cols.media,
                   storet.cols.units,
                   storet.cols.org,
                   storet.cols.site_id]

    out[shared_cols] = test[shared_cols].values
    out[storet.cols.char] = 'Phosphorus'
    out[storet.cols.frac] = 'Suspended'
    out[storet.cols.units] = 'mg/l as P'

    out.to_sql(table, con=con, schema=schema,
               index=False, if_exists='append')


def _update_merged_storet_with_TN(con, schema, table='merged_storet'):
    """
    Note: this creates duplicate entries if TN already in database
    """
    schema_pre = schema + '.'

    query = f"""
    SELECT * FROM {schema_pre}{table} WHERE "CharacteristicName"='Inorganic nitrogen (nitrate and nitrite)'
    """
    in_df = pd.read_sql_query(query, con=con)

    query2 = f"""
    SELECT * FROM {schema_pre}{table} WHERE "CharacteristicName"='Kjeldahl nitrogen'
    """
    on_df = pd.read_sql_query(query2, con=con)

    test = in_df.merge(on_df, how='inner',
                      on=['ActivityStartDate', 'ActivityMediaName',
                          'MonitoringLocationIdentifier','ResultMeasure/MeasureUnitCode'],
                      suffixes=('','_y'))
    
    # XXX why is this field not a float by default?
    totalN = test['ResultMeasureValue'].astype(float) + test['ResultMeasureValue_y'].astype(float)

    out = pd.DataFrame(columns=in_df.columns)
    out[storet.cols.result] = totalN.values

    shared_cols = [storet.cols.date,
                   storet.cols.time,
                   storet.cols.media,
                   storet.cols.units,
                   storet.cols.org,
                   storet.cols.site_id]

    out[shared_cols] = test[shared_cols].values
    out[storet.cols.char] = 'Nitrogen, mixed forms (NH3), (NH4), organic, (NO2) and (NO3)'
    out[storet.cols.frac] = 'Total'
    out[storet.cols.units] = 'mg/l'

    out.to_sql(table, con=con, schema=schema,
               index=False, if_exists='append')


def only_columns_in_merged_table(merged_df, con, schema):
    """ Returns columns that exist as columns in the merged_results table
    merged_df :
    con : sqlalchemy connection
    """
    query = f"""
    SELECT * FROM {schema}.merged_results LIMIT 0;
    """
    df = pd.read_sql_query(query, con=con)
    table_columns = pd.Series(df.columns)
    check_columns = pd.Series(merged_df.columns)
    found_columns = check_columns[check_columns.isin(table_columns)]
    n_col = pd.Series(
        ['Total Nitrogen, mixed forms <NH3>, <NH4>, organic, <NO2> and <NO3>']
    )
    found_columns = found_columns.append(n_col)
    return found_columns

def _merge_storet_for_site(con, schema, site, crosswalk_df, units_df, legacy=False):
    """ Crosswalks, converts, and pivots all records and loads them into db

    Note: this could be done for all sites at once if certain functions are
    groupby site
    """
    site_id = site[sites.cols.storet_id]

    # load storet data
    site_name = f'IL_EPA_WQX-{site_id}'

    query = f"""
    SELECT * FROM {schema}.wqp WHERE "MonitoringLocationIdentifier"='{site_name}';
    """
    storet_df = pd.read_sql_query(query, con=con)
    storet_df = storet_df[storet_df[storet.cols.media] == 'Water']
    # load NWIS data
    usgs_code = site['USGS Code']
    query = f"""
    SELECT * FROM {schema}.qwdata WHERE "site_no"='{usgs_code}';
    """
    nwis_df = pd.read_sql_query(query, con=con)
    
    if not nwis_df.empty:
        #append to storet
        conversion_factor, parm_cd = nwis.conversion_factor(nwis_df,
                                                            units_df,
                                                            nwis.cols.parameter_cd)
        result_col = nwis.cols.result
        nwis_df[result_col] = nwis_df[result_col] * conversion_factor
        nwis_df[nwis.cols.parameter_cd] = parm_cd

        # should rename or not name at all
        #return nwis_df
        nwis_df = nwis.to_storet(nwis_df, crosswalk_df, storet_site_id=site_name)
        #storet_df = storet_df.append(nwis_df, ignore_index=True)
        storet_df = pd.concat([storet_df, nwis_df], ignore_index=True)

    if legacy:
        # load legacy storet data
        query = f"""
        SELECT * FROM {schema}.legacy_storet WHERE "iepa_station"='{site_id}';
        """
        lstoret_df = pd.read_sql_query(query, con=con)

        if not lstoret_df.empty:
            # handle unit conversions
            conversion_factor, parm_cd = nwis.conversion_factor(lstoret_df,
                                                                units_df,
                                                                legacystoret.cols.parameter_cd)
            result_col = legacystoret.cols.result
            lstoret_df[result_col] = lstoret_df[result_col] * conversion_factor
            lstoret_df[legacystoret.cols.parameter_cd] = parm_cd

            lstoret_df = legacystoret.to_storet(lstoret_df,
                                                crosswalk_df,
                                                storet_site_id=site_name)

            #storet_df = storet_df.append(lstoret_df, ignore_index=True)
            storet_df = pd.concat([storet_df, lstoret_df], ignore_index=True)

        # load legacy storet data 2
        # this was an alternate format provided by M. Short
        query = f"""
        SELECT * FROM {schema}.legacy_storet_2 WHERE "station_code"='{site_id}';
        """
        lstoret2_df = pd.read_sql_query(query, con=con)

        if not lstoret2_df.empty:
            # handle unit conversions
            lstoret2_df = legacystoret.to_legacystoret(lstoret2_df,
                                                       crosswalk_df)

            conversion_factor, parm_cd = nwis.conversion_factor(lstoret2_df,
                                                                units_df,
                                                                legacystoret.cols.parameter_cd)
            result_col = legacystoret.cols.result
            lstoret2_df[result_col] = lstoret2_df[result_col] * conversion_factor
            lstoret2_df[legacystoret.cols.parameter_cd] = parm_cd

            lstoret2_df = legacystoret.to_storet(lstoret2_df,
                                                 crosswalk_df,
                                                 storet_site_id=site_name)

            #storet_df = storet_df.append(lstoret2_df, ignore_index=True)
            storet_df = pd.concat([storet_df, lstoret2_df], ignore_index=True)

    # drop duplicated values
    check_cols = [storet.cols.char,
                  storet.cols.frac,
                  storet.cols.date,
                  storet.cols.media]

    #duplicates = storet_df[check_cols].duplicated()
    #storet_df = storet_df[~duplicates]
    storet_df = storet_df.drop_duplicates(subset=check_cols, keep='first')
    #sort index by date
    sorted_index = pd.to_datetime(storet_df[storet.cols.date]).argsort()
    #apply sorted index
    storet_df = storet_df.iloc[sorted_index].reset_index(drop='True')
    return storet_df
