import pandas as pd
import numpy as np
from math import nan

import seaborn as sns
import matplotlib.pyplot as plt
from matplotlib import style, rc
#define baseflux
#XXX
# define column names used in boot_flux mtc, etc
wt='WT'
mtc='CQTC'
qtc='QTC' # flow trend component

def super_stations(con):
    df = pd.read_sql_query("SELECT river, site_no, sq_mi FROM nrec.stations_super;", con)
    return df
    
def baseflux(con, yr_start='1978'):
    """Return dataframe with baseflux of each watershed.
    """
    super_df = super_stations(con)
    query = f"""
    SELECT DISTINCT site_no, parameter_cd, baseflux
    FROM nrec.wrtds_out WHERE yr_start={yr_start};
    """
    df = pd.read_sql_query(query,con)
    df = df.merge(super_df, on=['site_no'])
    total_baseflux = df.groupby('parameter_cd').sum()
    return total_baseflux


def boot_flux(con, units='percent', yr_start='1978'):
    """ NOT FINISHED XXX
    """
    query = f"""
    SELECT site_no, parameter_cd, iboot, f_tc as {wt}, f_cqtc as {mtc}, f_qtc as {qtc}
    FROM nrec.wrtds_gfn_boot WHERE yr_start={yr_start};
    """
    df = pd.read_sql_query(query, con)
    
    query = f"""
    SELECT DISTINCT site_no, parameter_cd, baseflux
    FROM nrec.wrtds_out WHERE yr_start={yr_start};
    """
    df2 = pd.read_sql_query(query, con)

    super_df = super_stations(con)
    df2 = df2.merge(super_df, on=['site_no'])
    
    if units=='percent':
        pass
        
    elif units=='gg':
        factor = 1
        pass
        
    df.merge(df2, on=['site_no','parameter_cd'])

    df_p = df.merge(df2, on=['site_no','parameter_cd'])
    df_p[wt] = df_p[wt]/df_p['baseflux'] * 100
    df_p[mtc] = df_p[mtc]/df_p['baseflux'] * 100
    df_p[qtc] = df_p[qtc]/df_p['baseflux'] * 100

    total = df.groupby(['parameter_cd','iboot']).sum()
    total = total.merge(total_baseflux, left_index=True, right_index=True)
    total[wt] = total[wt]/total['baseflux'] * 100
    total[mtc] = total[mtc]/total['baseflux'] * 100
    total[qtc] = total[qtc]/total['baseflux'] * 100
    total['site_no'] = '1'
    total['river'] = 'Total'
    total = total.reset_index()
    total = total[df_p.columns]
    df_p = df_p.append(total)
    #
    id_vars = ['site_no','parameter_cd','river']
    melted = pd.melt(df_p, id_vars=id_vars, 
                     value_vars=[wt, mtc, qtc], var_name='class',
                     value_name='trend')

def get_baseflux(con, yr_start, total_only=False, major_only=True):
    query = f"""
    SELECT DISTINCT site_no, parameter_cd, baseflux
    FROM nrec.wrtds_out WHERE yr_start={yr_start};
    """
    df = pd.read_sql_query(query,con)

    if major_only:
        super_df = pd.read_sql_query("SELECT river, site_no, sq_mi FROM nrec.stations_super;", con)
        df = df.merge(super_df, on=['site_no'])

    if total_only:
        df = df.groupby('parameter_cd').sum().reset_index()
 
    return df
    


def get_gfn_results(con, yr_start, major_only=True, bbs=True, site=None, 
                    conc=False, dropna=True):
    """ Get the flux change estimate based on all the data (no BBS)
    """
    table = ''
    iboot = '0 as iboot,'

    if conc:
        f_or_c = 'c'
    else:
        f_or_c = 'f'

    if bbs:
        table = '_boot'
        iboot = 'iboot,'
    
    query_end = ''
    if dropna:
        query_end = f'and {f_or_c}_tc is not null'

    query = f"""
    SELECT site_no, parameter_cd, {iboot} {f_or_c}_tc as "{wt}", 
    {f_or_c}_cqtc as "{mtc}", {f_or_c}_qtc as "{qtc}"
    FROM nrec.wrtds_gfn{table} WHERE yr_start={yr_start} {query_end}

    """
    if site:
        query = query + f"AND site_no='{site}';"

    else:
        query = query + ";"

    df = pd.read_sql_query(query,con)

    if major_only:
        super_df = pd.read_sql_query("SELECT river, site_no, sq_mi FROM nrec.stations_super;", con)
        df = df.merge(super_df, on=['site_no'])
   
    return df

