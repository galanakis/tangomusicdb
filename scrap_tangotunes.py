import requests
from bs4 import BeautifulSoup
import pandas as pd
import re


def get_df(url):
    #url = 'https://www.tangotunes.com/no-aflojes-39136-rp.html'
    soup = BeautifulSoup(requests.get(url).text)
    data = soup.find_all('div',{'class':'additional-data'})[0]
    rows = data.find_all('div',{'class','row'})
    pairs = [[r.text.strip() for r in row.find_all('div')] for row in rows]

    print('----')
    print(url)
    print('----')
    df = pd.DataFrame(dict(pairs), index=[0])
    print(df)
    return df



url = 'https://www.tangotunes.com/vinyls.html?limit=all'
soup = BeautifulSoup(requests.get(url).text)
box = soup.find('div',{'class':'box product-listing'})
data = box.find_all('ul',{'class','odd'})

vinyl_refs = [d.find('a').get('href') for d in data]

url = 'https://www.tangotunes.com/shellacs.html?limit=all'
soup = BeautifulSoup(requests.get(url).text)
box = soup.find('div',{'class':'box product-listing'})
data = box.find_all('ul',{'class','odd'})

shellac_refs = [d.find('a').get('href') for d in data]

refs = vinyl_refs + shellac_refs

df = pd.concat([get_df(ref) for ref in refs], ignore_index=True)

df_filter = df.drop(columns=["Format", "Credit increase", "Price saving", "Album Tunes", "Album"])

df_filter[df_filter['Duration'].notnull()].to_csv('tangotunes.csv')