from flask import jsonify
from flask import request
from flask import Response
from flask import render_template
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
import hashlib
import datetime
import base64, random
import requests

class Controller:


    def createRoute(app, routes, sqlData, db, logger):
        for route in routes:
            if route.get('method')  is None:
                route['method'] = 'GET'

            app.add_url_rule(route['path'],methods = [route['method']],view_func=Controller.processUrl,defaults = {
                '_info': route, 'db': db,'log': logger, 'path': route['path'], 'type': route['type'] if 'type' in route else 'json'
                , 'template': route['tempalte'] if 'tempalte' in route else 'template.html'
            })

        # add default view for sql service
        allowedMethod: list =['GET','POST','PUT','DELETE']
        for sql in sqlData:
            parameter: dict = {'_info': sql,'db': db,'log': logger}
            app.add_url_rule('/_view/' + sql,methods = allowedMethod,view_func=Controller.processSQL,defaults = parameter)
            app.add_url_rule('/_view/' + sql +'/<id>',methods = allowedMethod,view_func=Controller.processSQL,defaults = parameter)   
            app.add_url_rule('/_view/' + sql +'/<id>/<action>',methods = allowedMethod,view_func=Controller.processSQL,defaults = parameter)


    def call(url,data = None,type = None):
        res = requests.get(request.base_url + '_status').json()
        token = res['access_token']

        if type is not None and type.lower() == 'post':
            res = requests.post(request.base_url + url, json  = data, headers= {
                'access-token': token
            }).json()

        elif type is not None and type.lower() == 'patch':
            res = requests.patch(request.base_url + url, json  = data, headers= {
                'access-token': token
            }).json()

        elif type is not None and type.lower() == 'put':
            res = requests.put(request.base_url + url, json  = data, headers= {
                'access-token': token
            }).json()

        elif type is not None and type.lower() == 'put':
            res = requests.delete(request.base_url + url, headers= {
                'access-token': token
            }).json()
        else:
            res = requests.get(request.base_url + url, headers= {
                'access-token': token
            }).json()

        return res


    # get form data into the system
    def getFormData():

        formData:dict = {}
        if request.method == 'POST' or request.method == 'PATCH':            
            if request.form != '' and len(request.form) > 0:
                formData = request.form.to_dict()   
            elif isinstance(request.json, (dict,list)):
                formData.update(request.json)
            elif request.data != '' and len(request.data) > 0:
                    d = json.loads(request.data)
                    if 'data' in d.keys():
                        formData.update(d['data'])

        return formData
    

    #get the input data from the query string
    def getGetData():
        formData: dict = {}
        args = request.args
        for name, value in args.items():
            formData[name] =value
        return formData



    def status(**kwargs) -> dict:
        
        currentDate: str = datetime.datetime.now().strftime('%Y%m%d')
        code: str = hashlib.md5((request.remote_addr +'/' + request.user_agent.string+ '/' + currentDate).encode('utf-8')).hexdigest() + '/' + str(uuid.uuid4())
        token:str = base64.b64encode(code.encode()).decode('utf-8')

        data: dict = {
            'remote_addr': request.remote_addr,
            'url':  request.path,
            'host': request.host,
            'user-agent': request.user_agent.string,
            'headers': dict(request.headers),
            'access_token': request.remote_addr.replace('.','') + datetime.datetime.now().strftime('%d%y%m') + '/' + token + '/' + str(random.random())
        }

            
        return data

    
    def uploadFile(**kwargs) -> dict:
        if 'file' not in request.files:
            kwargs['log'].error('File - parameter is not avaliable in the request')
            return {}
            
        filename = str(uuid.uuid4()) + '-'+ secure_filename(request.files['file'].filename)
        request.files['file'].save(os.path.join('Upload', filename))        
        kwargs['log'].info('File uplaod completed : ' + filename)

        return {"filename": filename}    

    # --------------------------- Process URL ---------------------------- #
    # process url given data
    # --------------------------- Process URL ---------------------------- #
    def processUrl(_info,**kwargs) -> str:     
        gotData: dict = {}
        formData: dict = None;   
        sendData = {'input': kwargs, 'processed': {}, "formData": formData}  
        config = Config()

        kwargs['log'].info('URL process started')

        if _info.get('method') is None and request.method != 'GET':
            kwargs['log'].error('Method Not allowed')
            return jsonify({'error': 'SYS001','text' : 'Method not allowed'})
        elif request.method not in _info.get('method'):
            kwargs['log'].error('Method Not allowed')
            return jsonify({'error': 'SYS001','text' : 'Method not allowed'})        

        if request.method != 'GET':
            formData: dict = {}
            try:         
                formData = Controller.getFormData()
            except ValueError:
                kwargs['log'].error('Json input is not correct')
                return  jsonify({'error': 'SYS002','text' : 'Json input is not correct'})
            sendData['formData'] = formData

            if isinstance(request.json, (dict,list)):
                sendData['formData'].update(request.json)

        if _info.get('guard') == True:
            if protectRequest(_info) == False:
                kwargs['log'].error('User is not authroized to access this page')
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
                kwargs['log'].info('Called function ' + components[1] + ' from class ' + components[0])
                cclass.log = kwargs['log']
                returnData = getattr(cclass,components[1])(**sendData)
            
            elif steps['type'] == 'sql':
                kwargs['log'].info('SQL step called')
                returnData = SQL.query(steps['p'],sendData['formData'])                
                
            elif steps['type'] == 'select':
                kwargs['log'].info('Select step called')
                directory = os.getcwd() + '/SQL/'
                fcontent = config.getYAML(directory + steps['p'] +'.yaml')
                returnData = SQL.queryTable(fcontent.get('table'),fcontent,sendData['formData']) 

            elif steps['type'] == 'insert':
                kwargs['log'].info('Insert step called')
                directory = os.getcwd() + '/SQL/'
                fcontent = config.getYAML(directory + steps['p'] +'.yaml')
                returnData = SQL.queryTable(fcontent.get('table'),fcontent,sendData['formData'])     

            elif steps['type'] == 'update':
                kwargs['log'].info('Update step called')
                directory = os.getcwd() + '/SQL/'
                fcontent = config.getYAML(directory + steps['p'] +'.yaml')
                returnData = SQL.queryTable(fcontent.get('table'),fcontent,sendData['formData'])                 
              
            
            #merge got information from function
            if isinstance(returnData, Response):
                return returnData
            
            if returnData is not None:
                gotData.update(returnData)
                sendData['processed'] = gotData

                if 'formData' in gotData and gotData['formData'] is not None:
                    sendData['formData'] = gotData['formData']
        sendToBrowser: str = ''
        if kwargs['type'].lower() == 'html':
            sendToBrowser = render_template(kwargs['template'] if kwargs['template'] is not None else 'template.html',data=sendData)
        else: 
            sendToBrowser = jsonify(gotData)
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

        kwargs['log'].info('SQL Process started')

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
                kwargs['log'].error('User is not authroized to access this page')
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



        #getting information about system
        if request.method != 'GET':
            try:         
                formData = Controller.getFormData()
            except ValueError:
                error = True
                kwargs['log'].error('Json input is not correct')
                output = {'error': 'SYS002','text' : 'Json input is not correct'}


        if _functionList['pre'] == True:
            kwargs['log'].info("Pre SQL function called pre" + request.method.capitalize() + _info.capitalize())
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
                kwargs['log'].error('Method not allowed')
                output = {'error': 'SYS001','text' : 'Method not allowed'}
            else:
                action = True
                output = SQL.insert(fcontent.get('table'),formData,fcontent)



        elif kwargs.get('action') is not None and kwargs.get('action').lower() == 'update':
            allowed = fcontent['update'].split(',')
            if request.method not in allowed:
                error = True
                kwargs['log'].error('Method not allowed')
                output = {'error': 'SYS001','text' : 'Method not allowed'}
            else:
                if len(formData) > 0:
                    action = True
                    output = SQL.update(fcontent.get('table'),formData,fcontent,kwargs)

        elif kwargs.get('action') is not None and kwargs.get('action').lower() == 'delete':
            allowed = fcontent['delete'].split(',')
            if request.method not in allowed:
                error = True
                kwargs['log'].error('Method not allowed')
                output = {'error': 'SYS001','text' : 'Method not allowed'}
            else:
                action = True
                output = SQL.delete(fcontent.get('table'),formData,fcontent,kwargs)



        if error == False and action == False:
            if (fcontent.get('sql') is not None) and len(fcontent.get('sql')) > 0:
                sql = fcontent.get('sql')
                if Config.displaySQL == True:
                    kwargs['log'].debug('SQL: ' + sql)

                output= SQL.query(sql,kwargs)

            elif (fcontent.get('table') is not None) and fcontent.get('table').lower() != '':
                if Config.displaySQL == True:
                    kwargs['log'].debug('SQL: ' + fcontent.get('table'))

                output = SQL.queryTable(fcontent.get('table'),fcontent,kwargs)

            if (fcontent.get('single') is not None) and fcontent.get('single').lower() == 'yes':
                if (output.get('list') is not None) and  len(output['list']) > 0:
                    record: dict = output['list'][0]
                    output =  {}
                    output['record']= record
                else:
                    kwargs['log'].error('No record found')
                    output = {'error': 'REC001','text' : 'No record found'}

        #post data information 
        if _functionList['post'] == True:
            cclass= getattr(_controller,'Middleware')
            status, returnData = getattr(cclass,'post' + request.method.capitalize() + _info.capitalize())(output)
            kwargs['log'].info("Pre SQL function called " + ' post' + request.method.capitalize() + _info.capitalize())
            if status == False:
                return returnData
            
            if returnData is not None:
                output = returnData

        return jsonify(output)