def get_gfn_flux_change(con, yr_start, total_only=False, bbs=False, yld=False,
                        conc=False, melted=True, boot=2000, site=None):
    """
    XXX: This function should replace get_bbs_flux_change

    Parameters
    ----------

    yld : boolean
        If True, kg/ha/yr else Gg/yr

    """
    major_only=True
    if site:
        major_only=False
    
    df = get_gfn_results(con, yr_start=yr_start, bbs=bbs, conc=conc, site=site, major_only=major_only)
    df['iboot'] = df.groupby(['parameter_cd','site_no']).cumcount() + 1

    if conc:
        total = df.groupby(['parameter_cd','iboot']).mean(numeric_only=True)
    else:
        total = df.groupby(['parameter_cd','iboot']).sum(numeric_only=True)

    if not site:
        total['site_no'] = '1'
        total['river'] = 'Total'
        total = total.reset_index()
        total = total[df.columns]

        if total_only:
            df = total
        else:
            df = df.append(total)

    if yld:
        for col in [wt, mtc, qtc]:
            df[col] = 1000000 * df[col] / (258.999 * df['sq_mi'])

    if melted:
        id_vars = ['site_no','parameter_cd','river']
        if site:
            id_vars = ['site_no', 'parameter_cd']
        df = pd.melt(df, id_vars=id_vars, 
                     value_vars=[wt, mtc, qtc], var_name='class',
                     value_name='trend')
    
    return df

unit_mod = {
    '00600': ' of N',
    '00630': ' of N',
    '00625': ' of N',
    '00665': ' of P',
    '00666': ' of P',
    '00667': ' of P',
    '00530': ''
}


param_name = {
    '00600': 'TN',
    '00630': 'NO23',
    '00625': 'TKN',
    '00665': 'TP',
    '00666': 'DP',
    '00667': 'PP',
    '00530': 'TSS'
}

def two_period_flux_yield_conc_change_by_river(param, label, con,
                                               filename=None,
                                               dpi=None,
                                               fontsize=8,
                                               legend_loc='best'):
    width=0.6
    whis = [5,95]
    start1 = 1978
    start2 = 2008
    starts = [1978, 2008]
    end = 2017
    palette={qtc:'b',mtc:'r',wt:'purple'}

    super_df = pd.read_sql_query("SELECT river, site_no, sq_mi FROM nrec.stations_super;", con)
    order = super_df.sort_values(by='sq_mi', ascending=False)['river'].values
    order = np.append('Total',order)

    sns.set(style="whitegrid", palette="pastel", color_codes=True)
    rc('font',**{'family':'sans-serif','sans-serif':['Arial'], 'size':8})
    flierprops = dict(markerfacecolor='1', markersize=1,
                      linestyle='none')

    fig, ax = plt.subplots(3,2, figsize=(7.48,5))
    ax = np.atleast_2d(ax)
    fig.subplots_adjust(wspace=0.2, hspace=0.1)

    for i, mode in enumerate(['conc','flux','yld']):
        kwargs = {'conc':False, 'yld':False}        
        if mode == 'conc' or mode =='yld':
            kwargs[mode] = True

        df1 = get_gfn_flux_change(con=con, yr_start=start1,
                                  total_only=False, bbs=True, **kwargs)
        df2 = get_gfn_flux_change(con=con, yr_start=start2,
                                  total_only=False, bbs=True, **kwargs)


        sns.boxplot(x="river",y="trend", hue="class", data=df1[df1['parameter_cd']==param],
                    palette=palette, order=order, ax=ax[i,0], flierprops=flierprops,
                    showfliers=False, linewidth=0.5, whis=whis, width=width)

        sns.boxplot(x="river",y="trend", hue="class", data=df2[df2['parameter_cd']==param],
                    palette=palette, order=order, ax=ax[i,1], flierprops=flierprops,
                    showfliers=False, linewidth=0.5, whis=whis, width=width)

        ylim = get_max_ax_lim(ax[i,0], ax[i,1])
        
        ax[i,0].set_ylim(ylim)
        ax[i,1].set_ylim(ylim)

        for j in [0,1]:
                ax[i,j].axhline(y=0, color='black',lw=1.3)
                ax[i,j].spines['top'].set_visible(False)
                ax[i,j].spines['bottom'].set_visible(False)
                ax[i,j].set_xlabel('')
    
                ax[i,j].spines['right'].set_visible(False)
                ax[i,j].legend().set_visible(False)
                ax[i,j].tick_params(axis="both", labelsize=fontsize, pad=1)
                if ax[i,j].is_last_col():
                    ax[i,j].set_ylabel('')

                if ax[i,j].is_first_row():
                    ax[i,j].text(0.5, 1.02, f'{starts[j]} to {end}',
                                 fontsize=fontsize, horizontalalignment='center',
                                 transform=ax[i,j].transAxes, fontweight='bold')

        if ax[i,0].is_last_row():
            ax[i,0].set_xticklabels(ax[i,0].get_xticklabels(), rotation=90,
                                    fontsize=fontsize, fontweight='bold')
            ax[i,1].set_xticklabels(ax[i,0].get_xticklabels(), rotation=90,
                                    fontsize=fontsize, fontweight='bold')
        else:
            ax[i,0].set_xticklabels('')
            ax[i,1].set_xticklabels('')

        #for i, name in enumerate(labels):
        for i, units in enumerate(['mg/L{}','Gg{} per yr','Gg{} per ha per yr']):
            mod = unit_mod.get(param,'')
            name = param_name.get(param,'')
            label = f'$\Delta${name} ({units.format(mod)})'
            #label = f'$\Delta${name} ({units})'
            ax[i,0].set_ylabel(label, fontsize=fontsize, fontweight='bold')

    ax[0,1].legend(loc=legend_loc, framealpha=1, prop={'size': 8})
    ax[0,1].get_legend().get_frame().set_linewidth(0.0)

    fig.subplots_adjust(bottom=0.12, left=0.08, right=0.98, top=0.98)

    if not filename is None:
        fig.savefig(filename, dpi=dpi)


