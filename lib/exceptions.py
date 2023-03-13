class apiException(Exception):
    #Raised when the api returns an error code
    #Attributes:
    #   cod -- error code returned by api
    #   message -- error message returned by api
    def __init__(self, cod, message):
        self.cod = cod
        self.message = message
        super().__init__(self.message)
