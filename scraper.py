#!/usr/bin/python
# -*- coding: utf-8 -*-
import codecs
import csv
import datetime
import itertools
import json
import os
import shutil
import threading
import urllib
from urllib.request import urlopen as uReq

import xlrd
from bs4 import BeautifulSoup as soup

from availability_scraper import AvailabilityScraper
from config_manager import ConfigManager
from product_scraper import ProductScraper
from util import fixEncodingFile, log


class Scraper():

    configManager = ConfigManager()
    store_list = []

    def __init__(self):
        log("Starting Scraper")

        self.store_list = self.fetch_alkos()
        self.productScraper = ProductScraper(self.configManager)
        self.availabilityScraper = AvailabilityScraper(self.configManager, self.store_list)
        self.CLEAN_FILES()

    def fetch_alkos(self):
        my_url = 'https://www.alko.fi/myymalat-palvelut'
        uClient = uReq(my_url)
        page_soup = soup(str(uClient.read()), "html.parser")
        uClient.close()

        store_data_arr = json.loads(page_soup.find(type="application/json").get_text()
                            .replace("\\xc3\\xa4","ä")
                            .replace("\\xc3\\xb6","ö")
                            .replace("\\xc3\\xa5","å")
                            .replace("\\xc3\\x84","Ä")
                            .replace("\\xc3\\x96","Ö")
                            .replace("\\xc3\\x85","Å")
                            .replace("\\",""))
        
        stores = []
        for store_data in store_data_arr["stores"]:
            if(store_data["outletTypeId"] != "outletType_tilauspalvelupisteet"):
                stores.append(store_data["name"])

        log("Downloaded alkos to file.")

        return stores

    def CLEAN_FILES(self):
        try:
            shutil.rmtree("result")
            os.remove("alko_products.xls")
            log("Cleaned folder")
        except:
            log("ERROR: Cleaning folders failed")

Scraper()