def two_period_flux_change_by_river(params, labels, con, filename=None, 
                                      dpi=None, fontsize=8, legend_loc='best',
                                      yld=False, conc=False, height=8):
    """
    labels = ['$\Delta$TN (Gg per yr)', '$\Delta$NO23 (Gg per yr)',
              '$\Delta$TKN (Gg per yr)', '$\Delta$TSS (Gg per yr)']

    labels = ['TN','NO23','TKN','TSS']
    params = ['00600','00630','00625','00530']
    """
    if yld:
        units = 'kg{} per ha per yr'
    elif conc:
        units = 'mg/L{}'
    else:
        units = 'Gg{} per yr'
    width=0.6
    whis = [5,95]
    start1 = 1978
    start2 = 2008
    starts = [1978, 2008]
    end = 2017
    palette={qtc:'b',mtc:'r',wt:'purple'}

    super_df = pd.read_sql_query("SELECT river, site_no, sq_mi FROM nrec.stations_super;", con)
    order = super_df.sort_values(by='sq_mi', ascending=False)['river'].values
    order = np.append('Total',order)

    df1 = get_gfn_flux_change(con=con, yr_start=start1, yld=yld, conc=conc,
                              total_only=False, bbs=True)
    df2 = get_gfn_flux_change(con=con, yr_start=start2, yld=yld, conc=conc,
                              total_only=False, bbs=True)
    df_list = [df1, df2]

    sns.set(style="whitegrid", palette="pastel", color_codes=True)
    rc('font',**{'family':'sans-serif','sans-serif':['Arial'], 'size':8})
    flierprops = dict(markerfacecolor='1', markersize=1,
                      linestyle='none')

    fig, ax = plt.subplots(len(params),2, figsize=(7.48, height))
    ax = np.atleast_2d(ax)
    fig.subplots_adjust(wspace=0.2, hspace=0.1)

    for i, param in enumerate(params):
        sns.boxplot(x="river",y="trend", hue="class", data=df1[df1['parameter_cd']==param],
                    palette=palette, order=order, ax=ax[i,0], flierprops=flierprops,
                    showfliers=False, linewidth=0.5, whis=whis, width=width)

        sns.boxplot(x="river",y="trend", hue="class", data=df2[df2['parameter_cd']==param],
                    palette=palette, order=order, ax=ax[i,1], flierprops=flierprops,
                    showfliers=False, linewidth=0.5, whis=whis, width=width)

        ylim = get_max_ax_lim(ax[i,0], ax[i,1])
        
        ax[i,0].set_ylim(ylim)
        ax[i,1].set_ylim(ylim)

        for j in [0,1]:
                ax[i,j].axhline(y=0, color='black',lw=1.3)
                ax[i,j].spines['top'].set_visible(False)
                ax[i,j].spines['bottom'].set_visible(False)
                ax[i,j].set_xlabel('')
    
                ax[i,j].spines['right'].set_visible(False)
                ax[i,j].legend().set_visible(False)
                ax[i,j].tick_params(axis="both", labelsize=fontsize, pad=1)
                if ax[i,j].is_last_col():
                    ax[i,j].set_ylabel('')

                if ax[i,j].is_first_row():
                    ax[i,j].text(0.5, 1.02, f'{starts[j]} to {end}',
                                 fontsize=fontsize, horizontalalignment='center',
                                 transform=ax[i,j].transAxes, fontweight='bold')

        if ax[i,0].is_last_row():
            ax[i,0].set_xticklabels(ax[i,0].get_xticklabels(), rotation=90,
                                    fontsize=fontsize, fontweight='bold')
            ax[i,1].set_xticklabels(ax[i,0].get_xticklabels(), rotation=90,
                                    fontsize=fontsize, fontweight='bold')
        else:
            ax[i,0].set_xticklabels('')
            ax[i,1].set_xticklabels('')

        #for i, name in enumerate(labels):
        for i, param in enumerate(params):
            mod = unit_mod.get(param,'')
            name = param_name.get(param,'')
            label = f'$\Delta${name} ({units.format(mod)})'
            #label = f'$\Delta${name} ({units})'
            ax[i,0].set_ylabel(label, fontsize=fontsize, fontweight='bold')

    ax[0,1].legend(loc=legend_loc, framealpha=1, prop={'size': 8})
    ax[0,1].get_legend().get_frame().set_linewidth(0.0)

    fig.subplots_adjust(bottom=0.12, left=0.08, right=0.98, top=0.98)

    if not filename is None:
        fig.savefig(filename, dpi=dpi)

