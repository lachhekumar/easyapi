class Clients:
    
    name: str = "Testing"
    
    def apiIndex(**kwargs) -> dict:
        return {"file": "index 234234"}

    def apiList(**kwargs) -> dict:
        return {"file": "Listing of clients with in system"}        