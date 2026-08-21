from fastapi.responses import JSONResponse
from fastapi import Request

def not_found_handler(request: Request, exc):
    return JSONResponse(status_code=404, content={"error": "Not Found"})

def bad_request_handler(request: Request, exc):
    return JSONResponse(status_code=400, content={"error": "Bad Request"})

def forbidden_handler(request: Request, exc):
    return JSONResponse(status_code=403, content={"error": "Forbidden"})