def get_max_ax_lim(*axes, axis='y'):
    assert axis == 'y', ValueError('Axis must be y')

    min_lim, max_lim = axes[0].get_ylim()
    for ax in axes:
        lower, upper = ax.get_ylim()
        max_lim = max(max_lim, upper)
        min_lim = min(min_lim, lower)
    return min_lim, max_lim

def two_period_statewide_tn_tp_tss_change(con, filename=None, dpi=None, fontsize=8, site=None):
    width = 0.6
    whis = [5,95]
    start1 = 1978
    start2 = 2008
    starts = [1978, 2008]
    end = 2017
    palette={qtc:'b',mtc:'r',wt:'purple'}
    n_params = ['00600','00630','00625']
    p_params = ['00665','00666','00667']
    tss_params = ['00530']

    df1 = get_gfn_flux_change(con=con, yr_start=start1, total_only=True, bbs=True, site=site)
    df2 = get_gfn_flux_change(con=con, yr_start=start2, total_only=True, bbs=True, site=site)

    df_list = [df1, df2]

    sns.set(style="whitegrid", palette="pastel", color_codes=True)
    rc('font',**{'family':'sans-serif','sans-serif':['Arial'], 'size':8})
    flierprops = dict(markerfacecolor='1', markersize=1,
                      linestyle='none')

    fig, ax = plt.subplots(3,2, figsize=(3.54,6))
    fig.subplots_adjust(wspace=0.3)
    
    for col in range(2):
        df = df_list[col]
        df['trend_tg'] = df['trend']/1000
        
        sns.boxplot(x="parameter_cd", y="trend", hue="class", data=df,
                    palette=palette,
                    order=p_params, ax=ax[0, col], flierprops=flierprops,
                    linewidth=0.5, showfliers=False, width=width, whis=whis)
        

        sns.boxplot(x="parameter_cd", y="trend", hue="class", data=df,
                    palette=palette,
                    order=n_params, ax=ax[1, col], flierprops=flierprops,
                    linewidth=0.5, showfliers=False, width=width, whis=whis)

        sns.boxplot(x="parameter_cd", y="trend_tg", hue="class", data=df,
                    palette=palette,
                    order=tss_params, ax=ax[2, col], flierprops=flierprops,
                    linewidth=0.5, showfliers=False, width=0.2, whis=whis)
        

        ax[0,col].text(0.5, 1.02, f'{starts[col]} to {end}',
                       fontsize=fontsize, horizontalalignment='center',
                       transform=ax[0,col].transAxes, fontweight='bold')


        for row in range(3):

            ax[row,col].axhline(y=0, color='black',lw=1)
            ax[row,col].spines['top'].set_visible(False)
            ax[row,col].spines['bottom'].set_visible(False)
            ax[row,col].spines['right'].set_visible(False)
            ax[row,col].set_xlabel('')
            ax[row,col].legend().set_visible(False)
            ax[row,col].tick_params(axis="both", labelsize=fontsize, pad=1)
    
    for row in range(3):
        ylim = get_max_ax_lim(ax[row,0], ax[row,1])
        ax[row,0].set_ylim(ylim)
        ax[row,1].set_ylim(ylim)
        ax[row,1].set_ylabel('')
   
    ax[1,0].set_xticklabels(['TN','NO23','TKN'], fontsize=fontsize)
    ax[1,1].set_xticklabels(['TN','NO23','TKN'], fontsize=fontsize)

    ax[0,0].set_xticklabels(['TP','DP','PP'], fontsize=fontsize)
    ax[0,1].set_xticklabels(['TP','DP','PP'], fontsize=fontsize)


    ax[2,0].set_xticklabels(['TSS'], fontsize=fontsize)
    ax[2,1].set_xticklabels(['TSS'], fontsize=fontsize)

    ax[0,0].set_ylabel('$\Delta$(Gg of P per yr)', fontweight='bold', fontsize=fontsize, labelpad=3)
    ax[1,0].set_ylabel('$\Delta$(Gg of N per yr)', fontweight='bold', fontsize=fontsize, labelpad=3)
    ax[2,0].set_ylabel('$\Delta$(Tg per yr)', fontweight='bold', fontsize=fontsize, labelpad=3)

    ax[2,1].legend(loc='lower center', framealpha=1, prop={'size': 8})
    ax[2,1].get_legend().get_frame().set_linewidth(0.0)

    fig.subplots_adjust(bottom=0.06, left=0.15, right=0.98, top=0.95)

    if not filename is None:
        fig.savefig(filename, dpi=dpi)

