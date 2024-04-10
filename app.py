import logging.handlers
from flask import Flask
from flask import jsonify
from Core.Config import Config
from Core.Controller import Controller
from Core.SQL import SQL
from flask_session import Session
from flask_cors import CORS
from Core.Validation import Validation
import os
import logging
from flask import request


#creating config object
config = Config()

app = Flask(__name__)

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

# session configuration
# session["name"] = request.form.get("name")

# app.config["SESSION_PERMANENT"] = False
# app.config["SESSION_TYPE"] = "filesystem"
# Session(app)


# connecting to db
db = SQL.connect(app)

#creating tables
for table in tableData:
    SQL.makeClass(table,tableData[table])


for route in applicationRoute:
    if route.get('method')  is None:
        route['method'] = 'GET'

    app.add_url_rule(route['path'],methods = [route['method']],view_func=Controller.processUrl,defaults = {
         '_info': route, 'db': db,'log': logger
      })

# add default view for sql service
allowedMethod: list =['GET','POST','PUT','DELETE']
for sql in sqlData:
    parameter: dict = {'_info': sql,'db': db,'log': logger}
    app.add_url_rule('/_view/' + sql,methods = allowedMethod,view_func=Controller.processSQL,defaults = parameter)
    app.add_url_rule('/_view/' + sql +'/<id>',methods = allowedMethod,view_func=Controller.processSQL,defaults = parameter)   
    app.add_url_rule('/_view/' + sql +'/<id>/<action>',methods = allowedMethod,view_func=Controller.processSQL,defaults = parameter)


#upload default function
parameter: dict = {'log': logger}
app.add_url_rule('/_upload/',methods = ['POST'],view_func=Controller.uploadFile,defaults = parameter)    

# @app.before_request
# def loadOnEveryRequest():
#     print("Impelementation Required")
        
@app.errorhandler(404)
def page_not_found(error):
    logger.error('URL not found ' + request.url)
    return 'This page does not exist', 404


@app.before_request
def before_request():
    logger.info('Request started for url ' + request.url)


# Run application from in realoader mode
app.run(passthrough_errors=True,use_reloader=True)