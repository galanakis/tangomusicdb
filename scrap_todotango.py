import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
import os
import html2text
import difflib
import mutagen
import urllib3
from mutagen.id3 import ID3, ID3NoHeaderError
from mutagen.easyid3 import EasyID3
from pathlib import Path
import wget

cache_dirname = os.path.join('todotango', 'cache')
output_dirname = os.path.join('todotango')
mp3_dirname = os.path.join("todotango", "audio", "mp3")

url_obras_todas = 'https://www.todotango.com/musica/obras/todas/-/0/0/'
url_obras_musica = 'https://www.todotango.com/musica/obras/musica/-/0/0/'
url_audio_mp3 = 'http://audio.todotango.com/mp3/'
url_audio_ogg = 'http://audio.todotango.com/ogg/'


# wget -r -nH  -A mp3 http://audio.todotango.com/mp3/ -P todotango/audio
def get_audio_links():

    page_text = urllib.request.urlopen(url_audio_mp3).read()
    soup = BeautifulSoup(page_text)

    # Find all links and filter the ones who end in .mp3
    audio_links = [a.text for a in soup.find_all('a', href=True) if re.match('.*\.mp3',a.text)]

    return audio_links


def download_audio_files():

    audio_links = get_audio_links()

    os.makedirs(mp3_dirname, exist_ok=True)

    for link in audio_links:
        source = url_audio_mp3 + '/' + link
        destination = os.path.join(mp3_dirname, link)
        print('Downloading ', source, ' to ', destination)
        wget.download(source, destination)


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


# This is a decorator. It prints the input arguments
# and the output of a function.
def print_io_decorator(func):
    def wrapper_print_io(*args, **kwargs):
        print(">>>>>")
        print(*args, **kwargs)
        print("<<<<<")
        output = func(*args, **kwargs)
        print(output)
        return output
    return wrapper_print_io


# This identifies the audio file information which is hidden inside
# javascript code instead of html. This makes it a bit clumsy,
# cause it relies on regular expression to extract the fields.
# On the other hand all data are inside a javascript dictionary,
# which is relatively straightforward to parse.
def parse_playlist_entry(playlist_entry):

    def search(field):
        match = re.search('.*'+field+':"([^"]+)".*', playlist_entry)
        return html2text.html2text(match.group(1) if match is not None else '').strip()

    fileid = search('id')
    titulo = search('titulo')
    canta = search('canta')
    detalles = search('detalles')
    duracion = search('duracion')
    formacion = search('formacion')

    # There are occasional tripple quotes in the duration.
    # With this I drop them and change the format of the time
    duracion = ":".join(filter(None, re.split('[^\d]', duracion)))   

    audio_data = {
        "Title": titulo,
        "Instrumentalist": formacion,
        "Vocalist": canta,
        "Recording Info": detalles,
        "Duration": duracion,
        "File ID": fileid,
    }

    return audio_data


# If it finds a playlist it will return it as a data frame
# if not it will return an empty data frame.
def maybe_get_playlist(page_text):

    # The audio information are hidden in a bit of javascript code
    # which I pick looking for the audio url.
    re_playlist = re.compile('({[^{]*https://audio.todotango.com[^}]*})')
    # This contains all elements in the playlist, as string
    # containing a js dictionary
    playlist_js_code = re.findall(re_playlist, page_text)

    playlist = map(parse_playlist_entry, playlist_js_code)

    return playlist


