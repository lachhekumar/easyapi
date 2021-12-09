import re

class Validation:
    SQL = None
    Error = None
    noSep: list = ['BigInteger','Integer','Float','Numeric','SmallInteger']

    def min(table,field,value, config) -> dict:
        valid: dict = config.get('valid')
        if(config.get('type') in Validation.noSep):
            if value < valid['min']:
                return Validation.Error['min']       
        else:
            if len(value) < valid['min']:
                return Validation.Error['min']       
        return {}

    def max(table,field,value, config) -> dict:
        valid: dict = config.get('valid')
        if(config.get('type') in Validation.noSep):
            if value > valid['max']:
                return Validation.Error['max']       
        else:
            if len(value) > valid['max']:
                return Validation.Error['max']       
        return {}


    def email(table,field,value, config) -> dict:
        regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        if(re.fullmatch(regex, value)):
            return {}              
        else:
            return Validation.Error['email']       

    def pattern(table,field,value, config) -> dict:
        valid: dict = config.get('valid')
        if(re.fullmatch(valid['pattern'], value)):
            return {}              
        else:
            return Validation.Error['email']       


    def unique(table,field,value, config, update = False,other: dict = {}) -> dict:
        query: str = 'select * from ' + table + ' where ' + field + "='"+ value +"'"
        if update == True:
            query = query + ' and ' + other['field'] +"!= '" + other['id'] + "'"  
            
        returnd: dict = Validation.SQL.query(query,{})
        if(returnd.get('list') is not None and len(returnd.get('list')) > 0):
            return Validation.Error['unique']
        return {}    

    def set(table,field,value, config) -> dict:
        if value not in config.get('set'):
            return Validation.Error['set']
        return {}
