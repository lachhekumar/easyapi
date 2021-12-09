class Index:
    
    name: str = "Testing"
    def getIndex() -> dict:
        return {"file": "index 1222"}

    #defaultly called this if controller is assigned
    def apiIndex() -> dict:
        return {"call": "Dynamic"}


    def apiClients() -> dict:
        return {"call": "Dynamic"}
