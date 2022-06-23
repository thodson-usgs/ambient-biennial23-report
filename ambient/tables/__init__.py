#module for creating tables

import pandas as pd

def create_gfn_views(parm_list, con, f_or_c='f'):
    """
    """
    i = f_or_c
    for parm_cd in parm_list:
            
        query = f"""
        DROP VIEW IF EXISTS nrec.gfn_{parm_cd};
        CREATE VIEW nrec.gfn_{parm_cd} AS 
        (SELECT site_no, {i}_tc as wt_{parm_cd}, {i}_cqtc as mt_{parm_cd}, {i}_qtc as qt_{parm_cd}
        FROM nrec.wrtds_gfn WHERE parameter_cd='{parm_cd}');
        """

        with con.connect() as c:
            c.execute(query)