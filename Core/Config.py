import json
import os
import yaml

class Config:

    #get Route of existing data
    def getRoute(self) -> dict:
        directory = os.getcwd()
        cnf = open(directory + '/Config/route.json')
        route = json.load(cnf)
        return route

    # process table
    def getTables(seld) -> dict:
        directory = os.getcwd() + '/SQL/Table/'
        list: dict = {}
        arr = os.listdir(directory)

        for file in arr:
            file = file.replace('.json','')
            table = open(directory + file +'.json')
            list[file] = json.load(table)
        return list

    # get SQL data
    def getSQL(self) -> dict:
        directory = os.getcwd() + '/SQL/'
        list: dict = {}
        arr = os.listdir(directory)

        for file in arr:
            file = file.replace('.yaml','')
            list[file] = ""
        
        return list

    
    def getYAML(self, file: str) -> dict:
        returnData: dict = {}
        with open(file, "r") as stream:
            try:
                returnData = yaml.safe_load(stream)
            except yaml.YAMLError as exc:
                print(exc)
        
        return returnData
