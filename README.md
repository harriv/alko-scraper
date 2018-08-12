# Alko Scraper
This is a scraper for the alko website. It downloads and parses the .xls file into csv from the alko website. After that, it uses the id:s found in the .xls to scrape the store availability from the website. You can select scraping parameters in the config file. This project can be used with my [Alko App](https://github.com/olahepelto/alko-app) project.

## Requirements
```bash
pip install xlrd
```
## Features
* Produces .csv files for availability and products
* Config file
* Easy cronjob creation

## Planned features
* All data => PostgreSQL

## Images
![alt text](https://raw.githubusercontent.com/olahepelto/alko-scraper/master/images/Screenshot1.png "Screenshot 1")
![alt text](https://raw.githubusercontent.com/olahepelto/alko-scraper/master/images/Screenshot2.png "Screenshot 2")
