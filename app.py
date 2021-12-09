from flask import Flask
from flask import jsonify
from Core.Config import Config
from Core.Controller import Controller
from Core.SQL import SQL
from flask_session import Session
from flask_cors import CORS
from Core.Validation import Validation
import os


#creating config object
config = Config()

app = Flask(__name__)

#getting application display route from json file
applicationRoute: dict = config.getRoute()
sqlData: dict = config.getSQL()
tableData: dict = config.getTables()

#get DB configuration
directory = os.getcwd() + '/Config/'
dbinfo = config.getYAML(directory + 'db.yaml')
siteInfo = config.getYAML(directory + 'site.yaml')
errorInfo = config.getYAML(directory + 'error.yaml')

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
         '_info': route,
         'db': db
      })

# add default view for sql service
allowedMethod: list =['GET','POST','PUT','DELETE']
for sql in sqlData:
    parameter: dict = {'_info': sql,'db': db}
    app.add_url_rule('/_view/' + sql,methods = allowedMethod,view_func=Controller.processSQL,defaults = parameter)
    app.add_url_rule('/_view/' + sql +'/<id>',methods = allowedMethod,view_func=Controller.processSQL,defaults = parameter)   
    app.add_url_rule('/_view/' + sql +'/<id>/<action>',methods = allowedMethod,view_func=Controller.processSQL,defaults = parameter)



# @app.before_request
# def loadOnEveryRequest():
#     print("Impelementation Required")
        
@app.errorhandler(404)
def page_not_found(error):
    return 'This page does not exist', 404



# Run application from in realoader mode
app.run(use_reloader=True)