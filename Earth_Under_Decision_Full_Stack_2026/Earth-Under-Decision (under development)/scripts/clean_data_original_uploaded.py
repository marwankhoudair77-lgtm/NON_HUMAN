import sys, json, pandas as pd, numpy as np, tifffile
src, out = sys.argv[1], sys.argv[2]
EV=f'{src}/c8a90989-GLDAS_NOAH025_3H_2_1_Evap_tavg_30.9000_31.0000_2022-12-27_to_2024-01-08.csv'
RM=f'{src}/f6ca75d4-GLDAS_NOAH025_3H_2_1_RootMoist_inst_30.9000_31.0000_2022-12-27_to_2024-01-08.csv'
GPM=f'{src}/ffc39274-GIOVANNI-g4.timeAvgMap.GPM_3IMERGM_07_precipitation.20230101-20231231.29E_30N_32E_31N.tif'
WX=f'{src}/635d2f64-4432340.csv'
days=pd.date_range('2023-01-01','2023-12-31',freq='D')
qc={}

# ---- GLDAS 3-hourly -> daily
def load(p,name):
    d=pd.read_csv(p).rename(columns={'x':'ts','y':name})
    d['ts']=pd.to_datetime(d.ts,utc=True)
    qc[name+'_dupes']=int(d.ts.duplicated().sum()); qc[name+'_nan']=int(d[name].isna().sum())
    d['date']=d.ts.dt.tz_localize(None).dt.normalize()
    return d
ev=load(EV,'flux'); rm=load(RM,'rm')
assert (ev.ts==rm.ts).all()
ev['mm3h']=ev.flux*10800   # kg m-2 s-1 * 10800 s = mm per 3h
eg=ev.groupby('date').agg(et_mm_day=('mm3h','sum'),n_steps=('mm3h','size'),et_neg_steps=('mm3h',lambda s:int((s<0).sum())))
rg=rm.groupby('date').agg(rootmoist_mm_mean=('rm','mean'),rootmoist_mm_min=('rm','min'),rootmoist_mm_max=('rm','max'))
g=eg.join(rg).reindex(days)
qc['gldas_days_2023']=int(g.n_steps.notna().sum()); qc['gldas_days_not_8_steps']=int((g.n_steps!=8).sum())
qc['et_days_negative_total']=int((g.et_mm_day<0).sum())
g.index.name='date'

# ---- Weather (NOAA GHCN-D) tidy, all stations
w=pd.read_csv(WX); w['DATE']=pd.to_datetime(w.DATE)
w=w.rename(columns={'STATION':'station_id','NAME':'station_name','DATE':'date','PRCP':'prcp_mm','TAVG':'tavg_c','TMAX':'tmax_c','TMIN':'tmin_c'})
qc['wx_dupe_station_days']=int(w.duplicated(['station_id','date']).sum())
w['flag_tmax_lt_tmin']=(w.tmax_c<w.tmin_c)
w['flag_tavg_outside_range']=((w.tavg_c>w.tmax_c+0.5)|(w.tavg_c<w.tmin_c-0.5))
qc['wx_tmax_lt_tmin']=int(w.flag_tmax_lt_tmin.sum()); qc['wx_tavg_outside']=int(w.flag_tavg_outside_range.sum())
w['in_nile_delta_region']=w.station_name.str.startswith('ALEXANDRIA')
w=w.sort_values(['station_name','date'])
w.to_csv(f'{out}/weather_stations_2023_clean.csv',index=False,float_format='%.2f')
alex=w[w.in_nile_delta_region].set_index('date')[['tavg_c','tmax_c','tmin_c','prcp_mm']].add_prefix('alex_').reindex(days)
qc['alex_days_with_tavg']=int(alex.alex_tavg_c.notna().sum()); qc['alex_last_date']=str(alex.alex_tavg_c.last_valid_index().date())

master=g.join(alex)
master['month']=master.index.month
master['et_mm_day']=master.et_mm_day.round(4)
for c in ['rootmoist_mm_mean','rootmoist_mm_min','rootmoist_mm_max']: master[c]=master[c].round(3)
master['n_steps']=master.n_steps.astype('Int64'); master['et_neg_steps']=master.et_neg_steps.astype('Int64')
master=master.rename(columns={'n_steps':'gldas_steps_per_day','et_neg_steps':'et_negative_steps'})
master['lat']=30.9; master['lon']=31.0
master.reset_index().to_csv(f'{out}/nile_delta_daily_clean_2023.csv',index=False)

# ---- GPM grid
t=tifffile.TiffFile(GPM); a=t.pages[0].asarray().astype(float)
a[a<-9000]=np.nan
res=0.1; lat0,lon0=31.8,29.5
rows=[]
for i in range(a.shape[0]):
    for j in range(a.shape[1]):
        rows.append(dict(lat=round(lat0-res*(i+.5),3),lon=round(lon0+res*(j+.5),3),precip_mm_hr_mean_2023=a[i,j]))
gp=pd.DataFrame(rows); gp['precip_mm_year_2023']=gp.precip_mm_hr_mean_2023*24*365
gp.to_csv(f'{out}/gpm_imerg_precip_2023_grid_clean.csv',index=False,float_format='%.5f')
cell=gp[(gp.lat.between(30.85,31.15))&(gp.lon.between(30.85,31.15))]
qc['gpm_cells']=len(gp); qc['gpm_nan']=int(gp.precip_mm_hr_mean_2023.isna().sum())
qc['gpm_annual_mm_cells_near_30.9N_31.0E']=round(float(cell.precip_mm_year_2023.mean()),1)
qc['gpm_annual_mm_range']=[round(float(gp.precip_mm_year_2023.min()),1),round(float(gp.precip_mm_year_2023.max()),1)]
qc['gpm_annual_mm_mean_all']=round(float(gp.precip_mm_year_2023.mean()),1)

# ---- monthly summary for storytelling
m=master.groupby('month').agg(et_mm_month=('et_mm_day','sum'),rootmoist_mm_mean=('rootmoist_mm_mean','mean'),
   rootmoist_mm_min=('rootmoist_mm_min','min'),rootmoist_mm_max=('rootmoist_mm_max','max'),
   alex_tavg_c_mean=('alex_tavg_c','mean'),alex_days_with_data=('alex_tavg_c','count')).round(2)
m.to_csv(f'{out}/storytelling_monthly_summary_2023.csv')
qc['et_year_mm']=round(float(master.et_mm_day.sum()),1)
qc['rm_mean']=round(float(master.rootmoist_mm_mean.mean()),1)
qc['rm_min_day']=str(master.rootmoist_mm_min.idxmin().date()); qc['rm_min']=float(master.rootmoist_mm_min.min())
qc['rm_max_day']=str(master.rootmoist_mm_max.idxmax().date()); qc['rm_max']=float(master.rootmoist_mm_max.max())
qc['et_peak_month']=int(m.et_mm_month.idxmax()); qc['et_peak_mm']=float(m.et_mm_month.max()); qc['et_low_month']=int(m.et_mm_month.idxmin()); qc['et_low_mm']=float(m.et_mm_month.min())
print(json.dumps(qc,indent=1,default=str)); print(m)
print(master.isna().sum())
