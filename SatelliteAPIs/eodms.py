# adaptation from GC collab python code for interacting with
# EODMS API for ordering Radarsat-1 imagery
# Github: https://github.com/nrcan-eodms-sgdot-rncan/eodms-ogc-client-py/wiki

# dependencies: pip install requests

import requests
import xml.etree.ElementTree as ET
import getpass
import pandas
import json

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

def getRecordsFromCSV():
    query = {
        "destinations": [], 
        "items": []
    }
    
    results_csv = pandas.read_csv("Results2000.csv")
    im_info = results_csv["Image Info"]

    for row in im_info:
        info = row.replace('" ', '", ')
        info = info.replace("] ","], ")
        info_dict = json.loads(info)

        query['items'].append(
                {
                    "collectionId": info_dict["collectionID"], 
                    "recordId": info_dict["imageID"]
                })
    
    return query

def getRecords(session, start_date, end_date):
    query_url = '''https://www.eodms-sgdot.nrcan-rncan.gc.ca/wes/rapi/search?collection=Radarsat1&query=CATALOG_IMAGE.THE_GEOM_4326+INTERSECTS+POLYGON+%28%28-84.6424242424242+73.9212121212121%2C-82.5187878787878+73.7563636363636%2C-85.0593939393939+71.7878787878788%2C-87.3672727272726+72.8545454545455%2C-84.6424242424242+73.9212121212121%29%29&resultField=RSAT1.BEAM_MNEMONIC&maxResults=5000&format=json'''
    response = session.get(query_url)

    rsp = response.content
    response_dict = json.loads(rsp.decode('utf-8'))

    results = response_dict['results']
    print("A total of {} images were found for the ROI".format(len(results)))
    records = []
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
    query = {
        "destinations": [], 
        "items": []
    }

    for item in records:

        query['items'].append(
                    {
                        "collectionId": item[1], 
                        "recordId": item[0]
                    })
    
    return query

def submit_post(query):
    rest_url = "https://www.eodms-sgdot.nrcan-rncan.gc.ca/wes/rapi/order"
    response = session.post(rest_url, data=str(query))
    
    print(response.content) 


if __name__ == "__main__":

    #set to true to order imagery,
    #link will be sent via email and
    # will be avaible on the EODMS 

    submit_order = False

    session = requests.Session()
    username = input("Enter your EODMS username: ")
    password = getpass.getpass("Enter your EODMS password: ")
    session.auth = (username, password)

    start_date = pandas.to_datetime("2010-03-01 00:00:00 GMT")
    print(start_date)
    end_date = pandas.to_datetime("2010-07-31 00:00:00 GMT")
    print(end_date)

    records = getRecords(session, start_date, end_date)


    
    """
    #Coordinate for Admiralty Inlet
    bounding_box = {'lower_corner': '-85.000000 73.000000', #lng-lat, string input
                    'upper_corner': '-84.230000 73.600000'}

    """

    n = len(records)
    print("Found {} records.".format(n))

    n_orders = round(n/50)
    orders = []
    for i in range(n_orders):
        if i == n_orders - 1:
            orders.append(records[i*50:])
        else:
            orders.append(records[i*50:i*50+49])
            print(i*50,i*50+49)
    
    query = buildQuery(records)

    if submit_order:
        submit_post(query)
