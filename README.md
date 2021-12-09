## CORS implementation
Setting avaliable in file: config/site.yaml
```yaml

cors: true
credentials: true
allowed:
  - url: "/*"
    method: "GET,POST"
    origin:
      - "kumar.ws"
      - "google.com"
```


## Route Configuration 

File: Config/route.json
```js
{"path":"/clients/<id>","steps":[
            {"type":"sql","p":""},
            {"type":"select","p":""},
            {"type":"insert","p":""},
            {"type":"update","p":""},
            {"type":"delete","p":""},
            {"type":"class","p":""}
    ],"method":"GET", "gaurd": true, "validate":"input.json"}
```

> All class will be referred from controller folder eg: Index.getIndex in this example Index is a class and getIndex is a function

- **gaurd** set to true will login/session validator to validate request.
- **validate** - Request by Querystring/Post as per the validation configured
- **method** - Allowed method it can be POST, GET, PUT, DELETE
- **path** - URL  that need to be processed
- **steps** - What action to performed when a url is callled
    - Steps Type
        - sql - Execute given query from a file
        - select -  Directly fire sql query given in or select from table
        - insert - Insert into table
        - update - Update into table
        - delete - Delete from table
        - class - Call controller function



## Table Declaration
SQL/Table/<tablename>.json
```json
{
    "company_id": {"type": "Integer","primary": true},
    "name": {"type": "String", "null":false, "valid": {"min": 2,"max": 50}},
    "phone": {"type": "String", "null":true, "valid": {"min": 2,"max": 50, "pattern":""}},
    "email": {"type": "String", "unique":true, "valid": {"email": true}},
    "status": {"type": "String", "default":"active", "set":["active","inactive"]}
}
```

- Type
    - Integer
    - String(size)
    - Text
    - DateTime
    - Float
    - Boolean
    - PickleType
    - LargeBinary


Query Defination
SQL/<queryname>.yaml this can be accessed using /_view/<queryname>
 - POST - Used for insert
 - PUT - Used for update
 - DELETE - Used for delete

 ```yaml
sql: "select * from	drivers limit 0,10"
guard: true
  
table: drivers
condition: "client_id={{session.id}}"

insert: "POST"  
update: "PUT,PATCH"
delete: "DELETE"

filter:
  inactive: ""
  notrequired: ""

single: "yes"
displayList: true
```

_insert_: Which method is allowed
_update_: Which method is allowed
_delete_: Which method is allowed

_filter_: Condition accept a array of condition, The key will be considered as a name

_displayList_: On update, insert, delete do you want to get the list again

condition - will be applied for all query which is execute for given view
{{session.id}} - will be replaced by id in session
- parse the {{ varaible given }} 
- get. get from the QUERY string
- post. get from request.json
- input. get from teh passed value
- session. get from session value


URL:
-----------
- **Pagigantion**: _view/<url>?record=20&page=0   
- **Search**: _view/company?record=30&search={"name":{"type":"like","value":"%Enterprises%"},"status":{"type":"=","value":"active"}}
- _view/company/1  -> Get only 1 records
- _view/company/add -> add new records to system, application should pass info in {data: {}}
- _view/company/1/update -> update records to system, application should pass info in {data: {}}
- _view/company/1/delete -> delete records from


## Packages
pip install pyyaml
pip install sqlalchemy
pip install -U Flask-SQLAlchemy
pip install  psycopg2
pip install sqlescapy
pip install Flask-Session
pip install -U flask-cors