def two_site_comparison(con, site1, site2, start, param, labels, filename=None, dpi=None, fontsize=8):
    #labels is list length 2
    # setup plot
    width = 0.6
    whis = [5, 95]
    sns.set(style="whitegrid", palette="pastel", color_codes=True)
    rc('font',**{'family':'sans-serif','sans-serif':['Arial'], 'size':8})
    flierprops = dict(markerfacecolor='1', markersize=1,
                      linestyle='none')

    #fig, ax = plt.subplots(2,2, figsize=(7.48,6))
    fig, ax = plt.subplots(1,2, figsize=(3.54,3))
    #fig, ax = plt.subplots(1,3, figsize=(5,3))
    fig.subplots_adjust(wspace=0.3)
    
    palette={qtc:'b',mtc:'r',wt:'purple'}
    if param == 'n':
        params = ['00600','00630','00625']
        xticklabels = ['TN','NO23','TKN']
        ylabel='$\Delta$(Gg of N per yr)'
        factor = 1
    elif param == 'p':
        params = ['00665','00666','00667']
        xticklabels = ['TP','DP','PP']
        ylabel='$\Delta$(Gg of P per yr)'
        factor = 1
    elif param == 'tss':
        params = ['00530']
        xticklabels = ['TSS']
        ylabel='$\Delta$(Tg per yr)'
        factor = 1/1000

    # get data
    end = 2017
    if site1 == 'total':
        df1 = get_gfn_flux_change(con=con, yr_start=start, total_only=True, bbs=True)
    else:
        df1 = get_gfn_flux_change(con=con, yr_start=start, site=site1, bbs=True)

    df2 = get_gfn_flux_change(con=con, yr_start=start, site=site2, bbs=True)
    df_list = [df1, df2]

    for col in range(2):
        df = df_list[col]
        df['trend'] = df['trend']*factor
        
        sns.boxplot(x="parameter_cd", y="trend", hue="class", data=df,
                    palette=palette,
                    order=params, ax=ax[col], flierprops=flierprops,
                    linewidth=0.5, showfliers=False, width=width, whis=whis)
        
        ax[col].text(0.5, 1.02, labels[col],
                     fontsize=fontsize, horizontalalignment='center',
                     transform=ax[col].transAxes, fontweight='bold')

        ax[col].axhline(y=0, color='black',lw=1)
        ax[col].spines['top'].set_visible(False)
        ax[col].spines['bottom'].set_visible(False)
        ax[col].spines['right'].set_visible(False)
        ax[col].set_xlabel('')
        ax[col].legend().set_visible(False)
        ax[col].tick_params(axis="both", labelsize=fontsize, pad=1)

        ax[col].set_xticklabels(xticklabels, fontsize=fontsize)
    
    ylim = get_max_ax_lim(ax[0], ax[1])
    ax[0].set_ylim(ylim)
    ax[1].set_ylim(ylim)
    ax[1].set_ylabel('')
   
    ax[0].set_ylabel(ylabel, fontweight='bold', fontsize=fontsize, labelpad=3)

    ax[1].legend(loc='lower center', framealpha=1, prop={'size': 8})
    ax[1].get_legend().get_frame().set_linewidth(0.0)
    #fig.suptitle(f'{start}-{end}')
    fig.subplots_adjust(bottom=0.06, left=0.15, right=0.98, top=0.90)

    if not filename is None:
        fig.savefig(filename, dpi=dpi)




