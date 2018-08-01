import urllib
import shutil
import xlrd
import csv
from configparser import ConfigParser
from util import fixEncodingFile, log


class ProductScraper():

    def __init__(self, configManager, product_id_list):
        self.configManager = configManager
        self.product_id_list = product_id_list
        self.GENERATE_PRODUCT_DATA()


    def GENERATE_PRODUCT_DATA(self):
        # Download the file from `url` and save it locally under `file_name`:
        with urllib.request.urlopen(
            self.configManager.get_value("Url", "AlkoXMLProductsUrl")) as response, open("alko_products.xls", 'wb') as out_file:
            shutil.copyfileobj(response, out_file)

        self.process_product_file("alko_products.xls", "alko_products.csv")

        fixEncodingFile("alko_products.csv")
        shutil.copy("alko_products.csv", self.configManager.get_value("OutputFiles", "AlkoProductsFile"))

        log("Generated product data.")

    def process_product_file(self, file, out):
        xls_workbook = xlrd.open_workbook(file)
        xls_sheet = xls_workbook.sheet_by_name('Alkon Hinnasto Tekstitiedostona')

        csv_file = open(out, 'w')
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
            wr.writerow(list)
            self.product_id_list.append(list[0])
            
        csv_file.close()
        self.remove_empty_lines("alko_products.csv")

        log("Processing product file: " + file + " -- " + out)

    def remove_empty_lines(self, filename):
        with open(filename) as in_file, open(filename, 'r+') as out_file:
            out_file.writelines(line for line in in_file if line.strip())
            out_file.truncate()
        
        log("Removed empty lines: " + filename)