import pandas as pd
import xml.etree.ElementTree as ET ## XML parsing

# This little module takes the xml file exported by
# Apple music and converts it into a pandas dataframe
# and then exports it into a csv.

lib_file = 'Library.xml'
csv_file = 'Library.csv'

tree = ET.parse(lib_file)
root = tree.getroot()
tracks = root.find('dict').find('dict').findall('dict')


def track_to_dict(track_xml):
    elements = [x.text for x in track_xml.iter() if x is not track_xml]
    keys = elements[0::2]
    values = elements[1::2]
    return dict(zip(keys,values))


tracks_df = pd.DataFrame(map(track_to_dict, tracks))

tracks_df.to_csv(csv_file)