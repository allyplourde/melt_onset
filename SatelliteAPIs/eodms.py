# adaptation from GC collab python code for interacting with
# EODMS API for ordering Radarsat-1 imagery
# Github: https://github.com/nrcan-eodms-sgdot-rncan/eodms-ogc-client-py/wiki

# dependencies: pip install requests

import requests
import xml.etree.ElementTree as ET
import getpass
import pandas
import json
from osgeo import ogr

# GetRecords POST request 
def getRecordsfromXML(max_records, start_date, end_date, lower_corner, upper_corner):
    # Submit a GetRecords to the CSW

    # Step 1: Generate xml request
   # Submit a GetRecords to the CSW
    post_xml = '''<csw:GetRecords xmlns:csw="http://www.opengis.net/cat/csw/2.0.2" 
    xmlns:ogc="http://www.opengis.net/ogc" service="CSW" 
    version="2.0.2" resultType="results" 
    startPosition="1" 
    maxRecords="200" 
    outputFormat="application/xml" 
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" 
    xsi:schemaLocation="http://www.opengis.net/cat/csw/2.0.2 
    http://schemas.opengis.net/csw/2.0.2/CSW-discovery.xsd" 
    xmlns:gml="http://www.opengis.net/gml" 
    xmlns:gmd="http://www.isotc211.org/2005/gmd" 
    outputSchema="http://www.opengis.net/cat/csw/2.0.2">
    <csw:Query typeNames="gmd:MD_Metadata">
        <csw:ElementSetName>full</csw:ElementSetName>
        <csw:Constraint version='1.1.0'>
            <ogc:Filter>
                <ogc:And>
                    <ogc:PropertyIsLike escapeChar='\\' singleChar='?' wildCard='*'>
                        <ogc:PropertyName>apiso:title</ogc:PropertyName>
                        <ogc:Literal>Radarsat-1*</ogc:Literal>
                    </ogc:PropertyIsLike>
                    <ogc:PropertyIsGreaterThanOrEqualTo>
                        <ogc:PropertyName>dc:date</ogc:PropertyName>
                        <ogc:Literal>2000-04-01T10:50:50Z</ogc:Literal>
                    </ogc:PropertyIsGreaterThanOrEqualTo>
                    <ogc:PropertyIsLessThanOrEqualTo>
                        <ogc:PropertyName>dc:date</ogc:PropertyName>
                        <ogc:Literal>2000-07-31T10:50:50Z</ogc:Literal>
                    </ogc:PropertyIsLessThanOrEqualTo>
                </ogc:And>
            </ogc:Filter>
        </csw:Constraint>
    </csw:Query>
</csw:GetRecords>''' #% (max_records, start_date, end_date, lower_corner, upper_corner)

    """
                    <ogc:BBOX>
                        <ogc:PropertyName>ows:BoundingBox</ogc:propertyname>
                        <gml:Envelope>
                            <gml:lowerCorner>%s</gml:lowercorner>
                            <gml:upperCorner>%s</gml:uppercorner>
                        </gml:Envelope>
                    </ogc:BBOX>
    """

    # Step 2: Send request

    csw_url = 'https://www.eodms-sgdot.nrcan-rncan.gc.ca/MetaManagerCSW/csw/eodms_catalog'
    headers = {'Content-Type':'application/xml'}
    csw_r = requests.post(csw_url, data=post_xml)

    root = ET.fromstring(csw_r.content)

    #print(csw_r.content)

    record_tag = '{http://www.opengis.net/cat/csw/2.0.2}Record'
    rec_element = []
    for child in root.iter("*"):
        if child.tag == record_tag:
            rec_element.append(child)
            
    # Get the ID of the first record
    rec_id = []
    if len(rec_element) > 0:
        for child in rec_element:
            id_tag = '{http://purl.org/dc/elements/1.1/}identifier'
            id_el = child.find(id_tag)
            rec_id.append(id_el.text)

    return rec_id

