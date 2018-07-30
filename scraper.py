#!/usr/bin/python
# -*- coding: utf-8 -*-

import csv
import datetime
import os
import shutil
import threading
import json
import urllib
from urllib.request import urlopen as uReq
import itertools
import xlrd
from bs4 import BeautifulSoup as soup
import codecs

def merge_all_files():
    result_file = open("availability.csv", "w")
    
    product_availability_header = "product_number,"
    with open("alko_store_names.txt") as f:
        content = f.readlines()
        for store in content:
            store = store.replace("\n","")
            product_availability_header += store + ","

    result_file.write(product_availability_header + "\n")

    for filename in os.listdir('result'):
        file_contents = open("result/" + filename).read()
        result_file.write(filename.split(".")[0] + "," + file_contents + "\n")

    result_file.close()


def downloadAlkosToFile():
    my_url = 'https://www.alko.fi/myymalat-palvelut'
    uClient = uReq(my_url)
    page_html = str(uClient.read())
    page_soup = soup(page_html, "html.parser")
    uClient.close()

    store_json = page_soup.find(type="application/json").get_text()

    f = open("myymalat-palvelut.json", "w")
    f.write(store_json.replace("\\xc3\\xa4","ä")
                        .replace("\\xc3\\xb6", "ö")
                        .replace("\\xc3\\xa5","å")
                        .replace("\\xc3\\x84","Ä")
                        .replace("\\xc3\\x96","Ö")
                        .replace("\\xc3\\x85","Å")
                        .replace("\\",""))
    f.close()

    with open('myymalat-palvelut.json') as f:
        store_data_arr = json.load(f)
    
    f = open("alko_store_names.txt", "w")
    for store_data in store_data_arr["stores"]:
        if(store_data["outletTypeId"] != "outletType_tilauspalvelupisteet"):
            f.write(store_data["name"])
            f.write("\n")
    f.close()

def data_to_file_with_product_id(id):
    my_url = 'https://www.alko.fi/INTERSHOP/web/WFS/Alko-OnlineShop-Site/fi_FI/-/EUR/ViewProduct-Include?SKU=' + str(
        id) + '&amp;AppendStoreList=true&amp;AjaxRequestMarker=true#'
    uClient = uReq(my_url)
    page_html = uClient.read()
    uClient.close()

    page_soup = soup(page_html, "html.parser")
    stores_in_stock_soup = page_soup.findAll("span", {"class": "store-in-stock"})

    all_alko_stores = []
    with open("alko_store_names.txt") as f:
        content = f.readlines()
        for store in content:
            all_alko_stores.append(store.replace("\n",""))

    stores_in_stock = []
    for a in stores_in_stock_soup:
        stores_in_stock.append(a.text)

    csv_line_string = ""
    for store in all_alko_stores:
        if store in stores_in_stock:
            csv_line_string += "1,"
        else:
            csv_line_string += "0,"

    filename = "result/" + str(id) + ".json"
    f = open(filename, "w")
    f.write(csv_line_string)
    f.close()


def GENERATE_AVAILABILITY_DATA():
    if not os.path.exists("result"):
        os.makedirs("result")
    else:
        shutil.rmtree("result")
        os.makedirs("result")

    # Open ids list
    id_filename = "alko_product_ids.txt"

    # Use this for testing!
    # id_filename = "testing_ids.txt"

    with open(id_filename) as f:
        content = f.readlines()

    # Remove \n and other chars at end of line
    content = [x.strip() for x in content]

    i = 0
    while (i < len(content)):
        create_amount = 50
        if (len(content) < i + 50):
            create_amount = len(content) - i
        print(datetime.datetime.now().strftime('%e.%m.%Y %H:%M:%S') + " -- Rows Left: " + str(
            len(content) - i) + " Creating Threads: " + str(create_amount) + " Done: " + str(i))

        thread_list = []
        for thread_num in range(0, create_amount):
            thread_list.append(threading.Thread(target=data_to_file_with_product_id, args=(content[i + thread_num],)))

        for thread_num in range(0, create_amount):
            thread_list[thread_num].start()

        for thread_num in range(0, create_amount):
            thread_list[thread_num].join()

        i += create_amount

    merge_all_files()

    fixEncodingFile("availability.csv")

    shutil.copy("availability.csv", "../alko-app/assets/availability.csv")
