from typing import List
from flask import jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import types
from sqlalchemy import text
from sqlalchemy import Column, ForeignKey
from sqlalchemy.sql.expression import true
from sqlescapy import sqlescape
from flask import request, session
from Core.Validation import Validation
import sys
import json
import re

class SQL:

    db = None
    dynamicClass: dict = {}
    tableField: dict = {}

    def connect(app):
        try:
            db = SQLAlchemy(app)
            SQL.db = db
            Validation.SQL = SQL
        except SQLAlchemyError as e:
            errorText = str(e.__dict__['orig'])
            print(errorText)
            sys.exit(-1)
        return db


    #run raw query
    def query(sql: str,input) -> dict:
        rList: List = []
        try:
            result = SQL.db.engine.execute(sql)
        except SQLAlchemyError as e:
            errorText = str(e.__dict__['orig'])
            return {'error': 'SQL001','text' : errorText}

        for row in result:
            rList.append(dict(row.items()))        

        return {"list": rList}


    #process table directrly
    def queryTable(table: str, config, input, search = None, direct = None,rawQuery = None) -> dict:

        returnData: dict = {}
        page: int = None
        perPage: int = None
        filterData: dict = None
        noSep: list = ['BigInteger','Integer','Float','Numeric','SmallInteger']

        #get configuration from querystring
        if request.args.get("page") is not None:
            page = int(request.args.get("page"))
        if request.args.get("record") is not None:
            perPage = int(request.args.get("record"))

        if request.args.get("search") is not None:
            filterData = json.loads(request.args.get("search"))

        if search is not None:
            if (filterData is None):
                filterData = search
            else:
                filterData.update(search)

        if SQL.dynamicClass.get(table) is not None:
            sqlQuery = SQL.dynamicClass[table].query
            if(filterData is not None):
                for filter in filterData:
                    fData = filterData[filter]
                    sep: str = "'"                    
                    if SQL.tableField[table][filter] is not None:
                        if SQL.tableField[table][filter]['type'] in noSep:
                            sep = ''

                    queryString = text(SQL.processParameter(sqlescape(table)+"."+ sqlescape(filter) + ' ' + 
                                        sqlescape(fData['type']) +  sep + sqlescape(fData['value']) + sep,input))
                    sqlQuery = sqlQuery.filter(queryString)

            #write  direct sql statement
            if request.args.get("_direct") is not None:
                sqlQuery = sqlQuery.filter(text(SQL.processParameter(request.args.get("_direct"),input)))
            
            if config.get('condition') is not None:
                sqlQuery = sqlQuery.filter(text(SQL.processParameter(config.get('condition'),input)))

            if input.get('id') is not None:
                sep: str = "'"                    
                pkField: str = SQL.getPrimaryKey(table)
                if SQL.tableField[table][pkField] is not None:
                    if SQL.tableField[table][pkField]['type'] in noSep:
                        sep = ''

                sqlQuery = sqlQuery.filter(text(sqlescape(table)+'.'+ pkField + "=" + sep + sqlescape(input.get('id')) + sep))

            #return raw Query
            if rawQuery == True:
                return sqlQuery

            try:
                if perPage is not None or page is not None:
                    if page is None or page < 1:
                        page = 1   

                    if perPage is None or perPage < 1:
                        perPage = 10                 

                    records = sqlQuery.paginate(page, perPage, False)
                    if(direct == True):
                        return records
                    listdata = [SQL.serialize(table,record) for record in records.items]
                    returnData = {'list': listdata,'totalPage' : records.pages, 'total': records.total }

                else:
                    records = sqlQuery.all()
                    if(direct == True):
                        return records

                    listdata = [SQL.serialize(table,record) for record in records]
                    returnData = {'list': listdata}

            except SQLAlchemyError as e:
                errorText = str(e.__dict__['orig'])
                return {'error': 'SQL001','text' : errorText}

        else:
            returnData = {'error': 'SQL002','text' : table + ' defination not avaliable'}
        
        return returnData

    def fieldValidation(table: str,data: dict, fieldInfo: dict, update: bool = False, other: dict ={}) -> dict:
        returnData: dict = {}

        #looping with in data
        for field in data:
            errorList: list = []
            info = fieldInfo.get(field)
            if info.get('unique') == True:
                r = Validation.unique(table,field,data[field],info,update,other)
                if r.get('code') is not None:
                    errorList.append(r)

            if info.get('set') is not None:
                r = Validation.set(table,field,data[field],info)
                if r.get('code') is not None:
                    errorList.append(r)

            if info.get('valid') is not None:
                for func in info.get('valid'):
                    r = getattr(Validation,func)(table,field,data[field],info)
                    if r.get('code') is not None:
                        errorList.append(r)


            if len(errorList) > 0:
                returnData[field] = errorList


        return returnData


    #insert into table
    def insert(table: str, data: dict, config: dict):
        returnData: dict = {}
        if SQL.tableField[table] is None:
            return {'error':'SQL003', 'text': 'Table defination is not avaliable'}


        for field in SQL.tableField[table]:
            finfo = SQL.tableField[table][field]
            fillData = False if (finfo.get('primary') is not None and finfo.get('primary') == True) else True
            if fillData == True:
                if data.get(field) is None:
                   if finfo.get('null') is not None and  finfo.get('null') == False:
                       data[field] = '' if finfo.get('default') is None else finfo.get('default')

        validate: dict= SQL.fieldValidation(table,data,SQL.tableField[table])
        if len(validate) > 0:
            return validate
            
        insert = SQL.dynamicClass[table](**data)

        #inserting to DB tables
        try:
            SQL.db.session.add(insert)
            SQL.db.session.commit()

            pk = SQL.getPrimaryKey(table)
            id = getattr(insert,pk)
            returnData = {'success': 'true','id': id}
        except SQLAlchemyError as e:
            errorText = str(e.__dict__['orig'])
            return {'error': 'SQL002','text' : errorText}

        return returnData



    #insert into table
    def update(table: str, data: dict, config: dict, input: dict):

        returnData: dict = {}

        if SQL.tableField[table] is None:
            return {'error':'SQL003', 'text': 'Table defination is not avaliable'}

        validate: dict= SQL.fieldValidation(table,data,SQL.tableField[table], True,{'id': input.get('id'), 'field': SQL.getPrimaryKey(table)})
        if len(validate) > 0:
            return validate

        listData = SQL.queryTable(table,config,input,direct=True)
        if(len(listData) == 0):
            return {'error':'SQL004', 'text': 'Record not avaliable for update'}

        for field in data:
            if SQL.tableField[table].get(field) is not None:
                setattr(listData[0],field,data[field])
        #updating to DB tables
        try:
            SQL.db.session.commit()
            returnData = {'success': 'true'}
        except SQLAlchemyError as e:
            errorText = str(e.__dict__['orig'])
            return {'error': 'SQL002','text' : errorText}

        return returnData        


    #insert into table
    def delete(table: str, data: dict, config: dict, input: dict):

        returnData: dict = {}

        if SQL.tableField[table] is None:
            return {'error':'SQL003', 'text': 'Table defination is not avaliable'}

        listData = SQL.queryTable(table,config,input,direct=True)
        if(len(listData) == 0):
            return {'error':'SQL004', 'text': 'Record not avaliable for delete'}


        #query = SQL.queryTable(table,config,input,rawQuery=True)

        try:
            SQL.db.session.delete(listData[0])
            SQL.db.session.commit()
            returnData = {'success': 'true'}
        except SQLAlchemyError as e:
            errorText = str(e.__dict__['orig'])
            return {'error': 'SQL002','text' : errorText}

        return returnData           

    # parse the {{ varaible given }} 
    # get. get from the QUERY string
    # post. get from request.json
    # input. get from teh passed value
    # session. get from session value

    def processParameter(condition: str, input: dict) -> str:
        p = re.compile(r'{{[a-zA-Z\._\-]+}}')
        foundData = p.findall(condition)
        for idata in foundData:
            data = idata.replace('{{','').replace('}}','').split('.')
            starterObject  = None
            if data[0].lower() == 'get':
                starterObject = request.args.get(data[1])
            elif data[0].lower() == 'post':
                starterObject = request.json
            elif data[0].lower() == 'session':
                starterObject = session[data[1]]
            else:
                starterObject = input[data[1]]

            for ad in data[2:]:
                if ad in dir(starterObject):
                    starterObject = starterObject[ad]

            if isinstance(starterObject, str):
                condition = condition.replace( idata,starterObject)
            else:
                condition = condition.replace( idata,'')

        return condition


    #------------------ get primar key for given table ----------------#
    def getPrimaryKey(table) -> str:
        for field in SQL.tableField[table]:
            if(SQL.tableField[table][field].get('primary') is not None and SQL.tableField[table][field].get('primary') == True):
                return field
        return ''


    #serialize got records
    def serialize(table,record) -> dict:
        returnData: dict = {}
        for field in SQL.tableField[table]:
            returnData[field] = getattr(record,field)
        return returnData

    # makeClass
    def makeClass(table, tableData):

        attr_dict: dict = {'__tablename__': table}        

        for fields in tableData:
            fieldData: str = tableData[fields]
            extra: dict = {}
            if (fieldData.get('primary') is not None) and fieldData.get('primary') == True:
                extra['primary_key'] = True

            if (fieldData.get('unique') is not None) and fieldData.get('unique') == True:
                extra['unique'] = True

            if (fieldData.get('null') is not None) and fieldData.get('null') == True:
                extra['nullable'] = True

            if (fieldData.get('default') is not None):
                extra['default'] = fieldData.get('default')

            if fieldData['type'] == 'String':
                length = 50
                if (fieldData.get('len') is not None) and fieldData.get('len') > 0: 
                    length = fieldData.get('len')

                attr_dict[fields] = Column(fields,getattr(types,fieldData['type'])(length),**extra)
            else:
                attr_dict[fields] = Column(fields,getattr(types,fieldData['type']),**extra)
    
        SQL.dynamicClass[table] = type(table,(SQL.db.Model,),attr_dict)
        SQL.tableField[table] = tableData
        
        return True