def two_period_statewide_tn_tp_change(con, filename=None, dpi=None, fontsize=8):
    width = 0.6
    whis = [5,95]
    start1 = 1978
    start2 = 2008
    starts = [1978, 2008]
    end = 2017
    palette={qtc:'b',mtc:'r',wt:'purple'}
    n_params = ['00600','00630','00625']
    p_params = ['00665','00666','00667']
    df1 = get_gfn_flux_change(con=con, yr_start=start1, total_only=True, bbs=True)
    df2 = get_gfn_flux_change(con=con, yr_start=start2, total_only=True, bbs=True)

    df_list = [df1, df2]

    sns.set(style="whitegrid", palette="pastel", color_codes=True)
    rc('font',**{'family':'sans-serif','sans-serif':['Arial'], 'size':8})
    flierprops = dict(markerfacecolor='1', markersize=1,
                      linestyle='none')

    #fig, ax = plt.subplots(2,2, figsize=(7.48,6))
    fig, ax = plt.subplots(2,2, figsize=(3.54,4))
    fig.subplots_adjust(wspace=0.3)
    
    for col in range(2):
        df = df_list[col]
        sns.boxplot(x="parameter_cd", y="trend", hue="class", data=df,
                    palette=palette,
                    order=n_params, ax=ax[0, col], flierprops=flierprops,
                    linewidth=0.5, showfliers=False, width=width, whis=whis)

        sns.boxplot(x="parameter_cd", y="trend", hue="class", data=df,
                    palette=palette,
                    order=p_params, ax=ax[1, col], flierprops=flierprops,
                    linewidth=0.5, showfliers=False, width=width, whis=whis)
        

        ax[0,col].text(0.5, 1.02, f'{starts[col]} to {end}',
                       fontsize=fontsize, horizontalalignment='center',
                       transform=ax[0,col].transAxes, fontweight='bold')


        for row in range(2):

            ax[row,col].axhline(y=0, color='black',lw=1)
            ax[row,col].spines['top'].set_visible(False)
            ax[row,col].spines['bottom'].set_visible(False)
            ax[row,col].spines['right'].set_visible(False)
            ax[row,col].set_xlabel('')
            ax[row,col].legend().set_visible(False)
            ax[row,col].tick_params(axis="both", labelsize=fontsize, pad=1)
            #if ax[row,col].is_last_col():
                #ax[row,col].spines['left'].set_visible(False)
                #ax[row,col].set_yticklabels([])

            #ax[row,col].tick_barams(ax)
    
    ax[0,0].set_xticklabels(['TN','NO23','TKN'], fontsize=fontsize)
    ax[0,1].set_xticklabels(['TN','NO23','TKN'], fontsize=fontsize)

    ax[1,0].set_xticklabels(['TP','DP','SP'], fontsize=fontsize)
    ax[1,1].set_xticklabels(['TP','DP','SP'], fontsize=fontsize)
    ax[0,0].set_ylabel('$\Delta$(Gg of N per yr)', fontweight='bold', fontsize=fontsize, labelpad=3)
    ax[1,0].set_ylabel('$\Delta$(Gg of P per yr)', fontweight='bold', fontsize=fontsize, labelpad=3)

    ax[0,1].set_ylabel('')
    ax[1,1].set_ylabel('')
    ax[0,1].set_ylim(ax[0,0].get_ylim())
    ax[1,1].set_ylim(ax[1,0].get_ylim())

    ax[0,1].legend(loc='lower right', framealpha=1, prop={'size': 8})
    ax[0,1].get_legend().get_frame().set_linewidth(0.0)

    
    fig.subplots_adjust(bottom=0.06, left=0.15, right=0.98, top=0.95)

    if not filename is None:
        fig.savefig(filename, dpi=dpi)