def getRecordsFromCSV(filename):
    """ alternative method to build query from CSV file of reords
        input:
            filename - (string) path/name to .csv file containing records
    """

    query = {
        "destinations": [], 
        "items": []
    }
    
    results_csv = pandas.read_csv(filename)
    im_info = results_csv["Image Info"]

    for row in im_info:
        info = row.replace('" ', '", ')
        info = info.replace("] ","], ")
        info_dict = json.loads(info)

        query['items'].append({"collectionId": info_dict["collectionID"], 
                                "recordId": info_dict["imageID"]})
    
    return query

def getRecords(session, start_date, end_date, coords):
    """ query EODMS database for records within region and date range
        input:
            session - requests session for HTTP requests
            start_date - (pandas datetime) find images after this date
            end_date - (pandas datetime) find images before this date
            coords - region on interest
        output:
            records - (list) records matchign search criteria
    """

    # convert coordiantes to string
    polygon_coordinates = ''
    for i in range(len(coords)):
        polygon_coordinates += str(coords[i][0]) + '+' + str(coords[i][1])
        if i < len(coords)-1:
            polygon_coordinates += '%2C'

    #query EODMS database
    query_url = '''https://www.eodms-sgdot.nrcan-rncan.gc.ca/wes/rapi/search?collection=Radarsat1&''' + \
                '''query=CATALOG_IMAGE.THE_GEOM_4326+INTERSECTS+POLYGON+%28%28''' + \
                    polygon_coordinates + '''%29%29&''' + \
                '''resultField=RSAT1.BEAM_MNEMONIC&maxResults=5000&format=json'''
    response = session.get(query_url)

    rsp = response.content
    response_dict = json.loads(rsp.decode('utf-8'))


    results = response_dict['results']
    n = len(results)    
    if n == 1000:
        print("Warning: limit of records has been reached, results may be incomplete")
        print("Try reducing the region of interest to avoid reaching the query limit")

    #Filter query results for specified daterange
    records = []  #records to order
    for result in results:
        if result["isOrderable"]:
            for item in result["metadata2"]:
                if item["id"] == "CATALOG_IMAGE.START_DATETIME":
                    date = pandas.to_datetime(item["value"])
            if date >= start_date and date <= end_date:
                record_id = result["recordId"]
                collection_id = result["collectionId"]
                records.append([record_id, collection_id])
    
    return records

def buildQuery(records):
    """ builds query to order records 
        input:
            records - (list) record and collection ids from EODMS query result
        output:
            query - (dict) dictionary of records
    """

    query = {"destinations": [], "items": []}

    for item in records:
        query['items'].append({"collectionId": item[1], "recordId": item[0]})
    
    return query

def submit_post(query):
    """ submits order to EODMS
        input:
            query - (dict) query with record and collection ids
    """

    rest_url = "https://www.eodms-sgdot.nrcan-rncan.gc.ca/wes/rapi/order"
    response = session.post(rest_url, data=str(query))

def extractCoords(filename):
    """ extracts coordinate geometry from an ESRI shapefile
        input:
            filename - (string) path+name of file
        output:
            coords - (list) list of polygon coordinates
    """

    shpfile = ogr.Open(filename)
    shape = shpfile.GetLayer(0)
    feature = shape.GetFeature(0)

    jsn = feature.ExportToJson()
    dct = json.loads(jsn)

    geom = dct["geometry"]
    coords = geom["coordinates"]

    coordinates = coords[0]

    return coordinates


if __name__ == "__main__":

    #set to true to order imagery,
    #(link will be sent via email)

    submit_order = False

    session = requests.Session()
    username = input("Enter your EODMS username: ")
    password = getpass.getpass("Enter your EODMS password: ")
    session.auth = (username, password)

    #Date range
    start_date = pandas.to_datetime("2010-03-01 00:00:00 GMT")
    end_date = pandas.to_datetime("2010-07-31 00:00:00 GMT")


    #Extract Coordinates from Shapefile
    filename = 'ROI_AI/ROI_AI.shp'
    coords = extractCoords(filename)

    #Query EODMS
    records = getRecords(session, start_date, end_date, coords)

    n = len(records)
    print("Preparing {} records for order.".format(n))
     
    orderquery = buildQuery(records)

    #Submit Order
    if submit_order:
        submit_post(orderquery)