# It parses the versiones table and returns a data frame.
def parse_versions(soup_versions):

    # Fields corresponding to each musical composition (theme)
    # - Title
    # - Rhythm (tango, miloga, etc). This is basically the genre.
    # - Year, Composers (music and lyrics)
    # - Composer of music (can be multiple of them)
    # - Composer of lyrics (can be multiple of them)
    theme_keys = {
        'Title': 'main_Tema1_lbl_Titulo',
        'Rhythm': 'main_Tema1_lbl_Ritmo',
        'Year of Composition': 'main_Tema1_lbl_Ano'
    }

    # Fields corresponding to the comporers of the theme.
    # Can by multiple of them.
    # - Music composers
    # - Lyrics composers
    composer_regex_keys = {
        'Music Composer': 'main_Tema1_Tema_Autores1_RP_TemasCreadores_AutoresMusica_hl_Creador_\d+',
        'Lyrics Composer': 'main_Tema1_Tema_Autores1_RP_TemasCreadores_AutoresLetra_hl_Creador_\d+'
    }

    # Fields corresponding to each version(performance) of this theme.
    # There can be multple than one performance.
    # - Genre (Rhythm)
    # - Vocalist
    # - Type of musical ensemble (orquestra, guitars, etc),
    # - Instrumentalist
    # - Recording information (data, location and label)
    versions_regex_keys = {
        'Genre': 'main_Tema1_RP_Versiones_lbl_RitmoDuracion_\d+',
        'Vocalist': 'main_Tema1_RP_Versiones_lbl_Canta_\d+',
        'Ensemble': 'main_Tema1_RP_Versiones_lbl_Formacion_\d+',
        'Instrumentalist': 'main_Tema1_RP_Versiones_lbl_Interprete_\d+',
        'Recording Info': 'main_Tema1_RP_Versiones_lbl_DetallesGrabacion_\d+'
    }

    # Returns one instance of this id as text.
    # If the id does not exit it returns an empty string.
    def find_text_byid(id_label):
        search_result = soup_versions.find(id=id_label)
        return search_result.text.strip() if search_result is not None else ''

    def find_all_text_byid_regex(id_regex):
        return [s.text.strip() for s in soup_versions.find_all(id=re.compile(id_regex))]

    # Dictionary of fields with theme data.
    d_theme = {k: find_text_byid(v) for k, v in theme_keys.items()}

    # Comma separated list of music and lyrics creators
    d_composer = {k: ", ".join(find_all_text_byid_regex(v)) for k, v in composer_regex_keys.items()}

    # For each field a list corresponding to different compositions.
    d_versions = {k: find_all_text_byid_regex(v) for k, v in versions_regex_keys.items()}
    # I can also do this in edits, but it is very consistent so I can do it here.
    # The singer names are always prefixed by "Canta", "Canta Carlos Gardel", "Canta Instrumental".
    # Here I drop this prefix.
    d_versions["Vocalist"] = [voc.replace("Canta ", "") for voc in d_versions["Vocalist"]]

    # From a dict of lists, to a list of dicts. Each dictionary contains
    # all information about each version. {**x, **y, **z} merges dictionaries
    # in (python >=3.5).
    versions = [{**d_theme, **d_composer, **dict(zip(d_versions, col))} for col in zip(*d_versions.values())]

    # This is a maybe empty list of dicts
    return versions


# If it finds the "versiones" table it will return the data
# as a list with one dataframe.
# If not, it will return an empty list.
# I am implementing the Maybe pattern using a list which may
# or may not be empty.
def maybe_get_versions(page_text):

    soup = BeautifulSoup(page_text, features="lxml")

    # A list of performances is found in a div with id "versiones".
    soup_versions = soup.find(id='versiones')

    # If element with id=versiones is found, it returns a list
    # otherwise it returns an empty list.
    return parse_versions(soup) if soup_versions else []


