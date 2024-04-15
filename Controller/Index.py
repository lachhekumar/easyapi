from Core.Controller import Controller
class Index:
    
    name: str = "Testing"
    def getIndex(**kwargs) -> dict:
        Controller.call('_status')
        return {"file": "index 1222", 'form': kwargs['formData']}

    #defaultly called this if controller is assigned
    def apiIndex(**kwargs) -> dict:
        return {"call": "Dynamic"}


    def apiClients(**kwargs) -> dict:
        return {"call": "Dynamic"}
