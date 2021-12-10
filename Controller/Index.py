class Index:
    
    name: str = "Testing"
    def getIndex(**kwargs) -> dict:
        return {"file": "index 1222"}

    #defaultly called this if controller is assigned
    def apiIndex(**kwargs) -> dict:
        return {"call": "Dynamic"}


    def apiClients(**kwargs) -> dict:
        return {"call": "Dynamic"}
