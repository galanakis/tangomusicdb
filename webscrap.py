import pandas as pd


# For each url supplied as argument, read the html page, parsing
# it for a table. Then select the table at the input index (default=0)
# and concatenate all dataframes.
# It assumes (but does not check), that all tables in all pages
# have the same structure.
# Input: a list of strings representing urls
# Output: a single dataframe, containing the concatenated tables.
def cat_tables_dataframe(*urls, table_index=0):
    return pd.concat([pd.read_html(url)[table_index] for url in urls], ignore_index=True)


# It performs transformations on the input df and returns the result.
def digest_performance_data(df_input):
    # Make a copy to modify.
    df = df_input.copy()
    # Row Filtering
    #
    # Here we include fildering criteria to drop some of the rows
    #
    # - Exclude entries where the date is a date range, cause they do not
    #   correspond to a single track. Those are identified by '--' (for
    #   example 1938--1952). The na=False defines the result for missing
    #   (empty) dates.
    ind_valid_date = ~df['Perf. date'].str.contains('--', na=False)
    #
    # - Exclude entries whith an empty or invalid title (one without any
    #   alphanumerics).
    ind_title_has_alpha = df['Title'].str.contains('\w+', regex=True, na=False)

    ind = ind_valid_date & ind_title_has_alpha
    # Overwrite the original dataframe
    df = df[ind]

    # Column Transformations
    #
    # Here we do transformations on columns and insert calculated columns.
    #
    # - From the date field we extract the year using regex matching.
    #   For each regex group we get one dataframe column. Since the
    #   date format is YYYY-MM-DD or YYYY or NaN (missing), we match with
    #   (\d\d\d\d)-(\d\d)-(\d\d). The first group will always by the year
    #   and the rest the month and day, or NaN if they don't exist.
    df[['Year', 'Mo', 'Da']] = df['Perf. date'].str.extract(r'(\d\d\d\d)-(\d\d)-(\d\d)')

    return df


# Reads the performance data from html, processes them and saves predetermined
# columns to csv.
def scrap_perf_data(*urls, filename, columns=['Title', 'Vocalist(s)', 'Instrumentalist(s)', 'Year', 'Mo', 'Da', 'Genre']):
    df_orig = cat_tables_dataframe(*urls)
    df = digest_performance_data(df_orig)
    df.to_csv(filename, columns=columns)

# Juan D' Arienzo performances in tango.info
# Contains a table with columns
# 'Title, TIWC, Genre, Instrumentalist(s), Vocalist(s), Lang., Perf. date, Dura., Track qty, info'
# url_darienzo = 'https://tango.info/performance/JuanaDarie'
# csv_darienzo = "darienzo_tango_info.csv"
# scrap_perf_data(url_darienzo, filename=csv_darienzo)

# Tango.info performance urls.
# The link 'https://tango.info/performance' returns a filtered list of performances
# (only the ones with more than 8 tracks). This may be sufficient, but we could
# also extract them all. The spa(nish) and zxx (instrumental) sublists are unfiltered
# and therefore I use them instead.
#  
# Performaces with vocalists
url_spa = 'https://tango.info/performance/spa'
# Instrumental performances
url_zxx = 'https://tango.info/performance/zxx'
# I hope the table index is the same in both
csv_perf = 'performances_tango_info.csv'

scrap_perf_data(url_spa, url_zxx, filename=csv_perf)
