#!/usr/bin/python
# -*- coding: utf-8 -*-

import time
import requests
import shutil
import xlrd
import csv
import os
import threading
from configparser import ConfigParser
from util import fixEncodingFile, log
from bs4 import BeautifulSoup as soup

class AvailabilityScraper():

    def __init__(self, connection, configManager, store_list, product_id_list, session):
        self.connection = connection
        self.configManager = configManager
        self.store_list = store_list
        self.product_id_list = product_id_list

        self.session = session
        self.GENERATE_AVAILABILITY_DATA()

    def GENERATE_AVAILABILITY_DATA(self):
        log("Generating availability data.")

        if not os.path.exists("result"):
            os.makedirs("result")
        else:
            shutil.rmtree("result")
            os.makedirs("result")

        i = 0
        while (i < len(self.product_id_list)):
            create_amount = int(self.configManager.get_value("AlkoAvailabilityScraper", "ThreadAmount"))
            if (len(self.product_id_list) < i + create_amount):
                create_amount = len(self.product_id_list) - i
            log("Rows Left: " + str(len(self.product_id_list) - i) + " Creating Threads: " + str(create_amount) + " Done: " + str(i))

            thread_list = []
            for thread_num in range(0, create_amount):
                thread_list.append(threading.Thread(target=self.data_to_file_with_product_id, args=(self.product_id_list[i + thread_num],)))

            for thread_num in range(0, create_amount):
                thread_list[thread_num].start()

            for thread_num in range(0, create_amount):
                thread_list[thread_num].join()

            i += create_amount

        self.merge_all_files()

        fixEncodingFile("availability.csv")

        shutil.copy("availability.csv", self.configManager.get_value("OutputFiles", "AvailabilityFile"))
    
    def merge_all_files(self):
        result_file = open("availability.csv", "w")
        
        product_availability_header = time.strftime("%d.%m.%Y  %H:%M:%S") + ","
        for store in self.store_list:
            product_availability_header += store.replace("Alko ", "") + ","

        result_file.write(product_availability_header + "\n")

        for filename in os.listdir('result'):
            file_contents = open("result/" + filename).read()
            result_file.write(filename.split(".")[0] + ";" + file_contents + "\n")

        result_file.close()

        log("Merged all availability part files.")
    
    def data_to_file_with_product_id(self, id):
        my_url = 'https://www.alko.fi/INTERSHOP/web/WFS/Alko-OnlineShop-Site/fi_FI/-/EUR/ViewProduct-Include?SKU=' + str(
            id) + '&amp;AppendStoreList=true&amp;AjaxRequestMarker=true#'
        

        request_success = False
        try_count = 0
        while(not request_success and try_count < 20):
            try_count += 1

            try:
                page_html = self.session.get(my_url).text
                request_success = True
                log("Got availability: " + str(id))
            except:
                log("ERROR: Retrying request Try: " + str(try_count) + " ID: " + str(id))
        

        page_soup = soup(page_html, "html.parser")
        stores_in_stock_soup = page_soup.findAll("span", {"class": "store-in-stock"})

        stores_in_stock = []
        for a in stores_in_stock_soup:
            stores_in_stock.append(a.text)

        csv_line_string = ""
        for store in self.store_list:
            if store in stores_in_stock:
                csv_line_string += "1;"
            else:
                csv_line_string += "0;"

        #cursor = self.connection.cursor()
        #sql = """INSERT INTO availability(Numero, Availability) VALUES('{0}','{1}') RETURNING Numero;""".format("", csv_line_string)

        #cursor.execute(sql)


        filename = "result/" + str(id) + ".json"
        f = open(filename, "w")
        f.write(csv_line_string)
        f.close()
