import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
import os

cache_dirname = os.path.join('tangotunes', 'cache')

# Cached url request.
# Looks for the page text in a predefined file,
# passes the request to the server if file not found.
# This replicates the funcionality of "requests_cache",
# But has the advantage that the cache is more readable.
def requests_cache(link):
    filename = os.path.join(cache_dirname, os.path.basename(os.path.normpath(link)) + ".html")
    try:
        page_text = open(filename, "r").read()
    except IOError:
        page_text = requests.get(link).text
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        open(filename, "w").write(page_text)
    return page_text


def get_df(url):
    #url = 'https://www.tangotunes.com/no-aflojes-39136-rp.html'
    soup = BeautifulSoup(requests_cache(url))

    title = soup.find('div',{'class':'product-name'}).h1.text
    data = soup.find_all('div',{'class':'additional-data'})[0]
    rows = data.find_all('div',{'class','row'})
    pairs = [[r.text.strip() for r in row.find_all('div')] for row in rows]

    print('----')
    print(url)
    print('----')
    df = pd.DataFrame(dict(pairs), index=[0])
    df['Title'] = title
    print(df)
    return df



url = 'https://www.tangotunes.com/vinyls.html?limit=all'
soup = BeautifulSoup(requests_cache(url))
box = soup.find('div',{'class':'box product-listing'})
data = box.find_all('ul',{'class','odd'})

vinyl_refs = [d.find('a').get('href') for d in data]

url = 'https://www.tangotunes.com/shellacs.html?limit=all'
soup = BeautifulSoup(requests_cache(url))
box = soup.find('div',{'class':'box product-listing'})
data = box.find_all('ul',{'class','odd'})

shellac_refs = [d.find('a').get('href') for d in data]

refs = vinyl_refs + shellac_refs

df = pd.concat([get_df(ref) for ref in refs], ignore_index=True)

csv_cols = [
    "Title",
    "Orchestra",
    "Singer",
    "Record Date",
    "Genre",
    "Duration",
    "Label",
    "Disc type",
    "Disc No."
]

#df_filter = df.drop(columns=["Format", "Credit increase", "Price saving", "Album Tunes", "Album"])

tunes_ind = df['Duration'].notnull()
df[tunes_ind].to_csv('tangotunes/tangotunes.csv', columns=csv_cols)