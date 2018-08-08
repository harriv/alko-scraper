#!/usr/bin/python
# -*- coding: utf-8 -*-

import psycopg2
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
    product_id_list = []

    def __init__(self):
        log("Starting Scraper")

        self.conn = psycopg2.connect(
            host=self.configManager.get_value("Database", "Host"),
            database=self.configManager.get_value("Database", "Database"), 
            user=self.configManager.get_value("Database", "Username"), 
            password=self.configManager.get_value("Database", "Password"))
        self.dropTable(self.conn)

        self.store_list = self.fetch_alkos()
        self.productScraper = ProductScraper(self.conn, self.configManager, self.product_id_list)
        self.availabilityScraper = AvailabilityScraper(self.conn, self.configManager, self.store_list, self.product_id_list)
        self.CLEAN_FILES()

    def dropTable(self, conn):
        cursor = conn.cursor()
        cursor.execute("DROP TABLE IF EXISTS products")
        cursor.execute("CREATE TABLE products (Numero varchar(255), Nimi varchar(255), Pullokoko decimal, Hinta decimal, Litrahinta decimal, Tyyppi varchar(255), Luonnehdinta varchar(255), Pakkaustyyppi varchar(255), ProsAlkohol decimal, EurPerLAlkohol decimal);")
        
        cursor.execute("DROP TABLE IF EXISTS availability")
        cursor.execute("CREATE TABLE availability (Availability varchar(1000));")

        cursor.execute("DROP TABLE IF EXISTS stores")
        cursor.execute("CREATE TABLE stores (Store varchar(1000));")

        conn.commit()
        log("Dropped and created psql table.")

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
        
        cursor = self.conn.cursor()

        stores = []
        for store_data in store_data_arr["stores"]:
            if(store_data["outletTypeId"] != "outletType_tilauspalvelupisteet"):
                stores.append(store_data["name"])
                sql = """INSERT INTO stores(Store) VALUES('{0}');""".format(store_data["name"])
                cursor.execute(sql)

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
