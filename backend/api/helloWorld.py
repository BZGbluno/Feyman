from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
import os
from fastapi.responses import JSONResponse
from fastapi import status

router = APIRouter()




@router.get("/api/helloWorld")
async def getChapters_endpoint():
    '''
    Small example of hello world
    '''
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"response": "nivar"}
    )
