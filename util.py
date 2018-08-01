import codecs
import datetime

def fixEncodingFile(path):
        #read input file
        with open(path, 'r') as file:
            lines = file.read()

        #write output file
        with codecs.open(path, 'w', encoding = 'utf8') as file:
            file.write(lines)
        
        log("Fixed file encoding: " + path)

def log(string):
        print(datetime.datetime.now().strftime('%e.%m.%Y %H:%M:%S') + " -- " + string)