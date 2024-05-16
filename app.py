import logging.handlers
from flask import Flask, g
from flask import jsonify
from Core.Config import Config
from Core.Controller import Controller
from Core.SQL import SQL
from Core.Weaviate import Weaviate
from flask_session import Session
from flask_cors import CORS
from Core.Validation import Validation
import os
import base64, random, datetime, logging, hashlib
from pathlib import Path
from flask import request
from dotenv import load_dotenv
from flask import session


#creating config object
dotenv_path = Path('Config/.env')
load_dotenv(dotenv_path=dotenv_path)
config = Config()


app = Flask(__name__, static_url_path = '', static_folder='Public/',
            template_folder='Public/')

#adding logs method to the system
logFormat = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
_handler = logging.handlers.TimedRotatingFileHandler(filename='Logs/info.log', when='midnight', interval=1, backupCount=30)
logging.basicConfig(encoding='utf-8',level=logging.INFO, format=logFormat, handlers=[_handler])
logging.basicConfig(filename='Logs/debug.log', encoding='utf-8',level=logging.DEBUG, format=logFormat)
logging.basicConfig(filename='Logs/error.log', encoding='utf-8',level=logging.ERROR, format=logFormat)
logging.basicConfig(filename='Logs/warning.log', encoding='utf-8',level=logging.WARNING, format=logFormat)
logger = logging.getLogger(__name__)
logger.info("Application started")


#getting application display route from json file
applicationRoute: dict = config.getRoute()
sqlData: dict = config.getSQL()
tableData: dict = config.getTables()

#get DB configuration
directory = os.getcwd() + '/Config/'
dbinfo = config.getYAML(directory + 'db.yaml')
siteInfo = config.getYAML(directory + 'site.yaml')
errorInfo = config.getYAML(directory + 'error.yaml')

#error management
Validation.Error = errorInfo

# cors implementation
if(siteInfo['cors'] == True):
    resourcesData: dict = {}
    credentials  = True if (siteInfo['credentials'] == True) else False
    for allow in siteInfo['allowed']:
        key = r""+allow['url']
        origins: list = []
        for org in allow['origin']:
            origins.append(org)

        resourcesData[key] = {"origins": origins,
                                "methods": allow['method'].split(','),
                                "supports_credentials":credentials}

    cors = CORS(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials = credentials)

db: dict =dbinfo['default']
app.config['SQLALCHEMY_DATABASE_URI'] = db['type']+'://'+ db['username']+ ':'+ db['password']+ '@'+ db['host']+ '/'+ db['database']
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# connecting to db
SQL.connect(app,tableData)
Controller.createRoute(app,applicationRoute, sqlData, logger)


#upload default function
parameter: dict = {'log': logger}
app.add_url_rule('/_upload/',methods = ['POST'],view_func=Controller.uploadFile,defaults = parameter)    
app.add_url_rule('/_status/',methods = ['GET'],view_func=Controller.status,defaults = parameter)    

# @app.before_request
# def loadOnEveryRequest():
#     print("Impelementation Required")
        
@app.errorhandler(404)
def page_not_found(error):
    logger.error('URL not found ' + request.url)
    return 'This page does not exist', 404



@app.after_request
def after_request(response):
    if g is not None and g.module is not None:
        for _class in g.module:
            if hasattr(g.module[_class],'_close'):
                g.module[_class]._close()

    return response


@app.before_request
def before_request():
    # g variable take the global variable for request
    logger.info('Request started for url ' + request.url)   

    #getting information
    setattr(g,'module',{})
    setattr(g,'files',{})
    setattr(g,'form',{})
    setattr(g,'get',{})

    g.files = Controller.getUploadFiles()    
    g.form = Controller.getFormData().update(g.files)
    g.get = Controller.getGetData()


    # load required module    
    if request.url_rule.defaults is not None:
        _compontent = request.url_rule.defaults['component'].split(',')
        if _compontent is not None:
            for compontent in _compontent:
                if compontent is not None:
                    dclass = __import__('Core.'+ compontent,globals(), locals(),fromlist=[compontent])                    
                    _class = getattr(dclass, compontent)()
                    g.module[compontent] = _class
                    


    if(str(request.content_type) == 'application/json' and request.path != '/_status/' and request.path != '/_status' and request.path != '/_replace/'):
        headers = dict(request.headers)
        logger.info('Application JSON request')
        if 'Access-Token' in headers and headers['Access-Token'] is not None:
            token = str(headers['Access-Token']).split('/')

            #token bsics
            currentDate: str = datetime.datetime.now().strftime('%Y%m%d')
            code: str = hashlib.md5((request.remote_addr +'/' + request.user_agent.string+ '/' + currentDate).encode('utf-8')).hexdigest()
            encodeToken:str = base64.b64decode(token[1]).decode("utf-8").split('/')
            if(encodeToken[0] != code):
                logger.info('Token Did not Match')
                return {'error': {'message': 'Invalid token, you can get access_totken by calling /_status api'}}
            
            uuid: str = encodeToken[1]
            setattr(request, 'uuid', uuid)
            
            
        else:
            logger.info('Token Did not Match')
            return {'error': {'message': 'Invalid token'}}




# Run application from in realoader mode
app.run(passthrough_errors=True,use_reloader=True, threaded=True,debug=True )