# It combines data found under versiones and under playlist
# in one big dataframe.
# This is done by creating a new index column "ID" combining
# text from instrumentalists, vocalists and recording info,
# which hopefully uniquely identifies the track.
# Then it matches by edit distance the indices of the two
# data frames (versions and playlist) and combines them
# into one by inserting the extra data of the playlist into
# the data of versiones.
def merge_versiones_playlist(df_ver, df_plist):

    # We construct a unique ID which defines the individual performance.
    df_ver["ID"] = df_ver["Ensemble"]+df_ver["Instrumentalist"] + df_ver["Vocalist"] + df_ver["Recording Info"]

    # We set this as the unique identifier of this performance.
    df_ver = df_ver.set_index("ID")

    # For the playlist data, we construct a similar unique ID, but we replace
    # its values with the closest (by edit distance) values from df["ID"].
    # This means that df and df_ps end up with the same index values. Only
    # df_ps has less columns.
    search_keys = df_plist["Instrumentalist"] + df_plist["Vocalist"] + df_plist["Recording Info"]
    df_plist["ID"] = search_keys.apply(lambda x: difflib.get_close_matches(x, df_ver.index)[0]) 
    df_plist = df_plist.set_index("ID")

    # We continue by merging the values of the two data frames.
    # pandas will only merge columns that correspond to the the rows
    # of the same index. Magic.
    df_ver[["Duration", "File ID"]] = df_plist[["Duration", "File ID"]]

    return df_ver


# Parses theme pages and returns a dataframe.
def parse_theme_page(page_text):

    # The versions table as a data frame, or an empty data frame
    df = pd.DataFrame(maybe_get_versions(page_text))

    if not df.empty:

        # The playlist as a data frame or an empty data frame
        df_plist = pd.DataFrame(maybe_get_playlist(page_text))

        if not df_plist.empty:
            df = merge_versiones_playlist(df, df_plist)

        df_print = df[['Title', 'Ensemble', 'Instrumentalist', 'Vocalist', 'Genre', 'Recording Info']].copy()
        df_print['Instrumentalist'] = df_print['Ensemble'] + df_print['Instrumentalist']
        #df_print['Title'] = df_print['Title'][df_print['Title'].notnull()].map(lambda s: '{: <20}'.format(s))
        #df_print['Instrumentalist'] = df_print['Instrumentalist'][df_print['Instrumentalist'].notnull()].map(lambda s: '{: <25}'.format(s))
        #df_print['Genre'] = df_print['Genre'][df_print['Genre'].notnull()].map(lambda s: '{: <15}'.format(s))
        #df_print['Vocalist'] = df_print['Vocalist'][df_print['Vocalist'].notnull()].map(lambda s: '{: <25}'.format(s))
        #df_print['Recording Info'] = df_print['Recording Info'][df_print['Recording Info'].notnull()].map(lambda s: '{: <30}'.format(s))

        #string = df_print[['Title', 'Ensemble', 'Instrumentalist', 'Vocalist', 'Genre', 'Recording Info']].to_string(header=False, index=False)

        print(df_print.to_string(header=False, index=False))

    return df


def get_theme_links(index_url):

    # Example link in the list:
    # 'https://www.todotango.com/musica/tema/2601/Bahia-Blanca/'
    # The music is as a file 2601

    page_text = requests_cache(index_url)

    soup = BeautifulSoup(page_text, features="lxml")

    # The link of each theme is in a div item of class "itemlista"
    links = [listitem.a.get('href') for listitem in soup.find_all('div', {"class": "itemlista"})]

    return links


# Wrapper, such that I can set the output directory
def to_csv(df, fname, **kwargs):

    os.makedirs(output_dirname, exist_ok=True)
    fname = os.path.join(output_dirname, fname)
    df.to_csv(fname, **kwargs)


# Reads a csv file with all columns being strings.
def read_csv(file_path):
    return pd.read_csv(file_path, index_col=0, dtype=str)


def analyze_all(links):

    # Generate a list of data frames, one for each theme
    df_list = [parse_theme_page(requests_cache(url)) for url in links]

    # Merge all data frames into one
    df_todotango = pd.concat(filter(lambda df_list: not df_list.empty, df_list), ignore_index=True)

    to_csv(df_todotango, 'todotango_raw.csv')

    df_edited = edit_data(df_todotango)

    csv_cols = [
        "Title",
        "Instrumentalist",
        "Vocalist",
        "Date",
        "Location",
        "Genre",
        "Music Composer",
        "Lyrics Composer",
        "Year of Composition",
        "Recording Info",
        "File ID"
    ]

    to_csv(df_edited, "todotango.csv", columns=csv_cols)

    ind = df_edited["Date"].fillna("").apply(lambda x: len(x)>4)

    to_csv(df_edited[ind], 'todotango_fulldate.csv', columns = csv_cols)


