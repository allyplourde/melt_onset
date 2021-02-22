# adaptation from GC collab python code for interacting with
# EODMS API for ordering Radarsat-1 imagery
# Github: https://github.com/nrcan-eodms-sgdot-rncan/eodms-ogc-client-py/wiki

# dependencies: pip install requests

import requests
import xml.etree.ElementTree as ET
import getpass

# GetRecords POST request 
def getRecords(max_records, start_date, end_date, lower_corner, upper_corner):
    # Submit a GetRecords to the CSW

    # Step 1: Generate xml request
   # Submit a GetRecords to the CSW
    post_xml = '''<?xml version="1.0" encoding="UTF-8"?>
    <csw:GetRecords service='CSW' version='2.0.2'
        maxRecords='15'
        startPosition='1'
        resultType='results'
        outputFormat='application/xml'
        outputSchema='http://www.opengis.net/cat/csw/2.0.2'
        xmlns='http://www.opengis.net/cat/csw/2.0.2'
        xmlns:csw='http://www.opengis.net/cat/csw/2.0.2'
        xmlns:ogc='http://www.opengis.net/ogc'
        xmlns:ows='http://www.opengis.net/ows'
        xmlns:dc='http://purl.org/dc/elements/1.1/'
        xmlns:dct='http://purl.org/dc/terms/'
        xmlns:gml='http://www.opengis.net/gml'
        xmlns:xsi='http://www.w3.org/2001/XMLSchema-instance'
        xsi:schemaLocation='http://www.opengis.net/cat/csw/2.0.2
        http://schemas.opengis.net/csw/2.0.2/CSW-discovery.xsd'>
        <csw:Query typeNames='csw:Record'>
            <csw:ElementSetName typeNames='csw:Record'>full</csw:ElementSetName>
            <csw:Constraint version="1.1.0">
                <ogc:Filter>
                    <ogc:And>
                        <ogc:PropertyIsLessThan>
                            <ogc:PropertyName>dc:date</ogc:PropertyName>
                            <ogc:Literal>%s</ogc:Literal>
                        </ogc:PropertyIsLessThan>
                        <ogc:PropertyIsGreaterThan>
                            <ogc:PropertyName>dc:date</ogc:PropertyName>
                            <ogc:Literal>%s</ogc:Literal>
                        </ogc:PropertyIsGreaterThan>
                        <ogc:PropertyIsLike escapeChar='\\' singleChar='?' wildCard='*'>
                            <ogc:PropertyName>dc:title</ogc:PropertyName>
                            <ogc:Literal>*</ogc:Literal>
                        </ogc:PropertyIsLike>
                        <ogc:BBOX>
                            <ogc:PropertyName>ows:BoundingBox</ogc:PropertyName>
                            <gml:Envelope>
                                <gml:lowerCorner>%s</gml:lowerCorner>
                                <gml:upperCorner>%s</gml:upperCorner>
                            </gml:Envelope>
                        </ogc:BBOX>
                    </ogc:And>
            </ogc:Filter>
            </csw:Constraint>
        </csw:Query>
    </csw:GetRecords>''' % (end_date, start_date, lower_corner, upper_corner)

    # Step 2: Send request

    csw_url = 'https://www.eodms-sgdot.nrcan-rncan.gc.ca/MetaManagerCSW/csw/eodms_catalog'
    headers = {'Content-Type':'application/xml'}
    csw_r = requests.post(csw_url, data=post_xml)

    root = ET.fromstring(csw_r.content)

    print(csw_r.content)

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

def submit_post(query):
    rest_url = "https://www.eodms-sgdot.nrcan-rncan.gc.ca/wes/rapi/order"
        
    session = requests.Session()
    username = input("Enter your EODMS username: ")
    password = getpass.getpass("Enter your EODMS password: ")
    session.auth = (username, password)

    response = session.post(rest_url, data=str(query))
    print(response.content) 


if __name__ == "__main__":

    #set to true to order imagery,
    #link will be sent via email and
    # will be avaible on the EODMS 
    submit_order = False

    #Coordinate for Admiralty Inlet
    bounding_box = {'lower_corner': '-85.000000 73.000000', #lng-lat, string input
                    'upper_corner': '-84.230000 73.600000'}

    date_range = ["2017-04-01Z", "2017-07-31Z"] #start date, end date, "YYYY-MM-DDZ"

    maxRecords = 10

    records = getRecords(maxRecords, date_range[0], date_range[1], bounding_box['lower_corner'], bounding_box['upper_corner'])
    print("Number of Records: ", len(records))
    query = {
        "destinations": [], 
        "items": []
    }

    for record in records:
        query['items'].append(
                {
                    "collectionId": "Radarsat1", 
                    "recordId": record
                })
    print(query)


    if submit_order:
        submit_post(query)
