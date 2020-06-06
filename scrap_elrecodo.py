import pandas as pd
import requests
from bs4 import BeautifulSoup


base_url = 'https://www.el-recodo.com'
link_url = 'https://www.el-recodo.com/music?lang=en'


def request_text(url):
    return requests.get(url).text


def get_table(url):
    print(url)
    page_text = requests.get(url).text
    df = pd.read_html(page_text)[0]
    return df


def get_links():
    page_text = request_text(link_url)
    soup = BeautifulSoup(page_text)
    soup_list = soup.find_all('div', {'class': 'card m-1'})
    links = [base_url+'/'+l.a.get('href') for l in soup_list]
    return links

def get_npages(sub_url):

    page_text = request_text(sub_url)
    soup = BeautifulSoup(page_text)
    soup1 = soup.find_all('nav', {'aria-label': 'Page navigation'})[0]
    soup2 = soup1.find_all('a',{'class':'page-link'})
    npages = len(set([l.get('href') for l in soup2]))-1

    return npages


links = get_links()
ext_links = []

for l in links:
    np = get_npages(l)
    for i in range(1,np+1):
        suffix = '&lang=en'
        repltext = '&P='+str(i)+suffix
        ext_l = l.replace(suffix, repltext)
        print(ext_l)
        ext_links.append(ext_l)


tables = [get_table(el) for el in ext_links]

df = pd.concat(tables, ignore_index=True)

csv_cols = [
    'TITLE',
    'ORCHESTRA',
    'SINGER',
    'STYLE',
    'DATE',
    'COMPOSER',
    'AUTHOR',
    'SOLOIST',
    'DIRECTOR'
]

df.to_csv('elrecodo.csv', columns=csv_cols)
