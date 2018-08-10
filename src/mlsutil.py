import numpy as np
import pandas as pd
import requests
from bs4 import BeautifulSoup

def team_stats_raw_file_path_for(year):
    return '../raw/team-{}-reg.html'.format(year)


def team_stats_datafile_path_for(year):
    return "../data/team-stats-{}.csv".format(year)


def team_stats_download_raw_for(year):
    '''
    Download html team stats for `year` from mlssoccer.com.
    '''
    file_path = team_stats_raw_file_path_for(year)
    url = 'https://www.mlssoccer.com/stats/team?year={}&season_type=REG'.format(year)
    r = requests.get(url)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(r.text)


def team_stats_convert_raw_to_csv_for(year):
    '''
    Convert the raw html data into a csv for later statistical
    fun.
    '''
    html_file_path = team_stats_raw_file_path_for(year)
    # open up the html file and get a reference to any tables
    with open(html_file_path) as f:
        soup = BeautifulSoup(f, 'lxml')

    table_elements = soup.find_all('table')

    # just assume there is only one
    table_element = table_elements[0]

    # import the data into a DataFrame
    df = table_to_dataframe(table_element)

    # reset the index to be the first column
    df.set_index('Club', drop = True, inplace = True)
    df.to_csv(team_stats_datafile_path_for(year))


def table_to_dataframe(table_element):
    '''
    Convert an html table into a pandas DataFrame
    `table_element` is a BeautifulSoup `table` Tag

    Assumptions:
     * number of columns is the same as number of column headers
     * all rows have the same number of data elements
     * the first row contains column headers
    '''
    # figure out the size of the table
    n_rows = 0

    row_tags = table_element.find_all('tr')
    header_row_tags = row_tags[0]
    row_tags = row_tags[1:]

    n_rows = len(row_tags)

    # grab the column names
    column_names = [header_tag.get_text().strip() for header_tag in header_row_tags.find_all('th')]

    # initialize a DataFrame to hold the data
    df = pd.DataFrame(columns=column_names, index=range(n_rows))

    # insert table data into DataFrame
    i_row = 0
    for row_tag in row_tags:
        i_column = 0
        data_tags = row_tag.find_all('td')
        for data_tag in data_tags:
            df.iloc[i_row, i_column] = data_tag.get_text().strip()
            i_column += 1
        i_row += 1

    return df