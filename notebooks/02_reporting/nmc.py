import xarray as xr

def location_label(site):
    return site['river'] + ' ' + site['location']

def compute_river_load(ds, site, nested=True):
    
    site_load = ds.sel(site=site['gage_id'])
    site_load = site_load.drop_vars('site')
    #site_load = site_load * site['scale_factor']

    upstream_gage = site.get('upstream_gage')
    
    if upstream_gage and nested:
        upstream_load = ds.sel(site=upstream_gage).drop_vars('site')
        site_load = site_load - upstream_load
        
    site_load = site_load.assign_coords(coords={'river':location_label(site)})
    
    site_load = site_load * site['scale_factor']
    return site_load


def compute_network_loads(ds, network, nested=True):
    rivers = []
    
    for site in network:
        if site['gage_id'] in ds.site and not site.get('nested'):
            rivers.append(compute_river_load(ds, site, nested))
        
    return xr.concat(rivers, dim='river')
    #return rivers

def labels(network, nested=False):
    labels = []
    for site in network:
        is_nested = site.get('nested')

        if is_nested is None or is_nested==nested:
            #print(nested)
            labels.append(location_label(site))
            
    return labels

def gages(network, nested=False):
    labels = []
    for site in network:
        is_nested = site.get('nested')

        if is_nested is None or is_nested==nested:
            #print(nested)
            labels.append(site['gage_id'])
            
    return labels
#def compute_network_total(ds, network):
#    pass

def kg_to_lbs(x):
    return x * 2.20462

def kg_to_kt(x):
    return x * 1.0e-6