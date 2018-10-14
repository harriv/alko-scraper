#!/usr/bin/python
# -*- coding: utf-8 -*-

import time
import shutil
import xlrd
import csv
import os
import threading
from configparser import ConfigParser
from util import fixEncodingFile, log
from bs4 import BeautifulSoup as soup
import xml.etree.ElementTree as xml

class SuperAlkoScraper():
    
    global_lock = threading.Lock()

    def __init__(self):
        self.GENERATE_AVAILABILITY_DATA()

    def GENERATE_AVAILABILITY_DATA(self):
        log("Generating availability data.")
        AMOUNT_SCRAPER_PRODUCTS = 30000
        SCRAPER_START_ID = 21000

        i = 0
        while (i < AMOUNT_SCRAPER_PRODUCTS):
            create_amount = 10
            if (AMOUNT_SCRAPER_PRODUCTS < i + create_amount):
                create_amount = AMOUNT_SCRAPER_PRODUCTS - i
            #log("Rows Left: " + str(AMOUNT_SCRAPER_PRODUCTS - i) + " Creating Threads: " + str(create_amount) + " Done: " + str(i))

            thread_list = []
            for thread_num in range(0, create_amount):
                thread_list.append(threading.Thread(target=self.data_to_file_with_product_id, args=((SCRAPER_START_ID + i + thread_num),)))

            for thread_num in range(0, create_amount):
                thread_list[thread_num].start()

            for thread_num in range(0, create_amount):
                thread_list[thread_num].join()

            i += create_amount

    def data_to_file_with_product_id(self, id):
        request_success = False
        try_count = 0
        while(not request_success and try_count < 20):
            try_count += 1

            try:
                uClient = uReq("https://m.viinarannasta.ee/range-of-products/1/1/" + str(id))
                page_html = uClient.read()
                uClient.close()
                request_success = True
            except:
                log("ERROR: Retrying request Try: " + str(try_count) + " ID: " + str(id))
        

        page_soup = soup(page_html, "html.parser")

        stores_in_stock_soup = page_soup.findAll("td",{"class": "kast"})#, {"class": "store-in-stock"}

        newList = []
        for a in stores_in_stock_soup:
            newList.append(self.remove_tags(str(a)))

        if(newList[0] != '' and not len(newList) == 8):
            newList = [newList[0],newList[7],newList[9]]
            csv_line_string = str(id)
            for store in newList:
                csv_line_string += "," + store
            self.write_to_file(csv_line_string)
        return

        #stores_in_stock = []
        #for a in stores_in_stock_soup:
        #    stores_in_stock.append(a.text)

        filename = "result/" + str(id) + ".json"
        f = open(filename, "w")
        f.write(csv_line_string)
        f.close()

    def remove_tags(self, text):
        return ''.join(xml.fromstring(text).itertext())

    def write_to_file(self, string):
        self.global_lock.acquire()

        with open("super_alko_products.csv", "a+") as file:
            file.write(str(string))
            file.write("\n")
            file.close()

        self.global_lock.release()