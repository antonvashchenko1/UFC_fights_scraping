# Automated Scraping of UFC statistics

This repository contains classes and scripts that can be used to retrieve statistics from individual UFC events, fighters, fights, or all of them together

# Function

First, links to all events, fights and fighters are collected and stored in the folder links. Additional information is collected for the links, which is only available in the respective page hierarchy. Then iterate through the saved links and collect all the information and save it as a csv file in the data folder.

# Usage

- Run the Notebook "get_ufc_stats.ipynb"


# Todo

- The performance should be improved, because one run takes about 1.5 h.
- Clean and transform data to train machine learning models that can predict the outcome of a fight between two fighters 