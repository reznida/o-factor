import numpy as np
import pandas as pd
from collections import defaultdict

import requests
from bs4 import BeautifulSoup
import re
import os
import time
import csv
import os

if not os.path.exists('data/'):
    os.makedirs('data/')

# Load the PMC database
df = pd.read_csv('PMC-ids.csv')

# Check for articles that have a journal title and create a list of articles from neuro-psych-bio-medical fields
df_temp = df[~df['Journal Title'].isnull()]
j_list = ['brain', 'plos', 'neuro', 'psych', 'behav', 'cogn', 'bio', 'proc natl acad', 'elife',
          'nature', 'science', 'sci rep', 'nat ', 'front ']
df_keep = df_temp[df_temp['Journal Title'].str.lower().str.contains('|'.join(j_list))]

# It is possible to scrape only specific journals, e.g., PLoS Computational Biology,
# note that the journal titles in the PMC database are abbreviated. In that case the df will look like this:
# df_keep = df[df['Journal Title']=='PLoS Comput Biol']

# Limit the year range
df_keep = df_keep[df_keep['Year']>=2006]
df_keep.reset_index(inplace=True, drop=True)

# Load you personal API key
apikey = open('apikey.txt', 'r').read()

# Load keywords and create open-science categories
terms = pd.read_csv('keywords.csv')
categories = terms['category']
categories_unique = np.unique(np.array(categories))

# Saving parameters
N_previous = 0
N_save = 500

db = 'pmc'
base = 'http://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?'
dict_term = defaultdict(list)

for i, row in df_keep.loc[N_previous + 1:].iterrows():
    # Get 1 paper info
    journal_title = row['Journal Title']
    year = row['Year']
    pmcid = row['PMCID']
    # Get full text of 1 paper
    s = '{:s}db={:s}&id={:s}'.format(base, db, pmcid, apikey)
    out = requests.get(s)
    bs = BeautifulSoup(out.content, 'lxml')

    # Check if full text is available; if not - move to the next paper
    full_text_available = not (bs.findAll('sec') == [])
    if full_text_available is True:
        # If so - loop through open-science categories
        dict_term['PMCID'].append(pmcid)
        dict_term['Journal Title'].append(journal_title)
        dict_term['Year'].append(year)
        for categoryInd in categories_unique:
            dict_term[terms['category_description'][terms['category'] == categoryInd].values[0]].append(0)
            found_keyword = False
            # Loop through specific keywords related to each open-science category
            for term in terms['keyword'][terms['category'] == categoryInd]:
                for s in re.finditer(term, out.text, re.IGNORECASE):
                    dict_term[terms['category_description'][terms['category'] == categoryInd].values[0]][-1] = 1
                    found_keyword = True

                # If one keyword is found, stop with searching for this category
                if found_keyword is True:
                    break

    # Save data - each N_save scraped papers
    if (i % N_save == 0) & (i > 0):
        print(i)
        df_save = pd.DataFrame(dict_term)
        df_save.to_csv('data/ofactor_{:d}.csv'.format(i))
        if not (i == N_save):
            os.remove('data/ofactor_{:d}.csv'.format(i - N_save))

# Save the final data
df_save = pd.DataFrame(dict_term)
df_save.to_csv('data/ofactor_{:d}.csv'.format(i))
