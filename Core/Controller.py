from flask import jsonify
from flask import request
from flask import Response
from Core.Config import Config
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.utils import secure_filename
from Core.Config import Config
from Core.SQL import SQL
from guard import protectRequest
import importlib
import os
import yaml
import sqlalchemy
import json
import uuid

class Controller:

    def uploadFile(**kwargs) -> dict:
        if 'file' not in request.files:
            return {}
            
        filename = str(uuid.uuid4()) + '-'+ secure_filename(request.files['file'].filename)
        request.files['file'].save(os.path.join('Upload', filename))        

        return {"filename": filename}    

    # --------------------------- Process URL ---------------------------- #
    # process url given data
    # --------------------------- Process URL ---------------------------- #
    def processUrl(_info,**kwargs) -> str:     
        gotData: dict = {}
        formData: dict = None;   
        sendData = {'input': kwargs, 'processed': {}, "formData": formData}  
        config = Config()

        if _info.get('method') is None and request.method != 'GET':
            return jsonify({'error': 'SYS001','text' : 'Method not allowed'})
        elif request.method not in _info.get('method'):
            return jsonify({'error': 'SYS001','text' : 'Method not allowed'})        

        if request.method != 'GET':
            formData = request.form.to_dict()   
            content_type = request.headers.get('Content-Type') 
            sendData['formData']:dict = {}
            if request.data != '' and len(request.data) > 0:
                try:         
                    d = json.loads(request.data)
                    if 'data' in d.keys():
                        formData.update(d['data'])

                except ValueError:
                    return  jsonify({'error': 'SYS002','text' : 'Json input is not correct'})
            sendData['formData'] = formData

            if isinstance(request.json, (dict,list)):
                sendData['formData'].update(request.json)

        if _info.get('guard') == True:
            if protectRequest(_info) == False:
                return jsonify({'error': 'SYS005','Text': 'User is not authroized to access this page'})

        #if no steps avalaible then we are trying to find teh controller
        if _info.get('steps')  is None or len(_info.get('steps')) < 1:
            _info['steps'] = [{"type": "class","p": Controller.findController(_info)}]

        #loading information from given steps
        for steps in _info['steps']:

            returnData: dict = {}
            if steps['type'] == 'class':
                #loading class dynamically
                components = steps['p'].split('.')
                if components[1] is None:
                    components[1] = 'apiIndex'

                dclass = __import__('Controller.'+ components[0],globals(), locals(),fromlist=[components[0]])
                cclass= getattr(dclass,components[0])
                returnData = getattr(cclass,components[1])(**sendData)
            
            elif steps['type'] == 'sql':
                returnData = SQL.query(steps['p'],kwargs)                
            elif steps['type'] == 'select':
                directory = os.getcwd() + '/SQL/'
                fcontent = config.getYAML(directory + steps['p'] +'.yaml')
                returnData = SQL.queryTable(fcontent.get('table'),fcontent,kwargs) 
            elif steps['type'] == 'insert':
                directory = os.getcwd() + '/SQL/'
                fcontent = config.getYAML(directory + steps['p'] +'.yaml')
                returnData = SQL.queryTable(fcontent.get('table'),fcontent,kwargs)                 
            elif steps['type'] == 'update':
                directory = os.getcwd() + '/SQL/'
                fcontent = config.getYAML(directory + steps['p'] +'.yaml')
                returnData = SQL.queryTable(fcontent.get('table'),fcontent,kwargs)                 
              
            
            #merge got information from function
            if isinstance(returnData, Response):
                return returnData
            
            if returnData is not None:
                gotData.update(returnData)
                sendData['processed'] = gotData

        sendToBrowser: str = jsonify(gotData)
        return sendToBrowser

    # --------------------------- find controller ---------------------------- #
    # function find controller
    # --------------------------- find controller ---------------------------- #
    def findController(_info) -> str:
        apiController: str = "Index.apiIndex"
        pathInfo: dict = _info['path'].split('/')

        #looking up for a controller
        controllerFile: str = os.getcwd() + '/Controller/' + pathInfo[1].capitalize() +'.py'
        if os.path.isfile(controllerFile):
            apiController = pathInfo[1].capitalize() +'.apiIndex'
            # trying to load controller
            dclass = __import__('Controller.'+ pathInfo[1].capitalize(),globals(), locals(),fromlist=[pathInfo[1].capitalize()])
            cclass= getattr(dclass,pathInfo[1].capitalize())

            #trying to get action specific controller function
            if len(pathInfo) > 2:
                if pathInfo[2] == "":
                    pathInfo[2] = "index"

                funcList = dir(cclass)
                func: str = 'api'+_info['method'].capitalize() + pathInfo[2].capitalize()
                if func in funcList:
                    apiController = pathInfo[1].capitalize() + '.api'+_info['method'].capitalize() + pathInfo[2].capitalize()

                func: str = 'api'+ pathInfo[2].capitalize()
                if func in funcList:
                    apiController = pathInfo[1].capitalize() + '.api'+ pathInfo[2].capitalize()

        return apiController

    def getTableConfig(table :str) -> dict:
        directory = os.getcwd() + '/SQL/'
        with open(directory + table +'.yaml', "r") as stream:
            try:
                fcontent = yaml.safe_load(stream)
            except yaml.YAMLError as exc:
                print(exc)           
        return fcontent 


    # --------------------------- processSQL ---------------------------- #
    # process SQL Data
    # --------------------------- processSQL ---------------------------- #
    def processSQL(_info,db, **kwargs) -> str:
        directory = os.getcwd() + '/SQL/'
        output: dict = {}
        error: bool = False
        action: bool = False
        formData: dict = {}

        #loading app module
        with open(directory + _info +'.yaml', "r") as stream:
            try:
                fcontent = yaml.safe_load(stream)
            except yaml.YAMLError as exc:
                print(exc)            
        
        #gatehring SQL information
        sql: str = ""

        if fcontent.get('guard') == True:
            if protectRequest(_info) == False:
                return jsonify({'error': 'SYS005','Text': 'User is not authroized to access this page'})


        _controller = None
        _functionList = {'pre': None,'post': None}
        controllerFile: str = os.getcwd() + '/Controller/Middleware.py'
        if os.path.isfile(controllerFile):
            _controller = __import__('Controller.Middleware',globals(), locals(),fromlist=['Middleware'])
            cclass= getattr(_controller,'Middleware')
            funcList = dir(cclass)

            if 'pre' + request.method.capitalize() + _info.capitalize() in funcList:
                _functionList['pre'] = True

            if 'post' + request.method.capitalize() + _info.capitalize() in funcList:
                _functionList['post'] = True




        if request.method != 'GET':
            formData = request.form.to_dict()    

            if request.data != '' and len(request.data) > 0:
                try:         
                    d = json.loads(request.data)
                    if 'data' in d.keys():
                        formData.update(d['data'])

                except ValueError:
                    error = True
                    output = {'error': 'SYS002','text' : 'Json input is not correct'}

        if _functionList['pre'] == True:
            cclass= getattr(_controller,'Middleware')
            status, returnData = getattr(cclass,'pre' + request.method.capitalize() + _info.capitalize())(formData)
            if status == False:
                return returnData
            
            if returnData is not None:
                formData = returnData


        if kwargs.get('id') is not None:
            fcontent['single'] = 'yes'
        if kwargs.get('id') is not None and kwargs.get('id').lower() == 'add':
            allowed = fcontent['insert'].split(',')
            if request.method not in allowed:
                error = True
                output = {'error': 'SYS001','text' : 'Method not allowed'}
            else:
                action = True
                output = SQL.insert(fcontent.get('table'),formData,fcontent)



        elif kwargs.get('action') is not None and kwargs.get('action').lower() == 'update':
            allowed = fcontent['update'].split(',')
            if request.method not in allowed:
                error = True
                output = {'error': 'SYS001','text' : 'Method not allowed'}
            else:
                if len(formData) > 0:
                    action = True
                    output = SQL.update(fcontent.get('table'),formData,fcontent,kwargs)

        elif kwargs.get('action') is not None and kwargs.get('action').lower() == 'delete':
            allowed = fcontent['delete'].split(',')
            if request.method not in allowed:
                error = True
                output = {'error': 'SYS001','text' : 'Method not allowed'}
            else:
                action = True
                output = SQL.delete(fcontent.get('table'),formData,fcontent,kwargs)



        if error == False and action == False:
            if (fcontent.get('sql') is not None) and len(fcontent.get('sql')) > 0:
                sql = fcontent.get('sql')
                output= SQL.query(sql,kwargs)

            elif (fcontent.get('table') is not None) and fcontent.get('table').lower() != '':
                output = SQL.queryTable(fcontent.get('table'),fcontent,kwargs)

            if (fcontent.get('single') is not None) and fcontent.get('single').lower() == 'yes':
                if (output.get('list') is not None) and  len(output['list']) > 0:
                    record: dict = output['list'][0]
                    output =  {}
                    output['record']= record
                else:
                    output = {'error': 'REC001','text' : 'No record found'}

        #post data information 
        if _functionList['post'] == True:
            cclass= getattr(_controller,'Middleware')
            status, returnData = getattr(cclass,'post' + request.method.capitalize() + _info.capitalize())(output)
            if status == False:
                return returnData
            
            if returnData is not None:
                output = returnData

        return jsonify(output)