def plot_statewide_tn_tp_change(con, filename=None, dpi=None, yr_start=1978):
    """ Plot bar charts showing statewide total TN and TP change with uncertainty
    """
    palette={qtc:'b',mtc:'r',wt:'purple'}
    melted = get_gfn_flux_change(con=con, yr_start=yr_start, total_only=True, bbs=True)
    sns.set(style="whitegrid", palette="pastel", color_codes=True)
    rc('font',**{'family':'sans-serif','sans-serif':['Arial'], 'size':8})
    flierprops = dict(markerfacecolor='1', markersize=1,
                      linestyle='none')

    fig, ax = plt.subplots(1,2, figsize=(7.48,3))
    fig.subplots_adjust(wspace=0.3)

    params = ['00600','00630','00625']
    sns.boxplot(x="parameter_cd", y="trend", hue="class", data=melted,
                    palette=palette,
                    order=params, ax=ax[0], flierprops=flierprops,
                    linewidth=1, showfliers=False, whis=whis)


    params = ['00665','00666','00667']
    sns.boxplot(x="parameter_cd", y="trend", hue="class", data=melted,
                    palette=palette,
                    order=params, ax=ax[1], flierprops=flierprops,
                    linewidth=1, showfliers=False, whis=whis)


    for i in [0,1]:
        ax[i].axhline(y=0, color='black',lw=1.3)
        ax[i].spines['top'].set_visible(False)
        ax[i].spines['bottom'].set_visible(False)
        ax[i].spines['right'].set_visible(False)
        ax[i].set_xlabel('')
        ax[i].legend().set_visible(False)

    ax[0].set_ylabel('$\Delta$(Gg of N per yr)', fontweight='bold')
    ax[1].set_ylabel('$\Delta$(Gg of P per yr)', fontweight='bold')

    ax[0].set_xticklabels(['TN','NO23','TKN'], fontweight='bold')
    ax[1].set_xticklabels(['TP','DP','SP'], fontweight='bold')

    ax[1].legend(loc='upper right', framealpha=1)
    ax[1].get_legend().get_frame().set_linewidth(0.0)

    if not filename is None:
        fig.savefig(filename, dpi=dpi)


def all_flux_correlations(con, filename=None, dpi=None, both=False, majors=False, **kwargs):
    fontsize=8
    rc('font',**{'family':'sans-serif','sans-serif':['Arial'], 'size':6})
    sns.set(style="white")

    nrows = 1 + both
    ncols = 2
    years = [1978, 2008]
    # Set up the matplotlib figure
    fig, ax = plt.subplots(nrows, ncols, figsize=(7.48, 3.54 * nrows))
    if nrows == 1:
        ax = np.expand_dims(ax, axis=0)

    # Generate a custom diverging colormap
    cmap = sns.diverging_palette(220, 10, as_cmap=True)

    # Draw the heatmap with the mask and correct aspect ratio
    cbar_kws = dict(use_gridspec=False, shrink=1)
    #cbar_kws = dict(use_gridspec=False, location="top",shrink=1)
    fig.subplots_adjust(right=0.93)
    cbar_ax = fig.add_axes([0.95, 0.15, 0.025, 0.7]) 

    
    for i in range(nrows):
        for j in range(ncols):
            # Compute the correlation matrix
            majors_only = i%2 + majors #XXX Hack
            corr_df = _flux_correlation(con, majors_only=majors_only,
                                        yr_start=years[j], **kwargs)

            # Generate a mask for the upper triangle
            mask = np.zeros_like(corr_df, dtype=np.bool)
            mask[np.triu_indices_from(mask)] = True

            im = sns.heatmap(corr_df, mask=mask, cmap=cmap, center=0,
                        square=True, linewidths=.5, ax=ax[i,j], cbar_kws=cbar_kws,
                        vmin=-1, vmax=1, cbar_ax=cbar_ax)

            ax[i,j].set_xlabel('')
            ax[i,j].set_ylabel('')
            ax[i,j].tick_params(axis='both', labelsize=8)
            
            if ax[i,j].is_first_row():
                start = years[j]
                ax[i,j].text(0.5, 1.02, f'{start} to 2017',
                             fontsize=fontsize, horizontalalignment='center',
                             transform=ax[i,j].transAxes, fontweight='bold')

    cbar_ax.tick_params(labelsize=8)

    if filename:
        fig.save(filename, dpi=dpi)
    
def plot_flux_correlation(con, majors_only=True, filename=None, dpi=None, ax=None, **kwargs):
    """
    """
    rc('font',**{'family':'sans-serif','sans-serif':['Arial'], 'size':6})
    sns.set(style="white")

    # Compute the correlation matrix
    corr_df = _flux_correlation(con, majors_only=majors_only, **kwargs)

    # Generate a mask for the upper triangle
    mask = np.zeros_like(corr_df, dtype=np.bool)
    mask[np.triu_indices_from(mask)] = True

    # Set up the matplotlib figure
    if ax is None:
        fig, ax = plt.subplots(figsize=(3.54, 4))
        fig.subplots_adjust(left=0.15, bottom=0.15, right=.9, top=.98)
    # Generate a custom diverging colormap
    cmap = sns.diverging_palette(220, 10, as_cmap=True)

    # Draw the heatmap with the mask and correct aspect ratio
    cbar_kws = dict(use_gridspec=False, location="top",shrink=1)

    sns.heatmap(corr_df, mask=mask, cmap=cmap, center=0,
                square=True, linewidths=.5, ax=ax, cbar_kws=cbar_kws)
    
    ax.tick_params(axis='both', labelsize=10)
    ax.set_xlabel('')
    ax.set_ylabel('')
    #fig.tight_layout()
    if not filename is None:
        fig.savefig(filename, dpi=dpi)
    

