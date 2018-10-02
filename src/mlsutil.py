import numpy as np
import pandas as pd
import requests
from bs4 import BeautifulSoup

class TeamStatsConfig():
    name = 'team-stats'
    raw_path_template = '../raw/team-{}-reg.html'
    data_path_template = '../data/team-stats-{}.csv'
    url_template = 'https://www.mlssoccer.com/stats/team?year={}&season_type=REG'
    table_index = 'Club'

    @staticmethod
    def fixup(table):
        pass


# TODO: This isn't going to work for the results page as it loads the results
# dynamically
class TeamResultsConfig():
    name = 'team-results'
    raw_path_template = '../raw/team-results-{}.html'
    data_path_template = '../data/team-results-{}.csv'
    url_template = 'https://www.mlssoccer.com/results/{}'
    table_index = 'Club'

    @staticmethod
    def fixup(table):
        pass


class TeamStandingsConfig():
    name = 'team-standings-ss'
    raw_path_template = '../raw/team-standings-ss-{}.html'
    data_path_template = '../data/team-standings-ss-{}.csv'
    url_template = 'https://www.mlssoccer.com/standings/supporters-shield/{}/'
    table_index = '#'

    @staticmethod
    def fixup(table):
        '''
        Fixup the standings table so that it can be converted using our generic table converter
        '''
        # remove the first row, it is a secondary level header row
        table.tr.extract()

        # convert the first row in the table to hold th rather than td elements
        for tag in table.tr.find_all('td'):
            tag.name = 'th'

        # the Club column includes spans for mobile which erratically abreviate the team name
        # so clear those spans
        for span in table.select('.show-on-mobile-inline'):
            span.clear()


class Statistics():
    def __init__(self, config):
        self.config = config

    def source_url(self, year):
        return self.config.url_template.format(year)

    def raw_path(self, year):
        return self.config.raw_path_template.format(year)

    def data_path(self, year):
        return self.config.data_path_template.format(year)

    def fixup_table(self, table):
        return self.config.fixup(table)

    def download_raw_for(self, year):
        '''
        Download html statistic for `year` from mlssoccer.com.
        '''
        file_path = self.raw_path(year)
        url = self.source_url(year)
        r = requests.get(url)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(r.text)

    def convert_raw_to_csv_for(self, year):
        '''
        Convert the raw html data into a csv for later statistical fun.
        '''
        html_file_path = self.raw_path(year)
        # open up the html file and get a reference to any tables
        with open(html_file_path) as f:
            soup = BeautifulSoup(f, 'lxml')

        table_elements = soup.find_all('table')

        # just assume there is only one
        table_element = table_elements[0]

        # adjust the table before conversion
        self.fixup_table(table_element)

        # import the data into a DataFrame
        df = table_to_dataframe(table_element)

        # reset the index to be the specified index column
        df.set_index(self.config.table_index, drop = True, inplace = True)
        df.to_csv(self.data_path(year))


# TODO: Pandas supports directly loading from html. Should experiment with
# that rather than manually grabbing the data. pd.read_html()
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