##
# We download and refine the alko price .xls file
##


def process_product_file(file, out):
    xls_workbook = xlrd.open_workbook(file)
    xls_sheet = xls_workbook.sheet_by_name('Alkon Hinnasto Tekstitiedostona')

    csv_file = open(out, 'w')
    product_id_file = open("alko_product_ids.txt", 'w')
    wr = csv.writer(csv_file, quoting=csv.QUOTE_ALL)
    wr.writerow(["Numero",#0
                 "Nimi",#1
                 "Pullokoko",#3
                 "Hinta",#4
                 "Litrahinta",#5
                 "Tyyppi",#8
                 "Luonnehdinta",#17
                 "Pakkaustyyppi",#18
                 "ProsAlkohol",#20
                 "EurPerLAlkohol"])#  Calculate

    for rownum in range(4, xls_sheet.nrows):
        list = xls_sheet.row_values(rownum)
        for i in range(0, len(list)):
            if (not isinstance(list[i], float)):
                list[i] = list[i].replace(u"\u200b", "")
                list[i] = list[i].replace(u"\u02da", "")
                list[i] = list[i].replace(u"\u0142", "")
		
		
        try:
            pullokoko = float(list[3].replace(" l","").replace(",","."))
        except:
            pullokoko = 0.0

        try:
            eurPerLAlko = round(float(list[4])/(pullokoko*(float(list[20])/100)), 2)
        except:
            eurPerLAlko = "0"
	
        list = [list[0], list[1], pullokoko, list[4], list[5], list[8], list[17], list[18], list[20], eurPerLAlko]
        print(list)
        wr.writerow(list)
        product_id_file.write(list[0] + "\n")
    csv_file.close()
    product_id_file.close()
    remove_empty_lines("alko_products.csv")



def remove_empty_lines(filename):
    with open(filename) as in_file, open(filename, 'r+') as out_file:
        out_file.writelines(line for line in in_file if line.strip())
        out_file.truncate()


def GENERATE_PRODUCT_DATA():
    # Download the file from `url` and save it locally under `file_name`:
    with urllib.request.urlopen(
            "https://www.alko.fi/INTERSHOP/static/WFS/Alko-OnlineShop-Site/-/Alko-OnlineShop/fi_FI/Alkon%20Hinnasto%20Tekstitiedostona/alkon-hinnasto-tekstitiedostona.xls") as response, open(
            "alko_products.xls", 'wb') as out_file:
        shutil.copyfileobj(response, out_file)

    process_product_file("alko_products.xls", "alko_products.csv")

    fixEncodingFile("alko_products.csv")


    shutil.copy("alko_products.csv", "../alko-app/assets/alko_products.csv")

def fixEncodingFile(path):
    rf = open(path, "r")
    content = rf.read()
    rf.close()
    
    wf = open(path, "w")
    wf.write(content.replace("\\xc3\\xa4","ä")
                        .replace("\\xc3\\xb6", "ö")
                        .replace("\\xc3\\xa5","å")
                        .replace("\\xc3\\x84","Ä")
                        .replace("\\xc3\\x96","Ö")
                        .replace("\\xc3\\x85","Å")
                        .replace("\\",""))
    wf.close()

    #read input file
    with codecs.open(path, 'r', encoding = 'ansi') as file:
        lines = file.read()

    #write output file
    with codecs.open(path, 'w', encoding = 'utf8') as file:
        file.write(lines)

def CLEAN_FILES():
    try:
        shutil.rmtree("result")
        os.remove("alko_products.xls")
        os.remove("alko_store_names.txt")
        os.remove("myymalat-palvelut.json")
        os.remove("alko_product_ids.txt")
    except:
        print("ERROR: FAILED REMOVING FILES")


downloadAlkosToFile()
GENERATE_PRODUCT_DATA()
GENERATE_AVAILABILITY_DATA()
CLEAN_FILES()
