
# ======================================================= #
# LIBRARIES
# ======================================================= #
import os
import pandas as pd
import time
from cpforager import parameters, utils, AXY


# ======================================================= #
# DIRECTORIES
# ======================================================= #
root_dir = os.getcwd()
data_dir = os.path.join(root_dir, "data", "lv0")
config_dir = os.path.join(root_dir, "configs")
test_dir = os.path.join(root_dir, "tests", "axy_lev0_to_lev1_lev2")

lv1_dir = os.path.join(root_dir, "data", 'lv1')
lv2_dir = os.path.join(root_dir, "data", 'lv2')

# ======================================================= #
# PARAMETERS
# ======================================================= #

# set metadata
fieldwork = "BRA_ABR_2021_09"
colony = "BRA_ABR_SBA"
file_name = "BRA_ABR_SBA_2021-08-12_SDAC_03_V18308_M_GPS_AXY_AB04_UTC.csv"

# set configuration paths
config_colony_path = os.path.join(config_dir, "colony_%s.yml" % (colony))
config_trips_path = os.path.join(config_dir, "trips.yml")
config_dives_path = os.path.join(config_dir, "dives_SULA.yml")
config_accelero_path = os.path.join(config_dir, "accelero_rollavg.yml")

# set parameters dictionaries
params = parameters.get_params([config_colony_path, config_trips_path, config_dives_path, config_accelero_path])
plot_params = parameters.get_plot_params()


# ======================================================= #
# TEST AXY CLASS
# ======================================================= #

# set file infos
file_id = file_name.replace(".csv", "")
file_path = os.path.join(data_dir, fieldwork, file_name)

# load raw data
df = pd.read_csv(file_path, sep=",")

# produce "datetime" column of type datetime64
df["datetime"] = pd.to_datetime(df["date"] + " " + df["time"], format="%Y-%m-%d %H:%M:%S.%f", dayfirst=False)

# if time is at UTC, convert it to local datetime
if "_UTC" in file_name: df = utils.convert_utc_to_loc(df, params.get("local_tz"))

# build AXY object
axy = AXY(df=df, group=fieldwork, id=file_id, params=params)

# test built-in methods
print(axy)
print(len(axy))
print(axy[1312])
print(axy.df_gps.iloc[1312])

# test display_data_summary method
axy.display_data_summary()

# test full_diag, maps_diag, folium_map methods
_ = axy.full_diag(test_dir, "%s_diag" % file_id, plot_params)
_ = axy.maps_diag(test_dir, "%s_map" % file_id, plot_params)
_ = axy.folium_map(test_dir, "%s_fmap" % file_id, plot_params)

# ======================================================= #
# SAVE DATAFRAMES
# ======================================================= #
axy.df.to_csv(os.path.join(lv1_dir, fieldwork, "%s_%s" % (file_id,"raw.csv")), index=False)


# ======================================================= #
# TEST FAST FULL DIAGNOSTIC
# ======================================================= #

# compare plotting speed of full diagnostic
for fast in [False, True]:
    start = time.time()
    _ = axy.full_diag(test_dir, "%s_diag_fast=%r" % (file_id, fast), plot_params, fast=fast)
    end = time.time()
    print("Full diagnostic [fast=%r] : %.1f minutes" % (fast, (end-start)/60))


# ======================================================= #
# TEST AXY INTERPOLATION
# ======================================================= #
# build a regular interpolation datetime
interp_freq_secs = [5,10,20,30]

for interp in interp_freq_secs:
    
    interp_datetime = pd.date_range(start=axy.df_gps["datetime"].iloc[0], end=axy.df_gps["datetime"].iloc[-1], freq=pd.Timedelta(seconds=interp), periods=None)
    
    # compute interpolated positions from AXY method
    df_gps_interp = axy.interpolate_lat_lon(interp_datetime, add_proxy=True)
    
    # merge dataframes on datetime column
    df_wo_positions = axy.df[["date", "time", "ax", "ay", "az", "pressure", "temperature", "datetime"]]
    df_interp = pd.merge(df_wo_positions, df_gps_interp, on="datetime", how="left")
    
    # build another AXY object with interpolated dataframe
    axy_interp = AXY(df=df_interp, group=fieldwork, id="%s_%s" % (axy.id, "interp"), params=params)
    
    # save df with axy at interpolated gps resolution (level 2)
    axy_interp.df_gps.to_csv(os.path.join(lv2_dir, fieldwork, "%s_%s%s" % (file_id,interp,"s.csv")), index=False)
    