def plot_2flux_correlation(con, majors_only=True, filename=None, dpi=None, ax=None, 
                          start1=1978, start2=2008, **kwargs):
    """ XXX NOT FINISHED
    TODO: match cbar
    """
    rc('font',**{'family':'sans-serif','sans-serif':['Arial'], 'size':6})
    sns.set(style="white")

    # Compute the correlation matrix
    corr_df = _flux_correlation(con, majors_only=majors_only, yr_start=start1)
    return corr_df

    # Generate a mask for the upper triangle
    mask = np.zeros_like(corr_df, dtype=np.bool)
    mask[np.triu_indices_from(mask)] = True

    vmax=1
    vmin=-1

    # Compute the correlation matrix
    corr2_df = _flux_correlation(con, majors_only=majors_only, yr_start=start2)

    # Generate a mask for the upper triangle
    mask2 = np.zeros_like(corr2_df, dtype=np.bool)
    mask2[np.triu_indices_from(mask2)] = True

    # Set up the matplotlib figure
    if ax is None:
        fig, ax = plt.subplots(nrows=1, ncols=2, figsize=(7.48, 4), sharey=True)
        fig.subplots_adjust(left=0.15, bottom=0.15, right=.9, top=.98)
    # Generate a custom diverging colormap
    cmap = sns.diverging_palette(220, 10, as_cmap=True)

    # Draw the heatmap with the mask and correct aspect ratio
    cbar_kws = dict(use_gridspec=False, location="right",shrink=1)

    sns.heatmap(corr_df, mask=mask, cmap=cmap, center=0, vmax=vmax, vmin=vmin,
                square=True, linewidths=.5, ax=ax[0], cbar_kws=cbar_kws)

    sns.heatmap(corr2_df, mask=mask2, cmap=cmap, center=0, vmax=vmax, vmin=vmin,
                square=True, linewidths=.5, ax=ax[1], cbar_kws=cbar_kws)
    
    for i in [0,1]:
        ax[i].tick_params(axis='both', labelsize=10)
        ax[i].set_xlabel('')
        ax[i].set_ylabel('')
    #fig.tight_layout()
    if not filename is None:
        fig.savefig(filename, dpi=dpi)
 

def _flux_correlation(con, majors_only=True, yr_start='1978'):
    # correlation flux major rivers
    query = f"""
    SELECT site_no, parameter_cd, f_tc as wt, f_cqtc as mtc, f_qtc as qtc FROM nrec.wrtds_gfn WHERE yr_start={yr_start};
    """
    df = pd.read_sql_query(query,con)

    query = f"""
    SELECT DISTINCT site_no, parameter_cd, baseflux FROM nrec.wrtds_out WHERE yr_start={yr_start};
    """
    df2 = pd.read_sql_query(query, con)

    if majors_only:
        super_df = pd.read_sql_query("SELECT river, site_no, sq_mi FROM nrec.stations_super;", con)

        df2 = df2.merge(super_df, on=['site_no'])

    #df= df.append(total)


    #df = df[df['site_no'].isin(super_df['site_no'])].reset_index()
    #df_p =  df.merge(super_df, on='site_no').merge(df2, on=['site_no','parameter_cd'])
    df_p = df.merge(df2, on=['site_no','parameter_cd'])
    df_p['wt'] = df_p['wt']/df_p['baseflux'] * 100
    df_p['mtc'] = df_p['mtc']/df_p['baseflux'] * 100
    df_p['qtc'] = df_p['qtc']/df_p['baseflux'] * 100


    x = df_p.pivot_table(index='site_no',values='mtc',columns='parameter_cd')
    #
    cols = {
        '00530':'TSS',
        '00667':'SP',
        '00600':'TN',
        '00610':'NH4',
        '00625':'TKN',
        '00630':'NO23',
        '00665':'TP',
        '00666':'DP',
        '99220':'Cl'
    }
    x = x.rename(columns=cols)
    return x.corr()
