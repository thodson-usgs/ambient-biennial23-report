from awqmn.crosswalk import cols


def analysis_name(record):
    """ Return the full analysis name of an entry in the crosswalk table

    Combine the characteristic name and the result sample fraction to form the
    name of the analysis.

    Parameters
    ----------
    record : Series
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