# Heuristically generate a list of unique vocalists
# Ideally this should be loaded from a file.
# I noticed some vacant entries. The input is the list of
# singer entries (which are not separated by comma).
def get_unique_vocalists(mixed_vocalists):

    # Singer's names can have up to 3 words. There are few
    # with 1 and some with 3 but most have 2.
    vocalists = set(filter(lambda x: len(x.split()) <= 3, mixed_vocalists))

    # All entries with up to 3 words are probably single people
    # There are a few entries that have one word (Charlo, Gaby),
    # but those do not seem to have any duos with any one else.
    # So a duo would be at least 4 words.
    solos = set(filter(lambda x: len(x.split()) <= 3, mixed_vocalists))

    # All entries with more than 3 words are probably duos
    # but can also be people with really long names, like
    # Juan Carlos Marabrio Catán, who has two numbers and
    # two surnames!
    duos = set(filter(lambda x: len(x.split()) > 3, mixed_vocalists))

    # There are some invalid names
    duos.discard('Varios autores Varios autores')

    # Here I try to split duos using names I found in solos
    # Only assmution is that there are not duos involving
    # people with one word names.
    for pair in duos:
        for name in solos:
            if name in pair and len(pair.split())-len(name.split()) > 1:
                vocalists.add(name)
                pair = pair.replace(name, '').strip()
        if pair != '':
            vocalists.add(pair)

    # In what is left there are still some people who only appear
    # in duos. I take special care.
    vocalists.discard('Daniel Melingo Fabiana Cantilo')
    vocalists.add('Daniel Melingo')
    vocalists.add('Fabiana Cantilo')
    vocalists.discard('Omar Quirós Oscar Galán')
    vocalists.add('Omar Quirós')
    vocalists.add('Oscar Galán')
    vocalists.discard('Carlos Soler Luis Román')
    vocalists.add('Carlos Soler')
    vocalists.add('Luis Román')
    vocalists.discard('René Ruiz Alberto Acuña')
    vocalists.add('René Ruiz')
    vocalists.add('Alberto Acuña')

    return vocalists


# This is the list of locations appearing in recording information
def get_locations():
    locations = [
        "Alemania",
        "Amsterdam",
        "BUENOS AIRES",
        "Bahía Blanca",
        "Barcelona",
        "Bariloche",
        "Berlin",
        "Berlín",
        "Bernal",
        "Bilbao",
        "Bogotá",
        "Brasil",
        "Buenos Aires",
        "Camden \(USA\)",
        "Caracas",
        "Carreras \(Santa Fe\)",
        "Chile",
        "Ciudadela \(Prov. de Bs. As.\)",
        "Colombia",
        "Cuba",
        "Córdoba",
        "Dinamarca",
        "Ecuador",
        "España",
        "Estados Unidos",
        "Francia",
        "Frankfurt",
        "Granada",
        "Italia",
        "Japón",
        "La Habana",
        "La Plata",
        "Madrid",
        "Malmö \(Suecia\)",
        "Medellín",
        "Mendoza",
        "Milan",
        "Milán",
        "Montevideo",
        "México",
        "New York",
        "Nueva York",
        "Paris",
        "París",
        "Perú",
        "Piacenza \(Italia\)",
        "Piacenza",
        "Polonia",
        "Pontevedra",
        "Poços de Caldas",
        "Rosario",
        "Tokio",
        "Tokyo",
        "Viena",
        "Villa Mercedes Calle Angosta",
        "Zaragoza",
        "\"Hollywood, USA Forever Tango\"",
        "\"Long Island, NY\"",
    ]

    loc_spelling_corrections = {
       "BUENOS AIRES": 'Buenos Aires',
       "Berlin": "Berlín",
       "New York": "Nueva York",
       "Paris": "París",
       "Tokyo": 'Tokio',
       "\"Hollywood, USA Forever Tango\"": 'Hollywood, USA Forever Tango',
       "\"Long Island, NY\"": "Long Island, NY"
    }

    return locations, loc_spelling_corrections


