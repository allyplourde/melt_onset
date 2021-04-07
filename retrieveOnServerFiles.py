### Retrive On-Server Files ###
#
# given a csv of filepaths, this script
# retrives the files and copies them over
# into a new directory.
# filepaths can be retrived by querying the "location"
# field of tblmetadata_on_server
#
#

import os
from shutil import copyfile
import pandas as pd

#Source files
FILE_WITH_PATHS = "Imagery/radarsat2_onserver_filepaths_2011.csv"
#Destination 
TARGET_FOLDER = "Imagery\\R2\\2011\\Ascending"

if __name__ == "__main__":

    df = pd.read_csv(FILE_WITH_PATHS)
    ascending = df.loc[df['PassDir']==' Ascending']['Filepath'].values
    descending = df.loc[df['PassDir']==' Descending']['Filepath'].values
    
    
    for path in ascending:
        #get source filename
        path = path.split("/")
        filename = path[-1]
        
        # On Castor, 'Tank' needs to be replaced with 'J:'
        # these lines can be skipped if running on pollux
        path[1] = "J:"
        src = "/".join(path[1:])
        
        # create path to target folder
        dst = os.path.join(TARGET_FOLDER, filename)
        
        #transfer files!
        copyfile(src, dst)
    
        
        
