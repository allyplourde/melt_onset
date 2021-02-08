import sys
import io
import ftplib 
import os

 
if __name__ == "__main__":

    download_path = 'C:/Users/Owner/repos/melt_onset/Imagery/R1'
    FTP = ftplib.FTP('data.eodms-sgdot.nrcan-rncan.gc.ca')
    
    FTP.login()

    # set working directory to FTP directory provided in
    # EODMS delivery notification email
    FTP.cwd('/public/carts/ec30ff36-c727-4f0e-bf5d-7766ff76be56')
    os.chdir(download_path)
    print(FTP.pwd())
    
    '''Get all folders and files on FTP Server'''
    #folders , files = list_all_ftp_files(ftp , '/')

    for folder in FTP.nlst():
        print(FTP.nlst(folder))
        f = FTP.nlst(folder)[0]
        ff, file_name = f.split('/')
        r = io.BytesIO()
        with open(file_name, "wb") as outfile:
            FTP.retrbinary('RETR {0}'.format(f), r.write)
            outfile.write(r.getbuffer())
            print("downloaded: {0}".format(file_name))

    