def correct(string, corrections):

    for k, v in corrections.items():
        string = re.sub(k, v, string)

    return string


instrumentalist_corrections = {
    "Trio": "Trío",
    "Bandoneon": "Bandoneón",
    "bandoneon": "bandoneón",
    "Quiteto": "Quinteto",
    "\"": "",
    "^\W+": "",
    "\W+$": "",
    "^Con ": "",
    "de:": "de",
    "dir. Por": "dir:",
    "\W+[dD][iI][rR]\W+": " -dir: ",
    "Conjunto -dir:": "Conjunto",
    "Trío -dir:": "Trío",
    "Cuartetango -dir:": "Cuartetango",
    "Guitarras -dir:": "Guitarras",
    "Orquesta -dir:": "Orquesta",
    "dirigid[ao] por:": "-dir:",
    "Dúo Dúo": "Dúo",
    "Conjunto Conjunto": "Conjunto",
    "Trío Trío": "Trío",
    "Cuarteto Cuarteto": "Cuarteto",
    "Orquesta Orquesta": "Orquesta",
    "Cuarteto Típico Cuarteto Típico ": "",
    "Orquesta Típica Porteña Raúl Garello": "Orquesta Típica Porteña -dir: Raúl Garello",
    "Bandoneón (?!de)": "Bandoneón de ",
    "Guitarra (?!de)" : "Guitarra de ",
    "Guitarras (?!de)" : "Guitarras de ",
    "Orquesta de cuerdas José Canet": "Orquesta de cuerdas de José Canet",
    "Piano:": "Piano de",
    "Orq\. ": "Orquesta ",
    "^guitarra": "Guitarra",
    "^orquesta": "Orquesta",
    "Conjunto -dir:": "Conjunto",
    "Orquesta -dir:": "Orquesta"

}


def corrections_regex(string):

    for original, replacement in instrumentalist_corrections.items():
        string = re.sub(original, replacement, string)

    return string


# Here I apply my own bias by reordering and restructuring the data
def edit_data(df_orig):

    df = df_orig.copy()

    # List of all locations appearing in Recording Info.
    locations,  loc_spelling_corrections = get_locations()

    # The Recording Info column contains the date, location and recording label
    # but any of them can be missing. The date format used is Day-Month-Year.
    # I separete the date string from the rest, and then reverse it to get
    # the ISO8601 date format.
    re_date = r'(\d{0,2}-?\d{0,2}-?\d\d\d\d)'
    re_loc = '('+'|'.join(locations)+')'
    re_info = '(.*)'
    re_dli = ' *'.join([re_date, re_loc, re_info])

    df[['Date', 'Location', 'Recording Info']] = df['Recording Info'].str.extract(re_dli)

    # Converting date to ISO8601 format: YYYY-MM-DD
    ind = df['Date'].notnull()

    def date_sanitizer(date_string):
        re_split_date = '(\d{0,2})-?(\d{0,2})-?(\d\d\d\d)'
        day, month, year = re.findall(re_split_date, date_string)[0]
        output = "-".join(list(map(lambda x: "%02d" % int(x), filter(None, list([year, month, day])))))
        if (output == '1900-01-01'):
            output = None
        return output

    df['Date'] = df['Date'][ind].apply(date_sanitizer)

    # Spell correct locations
    df["Location"][df["Location"].notnull()].apply(lambda x: correct(x,loc_spelling_corrections))    

    # Get the list of known vocalists, somehow.
    mixed_vocalists = set(df["Vocalist"])
    vocalists = get_unique_vocalists(mixed_vocalists)

    # Build a massive regular expressions for the vocalists
    re_vocalists = re.compile('('+"|".join(vocalists)+')')

    # This comma separates the identified vocalists
    ind = df["Vocalist"].notnull()
    df["Vocalist"] = df["Vocalist"].apply(lambda x: ", ".join(re.findall(re_vocalists, x)))

    # The ensemble is usually the word "orquesta". Sometimes it is
    # "Guitaras de Barbieri y Ricardo", instead of putting Barbieri y Ricardo
    # under instrumentalist. Here I merge the two, since the separation is not
    # always consistent.
    df['Instrumentalist'] = (df['Ensemble']+' '+df['Instrumentalist']).str.strip()

    ind = df["Instrumentalist"].notnull()
    df['Instrumentalist'] = df['Instrumentalist'][ind].apply(lambda x: corrections_regex(x))

    df = df.drop_duplicates()

    return df


