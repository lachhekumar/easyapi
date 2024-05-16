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
    ],"method":"GET", "gaurd": true, "validate":"input.json", "type":"html","template": "index.html","component": "SQL"}
```


> All class will be referred from controller folder eg: Index.getIndex in this example Index is a class and getIndex is a function
> function can return {'formData' : {}} this will replace the existing formData 

> self.log.info('<your message>') You can create your own log 

- **gaurd** set to true will login/session validator to validate request.
- **validate** - Request by Querystring/Post as per the validation configured
- **method** - Allowed method it can be POST, GET, PUT, DELETE
- **path** - URL  that need to be processed
- **component** - Any component to be loaded during request
- **steps** - What action to performed when a url is callled
    - Steps Type
        - sql - Execute given query from a file
        - select -  Directly fire sql query given in or select from table
        - insert - Insert into table
        - update - Update into table
        - delete - Delete from table
        - class - Call controller function
- **type** set return type default  is json
- **template** Template to be rendered at display


> Every controller function will get 3 input parameter **input**, **processed** , **formData**
- **input** - Input given by client, eg: /client/1 in this url user will get {id: 1} in input
- **processed** - If you are calling multiple step in url, previous function returned option will clubbed and sent in this option
- **formData** - Got input from form. if json request sent then ['data'] object will be considered

> component can have a function **_close** which will be called after page execution


## Table Declaration
SQL/Table/<tablename>.json
```json
{
    "company_id": {"type": "Integer","primary": true},
    "name": {"type": "String", "null":false, "valid": {"min": 2,"max": 50}},
    "phone": {"type": "String", "null":true, "valid": {"min": 2,"max": 50, "pattern":""}},
    "email": {"type": "String", "unique":true, "valid": {"email": true},"foreign":"drivers.drivers_id"},
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
    - Relationship ( Bind relationship)

> Note: if type is "Relationship", then "table" options should be added with the Table name.

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


**Controller/Middleware.py**  can hold the function which can be called pre & post execution of the SQL / Table page.
Function name should be formatted in the following style pre<request.method><Table|SQL>(input: dict) and post<request.method><Table|SQL>(input: dict)
**example:**
- preGetCompany
- prePostCompany

```python
    def preGetCompany(input: dict):
        return True, input  
```

function should return 2 value 
- 1. true|false  success status 
- 2. on success of pre function  it should return "input" assign it can be with modification
- 3. on success of post function  it should return object
- 4. on error of pre / post function  should return error object

URL:
-----------
- **Pagigantion**: _view/<url>?record=20&page=0   
- **Search**: _view/company?record=30&search={"name":{"type":"like","value":"%Enterprises%"},"status":{"type":"=","value":"active"}}
- _view/company/1  -> Get only 1 records
- _view/company/add -> add new records to system, application should pass info in {data: {}}
- _view/company/1/update -> update records to system, application should pass info in {data: {}}
- _view/company/1/delete -> delete records from

## Access Token
Service will need access token you can get access token form /_status/ call.  Pass access_token which is recieved in header
{
  'access-token': ***access-token***
}
Access token carry a uuid for every section you can get the same from ***request.uuid***


## Packages
pip install pyyaml<br/>
pip install sqlalchemy<br/>
pip install -U Flask-SQLAlchemy<br/>
pip install sqlescapy<br/>
pip install Flask-Session<br/>
pip install -U flask-cors<br/>