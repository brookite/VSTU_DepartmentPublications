from rest_framework.response import Response
from rest_framework import status


class APIResponse(Response):
    def __init__(self, data=[], status=status.HTTP_200_OK, message=None):
        response_data = {"items": data}
        if status is not None:
            if status >= 400:
                response_data["type"] = "error"
                response_data["message"] = message if message else "An error occurred"
            else:
                response_data["type"] = "success"
        super().__init__(response_data, status=status)