def label_mp3_files(df):

    ind = df["File ID"].notnull()
    df_files = df[ind].copy()
    df_files["File ID"] = df_files["File ID"].apply(lambda x: str(int(float(x))))
    df_files = df_files.set_index('File ID')

    # I need to fix this. Why would there be duplicate entries??
    # Ah ok, there are duplicate entries under versiones! For example
    # Look at Viviani of Di Sarli.
    df_files = df_files.drop_duplicates()

    # Breaking up the date in day, month and year.
    re_date = r'(\d\d\d\d)-?(\d{0,2})-?(\d{0,2})'
    df_files[["Year", "Month", "Day"]] = df_files["Date"].str.extract(re.compile(re_date))

    # The original data and also the regular expression extraction might result
    # in NaN which can cause issues with string manipulations.
    # Here we replaces all NaNs with empty strings.
    df_files = df_files.fillna("")

    # List of files without a numeric ID in their name.
    attribute_errors = []

    # List of files, present in disk, but without associated data
    key_errors = []

    for filename in Path(mp3_dirname).rglob('*.mp3'):
        try:
            fileid = re.match('(\d+)', os.path.basename(filename)).group(1)
            print(filename)
            row = df_files.loc[fileid]
            title = "".join(filter(None, ['%-12s' % row["Date"], row["Title"]]))
            artist = " / ".join(filter(None, [row["Instrumentalist"], row["Vocalist"]]))
            year = row["Year"]
            genre = row["Genre"]
            print(filename, title, artist, year, genre) 

            # Some files don't have ID3 tags!
            try:
                tags = ID3(filename)
            except ID3NoHeaderError:
                ID3().save(filename)

            audiofile = EasyID3(filename)
            audiofile["title"] = title
            audiofile["artist"] = artist
            audiofile["date"] = row["Year"]
            audiofile["genre"] = genre
            audiofile.save()

        # Files without a numeric id in their name
        except AttributeError:
            attribute_errors.append(filename)
        # Files in disk but without associated data
        except KeyError:
            key_errors.append(filename)

    print("-----------")
    print("The following files do not have a numeric id in their name")
    print("  ", ", ".join(map(str,attribute_errors)))
    print()
    print("The following files are in disk but there is no data for them")
    print("  ", ", ".join(map(str,key_errors)))



if __name__ == "__main__":

    links = get_theme_links(url_obras_todas)

    # This can be slow as it reads all page source.
    df_todotango = analyze_all(links)

    df_todotango.to_csv("todotango/todotango_raw.csv", ignore_index=True)

    df_edited = edit_data(df_todotango)

    # Custom editing!
    df_edited = edit_data(df_todotango)

    # Which columns to save and in what order
    csv_cols = [
        "Title",
        "Instrumentalist",
        "Vocalist",
        "Date",
        "Location",
        "Genre",
        "Music Composer",
        "Lyrics Composer",
        "Year of Composition",
        "Recording Info",
        "File ID"
    ]

    df_edited.to_csv("todotango/todotango.csv", columns=csv_cols)

    download_audio_files()

    label_mp3_files(df_edited)


