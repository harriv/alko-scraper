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
from urllib.request import urlopen as uReq


class SuperAlkoScraper():

    global_lock = threading.Lock()

    def __init__(self, configManager, session, ALKO_TYPE):
        self.ALKO_TYPE = ALKO_TYPE
        self.session = session
        self.configManager = configManager
        self.generate_super_alko_product_csv()

    def generate_super_alko_product_csv(self):
        log("Generating " + self.ALKO_TYPE + " data.")

        AMOUNT_SCRAPER_PRODUCTS = int(self.configManager.get_value(
            self.ALKO_TYPE, "ScrapeForwardIdAmount"))
        SCRAPER_START_ID = int(self.configManager.get_value(
            self.ALKO_TYPE, "StartScrapingId"))
        CREATE_THREAD_AMOUNT = int(
            self.configManager.get_value(self.ALKO_TYPE, "ThreadAmount"))

        HEADER = [
            "Numero",
            "Nimi",  # 1
            "Pullokoko",  # 3
            "Hinta",  # 4
            "Litrahinta",  # 5
            "Tyyppi",  # 8
            "Luonnehdinta",  # 17
            "Pakkaustyyppi",  # 18
            "ProsAlkohol",  # 20
            "EurPerLAlkohol"
        ]
        self.write_to_file(";".join(HEADER))

        i = 0
        while (i < AMOUNT_SCRAPER_PRODUCTS):

            if (AMOUNT_SCRAPER_PRODUCTS < i + CREATE_THREAD_AMOUNT):
                CREATE_THREAD_AMOUNT = AMOUNT_SCRAPER_PRODUCTS - i
            log("Rows Left: " + str(AMOUNT_SCRAPER_PRODUCTS - i) +
                " Creating Threads: " + str(CREATE_THREAD_AMOUNT) + " Done: " +
                str(i))

            thread_list = []
            for thread_num in range(0, CREATE_THREAD_AMOUNT):
                thread_list.append(
                    threading.Thread(target=self.data_to_file_with_product_id,
                                     args=((SCRAPER_START_ID + i + thread_num),
                                           )))

            for thread_num in range(0, CREATE_THREAD_AMOUNT):
                thread_list[thread_num].start()

            for thread_num in range(0, CREATE_THREAD_AMOUNT):
                # A 30s timeout in case of thread crashing,
                # thread should normally take <1s
                thread_list[thread_num].join(30)

            i += CREATE_THREAD_AMOUNT

        fixEncodingFile(self.configManager.get_value(
            self.ALKO_TYPE, "FileName"))
        shutil.copy(self.configManager.get_value(self.ALKO_TYPE, "FileName"),
                    self.configManager.get_value(self.ALKO_TYPE, "OutputFile"))

    def data_to_file_with_product_id(self, id):
        request_success = False
        try_count = 0
        while(not request_success and try_count < 20):
            try_count += 1

            try:

                uClient = uReq(self.configManager.get_value(
                    self.ALKO_TYPE, "SuperAlkoUrl") + str(id))

                page_html = uClient.read()
                uClient.close()
                request_success = True
            except:
                log("ERROR: Retrying request Try: " +
                    str(try_count) + " ID: " + str(id))

        try:
            print(id)
            page_soup = soup(page_html, "html.parser")
            product_data = page_soup.findAll(
                "td", {"class": "kast"})
        except:
            log("ERROR: skipped a product, weird text encoding.")
            return

        newList = []
        finalList = []
        try:
            for a in product_data:
                newList.append(self.remove_tags(str(a)))

            for a in newList:
                if("Product Code" in a or "Product type" in a or
                   "Specification" in a or "Product type" in a or
                   "In the Drawer" in a):
                    newList.remove(a)

            if(newList[0] != '' and not len(newList) == 8 and
               "Tobacco" not in newList[1]):

                finalList = [newList[0]]

                first_two_euro_values = []
                for a in newList:
                    if("€" in a):
                        first_two_euro_values.append(a.replace("€", "")
                                                     .replace("/L", "")
                                                     .replace(".", ",")
                                                     .strip()
                                                     )

                finalList.append("-")
                finalList.append(first_two_euro_values[0])
                finalList.append(first_two_euro_values[1])
                finalList.append("-")
                finalList.append("-")
                finalList.append("-")

                for a in finalList[0].split(" "):
                    if("%" in a):
                        pros_alcohol = a.replace("%", "").strip()
                        finalList.append(a.replace("%", "").strip())

                finalList.append(str(
                    (float(first_two_euro_values[1].replace(",", "."))*100) /
                    float(pros_alcohol.replace(",", "."))
                ).replace(".", ","))

                csv_line_string = str(id)
                for store in finalList:
                    csv_line_string += ";" + store
                self.write_to_file(csv_line_string)
        except:
            log("ERROR: Failed to process webpage, nothing added to csv!")

    def remove_tags(self, text):
        return ''.join(xml.fromstring(text).itertext())

    def write_to_file(self, string):
        self.global_lock.acquire()

        try:
            with open(self.configManager.get_value(self.ALKO_TYPE, "FileName"),
                      "a+") as file:
                file.write(str(string))
                file.write("\n")
                file.close()
        except:
            log("Error writing to file!")

        self.global_lock.release()
