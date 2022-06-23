# munge data to correct interval


# drop columns without sufficient data
def drop_sparse(values_df, flags_df, count=50, censorship=0.5):
    """ Drop columns that have too few data or too much censoship.
    """
    # select columns based on censorship
    censored_cols = values_df.columns[flags_df.mean() < censorship]
    # select columns with enough data
    sparse_cols   = values_df.columns[values_df.count() > count]

    selected_cols = censored_cols.join(sparse_cols, how='inner')

    return values_df[selected_cols]