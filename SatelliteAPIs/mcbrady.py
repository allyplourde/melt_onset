from eodms_api_client import EodmsAPI, params



client = EodmsAPI(collection='Radarsat2')
print(client)
client.query(start='2020-08-15', end='2020-08-22', geometry='C:/Users/Owner/repos/melt_onset/SatelliteAPIs/instances/roi_admiraltyinlet.shp')

#is_valid = params.validate_query_args({'start':'2020-08-15', 'end':'2020-08-22', 'geometry':'C:/Users/Owner/repos/melt_onset/SatelliteAPIs/lakewinnipegnorth.geojson'}, collection='RCMImageProducts')
#print(is_valid)

#keys = params.generate_meta_keys('RCMImageProducts')
#print(keys)