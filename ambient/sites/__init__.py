#table = read in dict and ignore nans from data
from awqmn.sites import cols
from awqmn import storet

def merge_site_info(df, site_df,  org='IEPA'):
    """ Return lat, lon, and huc8 id associated with a IEPA site.

    Parameters
    ----------
    df : DataFrame
        DataFame with IEPA site ID's as index
    site_df : DataFrame
        Table with site info
    org : str
        
    """
    site_df = site_df.copy()

    if org=='IEPA':
        id_col = cols.storet_id
        site_df[id_col] = 'IL_EPA_WQX-' + site_df[id_col]

    elif org=='USGS':
        id_col = cols.usgs_id

    elif org=='gage':
        id_col = cols.gage_id

    else:
        raise ValueError("org not recognized")

    location_cols = [id_col, cols.lat, cols.lon,
                     cols.huc8, cols.stream_name, cols.location]
    
    merge_df = site_df[location_cols].copy()
    merge_df = merge_df.set_index(id_col)

    return df.merge(merge_df, left_index=True, right_index=True, how='right')