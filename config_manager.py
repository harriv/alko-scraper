#!/usr/bin/python
# -*- coding: utf-8 -*-

from configparser import ConfigParser

class ConfigManager():

    def __init__(self):
        self.parser = ConfigParser()
        self.parser.read("alkolist.conf")

    def get_value(self, area, key):
        return self.parser.get(area, key)