import os
import pandas as pd
from cpforager import parameters, utils, AXY 

# =============================================================================
# LEVEL 0 to LEVEL 1 and LEVEL 2 interpolated
# =============================================================================

# config stuff 
root_dir = os.getcwd()
data_dir = os.path.join(root_dir, "data", "lv0")
config_dir = os.path.join(root_dir, "configs")

lv1_dir = os.path.join("data", 'lv1')
lv2_dir = os.path.join("data", 'lv2')

config_trips_path = os.path.join(config_dir, "trips.yml")
config_dives_path = os.path.join(config_dir, "dives_SULA.yml")
# config_accelero_path = os.path.join(config_dir, "accelero_highpass.yml")
config_accelero_path = os.path.join(config_dir, "accelero_rollavg.yml")

# fieldworks to process
# colonies = ['BRA_ABR_SBA',
#             'BRA_ABR_SBA',
#             'BRA_ABR_SBA',
#             'BRA_ABR_SBA']

# fieldworks = ['BRA_ABR_2022_09', 
#               'BRA_ABR_2023_09'
#               'BRA_ABR_2024_09'
#               'BRA_ABR_2025_09']

colonies = ['BRA_ABR_SBA']
fieldworks = ['BRA_ABR_2021_09']

# set interpolation frequency
interp_freq_secs = [5,10,30,60]
# interp_freq_secs = [60]

for interp in interp_freq_secs:
    print(interp)
    
    for (fieldwork, colony) in zip(fieldworks, colonies):
        print(fieldwork)
    
        # list of files to process
        files = os.listdir(os.path.join(data_dir, fieldwork))
        n_files = len(files)
    
        # set configuration paths according to colony code
        config_colony_path = os.path.join(config_dir, "colony_%s.yml" % (colony))
        
        # set parameters dictionaries
        params = parameters.get_params([config_colony_path, config_trips_path, config_dives_path, config_accelero_path])
    
        # create results folders
        lv1_fw_dir = os.path.join(lv1_dir, fieldwork)
        if not os.path.exists(lv1_fw_dir):
            os.makedirs(lv1_fw_dir)
            
        lv2_fw_dir = os.path.join(lv2_dir, fieldwork)
        if not os.path.exists(lv2_fw_dir):
            os.makedirs(lv2_fw_dir)
            
        # loop over files in directory
        for k in range(n_files):
            # set file infos
            file_name = files[k]
            
            # skip metadata file
            if '_AXY_' not in file_name : 
                continue
            
            file_id = file_name.replace(".csv", "")
            file_path = os.path.join(data_dir, fieldwork, file_name)
            
            print(f'\nfile {k}/{n_files}')
            print(file_id)
    
            # load raw data
            df = pd.read_csv(file_path, sep=",")
            
            # produce "datetime" column of type datetime64
            df["datetime"] = pd.to_datetime(df["date"] + " " + df["time"], format="mixed", dayfirst=False)
    
            # if time is at UTC, convert it to local datetime
            if "_UTC" in file_name: df = utils.convert_utc_to_loc(df, params.get("local_tz"))
            
            # covert to axy object, no interpolation
            axy = AXY(df=df, group=fieldwork, id=file_id, params=params)
            
            # save df with axy at gps resolution (level 1)
            #axy.df_gps.to_csv(os.path.join(lv1_fw_dir, file_name), index=False)
            axy.df_gps.to_csv(os.path.join(lv1_fw_dir, file_name), index=False)
            
            #interpolate axy
            interp_datetime = pd.date_range(start=axy.df_gps["datetime"].iloc[0], end=axy.df_gps["datetime"].iloc[-1], freq=pd.Timedelta(seconds=interp), periods=None)
            df_gps_interp = axy.interpolate_lat_lon(interp_datetime, add_proxy=True)
            df_wo_positions = axy.df[["date", "time", "ax", "ay", "az", "pressure", "temperature", "datetime"]]
            df_interp = pd.merge(df_gps_interp, df_wo_positions, on="datetime", how="outer")
            
            # create axy object with interpolated data
            axy_interp = AXY(df=df_interp, group=fieldwork, id="%s_%s" % (axy.id, "interp"), params=params)
            
            # save df with axy at interpolated gps resolution (level 2)
            
            #Add GPS resolution
            #axy_interp.df_gps.to_csv(os.path.join(lv2_fw_dir, file_name), index=False)
            axy_interp.df_gps.to_csv(os.path.join(lv2_fw_dir, "%s_%s%s" % (file_id,interp,"s.csv")), index=False)
        
        print('\n------------------------------------------------------------\n')
    



