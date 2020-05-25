import requests
from bs4 import BeautifulSoup
import pandas as pd
import re

url = 'https://www.todotango.com/musica/obras/musica/-/0/0/'

soup = BeautifulSoup(requests.get(url).text)

# Weird way of making a list of links but it works
results = [[a['href'] for a in itemlista.find_all('a')] for itemlista in soup.find_all('div',{"class":"itemlista"})]
temas = [item for sublist in results for item in sublist]


def get_by_id(sp, label):
    return [s.text for s in soup.find_all(id=label)]


def get_df(url):

    print('----')
    print(url)

    #url2='https://www.todotango.com/musica/tema/2601/Bahia-Blanca/'
    soup = BeautifulSoup(requests.get(url).text)

    titulo = "".join([s.text for s in soup.find_all(id='main_Tema1_lbl_Titulo')])
    ritmo =  "".join([s.text for s in soup.find_all(id='main_Tema1_lbl_Ritmo')])
    ano =    "".join([s.text for s in soup.find_all(id='main_Tema1_lbl_Ano')])

    creadores_musica = ", ".join([s.text for s in soup.find_all(id=re.compile('main_Tema1_Tema_Autores1_RP_TemasCreadores_AutoresMusica_hl_Creador_\d'))])
    creadores_letra =  ", ".join([s.text for s in soup.find_all(id=re.compile('main_Tema1_Tema_Autores1_RP_TemasCreadores_AutoresLetra_hl_Creador_0\d'))])

    ritmoduraction = [s.text for s in soup.find_all(id=re.compile('main_Tema1_RP_Versiones_lbl_RitmoDuracion_\d+'))]
    canta =          [s.text for s in soup.find_all(id=re.compile('main_Tema1_RP_Versiones_lbl_Canta_\d+'))]
    formacion =      [s.text for s in soup.find_all(id=re.compile('main_Tema1_RP_Versiones_lbl_Formacion_\d+'))]
    interprete =     [s.text for s in soup.find_all(id=re.compile('main_Tema1_RP_Versiones_lbl_Interprete_\d+'))]
    grabacion =      [s.text for s in soup.find_all(id=re.compile('main_Tema1_RP_Versiones_lbl_DetallesGrabacion_\d+'))]

    df = pd.DataFrame({'Genre': ritmoduraction, 'Vocalist':canta, 'Formation': formacion, 'Instrumentalist': interprete, 'Recording':grabacion})

    df['Title'] = titulo
    df['Ritmo'] = ritmo
    df['Year'] = ano
    df['Music'] = creadores_musica
    df['Lyrics'] = creadores_letra

    print('----')
    print(df)

    return df


df_todo = pd.concat([get_df(t) for t in temas], ignore_index=True)

df_todo.to_csv("todotango.csv")