
import os
import glob
import pandas as pd
PATH_TO_SIGLIB = "J:\\SCRATCH\\aplourde\\SigLib\\"
CONFIG_FILE = "admiraltyInlet_config.cfg"
IMAGE_DIRECTORY = "J:\\SCRATCH\\aplourde\\melt_onset\\Imagery\\R2_processed\\2011\\Ascending\\"


if __name__ == "__main__":
    
    os.chdir(IMAGE_DIRECTORY)
    cols = [ \
                "band", \
                "dynamicRange", \
                "dataType", \
                "nodata value", \
                "min", \
                "max", \
                "mean", \
                "std", \
                "obj", \
                "instid", \
                "imgref", \
                "date", \
                "doy"]
                
    stats = pd.DataFrame(columns = cols)
    
    for file in glob.glob("*.csv"):
    
        f = file.split("_")
        inst = f[-3]
        n = len(inst)
        instid = inst[-5:]
        obj = inst[0:(n-5)]
        imgref = "_".join(f[:-5])
        date = pd.to_datetime(f[0], format="%Y%m%d")
        doy = date.dayofyear
        
        df = pd.read_csv(file, header=None, names=cols)
        df.columns = stats.columns
        
        df.loc[:, "obj"] = obj
        df.loc[:, "instid"] = instid
        df.loc[:, "imgref"] = imgref
        df.loc[:, "date"] = date
        df.loc[:, "doy"] = doy
        
        stats = pd.concat([stats, df], ignore_index=True)
    print(stats)
    stats.to_csv("admiraltyInlet_2011.csv", index=False)
    
    
    
    
    
    
    