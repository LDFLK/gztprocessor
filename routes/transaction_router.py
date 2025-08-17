import json
from typing import Any, Dict, List
from fastapi import APIRouter
from fastapi.params import Body

import utils as utils
from gztprocessor.database_handlers.transaction_database_handler import get_gazette_info, get_gazettes_by_president, set_warning
from gztprocessor.database_handlers.transaction_database_handler import (save_transactions,)
from gztprocessor.database_handlers.transaction_database_handler import (get_saved_transactions,)

transaction_router = APIRouter()

@transaction_router.get("/info/{gazette_number}")
def get_gazette_info_route(gazette_number: str):
    info = get_gazette_info(gazette_number)
    if info:
        return info
    return {"error": "No info found for gazette"}

@transaction_router.get("/info/{gazette_type}/{from_date}/{to_date}")
def get_gazettes_per_president(gazette_type:str,from_date: str, to_date: str):
   return get_gazettes_by_president(gazette_type, from_date, to_date)

@transaction_router.post("/transactions/{gazette_number}")
def save_current_transactions(gazette_number: str, payload: Dict[str, Any] = Body(...)):
    # payload expected to be like: {"transactions": [...], "moves": [...]}
    save_transactions(gazette_number, payload)
    return {"status": "success"}

@transaction_router.get("/transactions/{gazette_number}")
def get_transactions(gazette_number: str):
    result = get_saved_transactions(gazette_number) 
    return result

@transaction_router.post("/transactions/{gazette_number}/warning")
def set_warning_route(gazette_number: str, payload: dict = Body(...)):
    """
    Set or clear the warning flag for a given gazette number.
    Expects payload like: {"warning": true} or {"warning": false}
    """
    warning = payload.get("warning")
    if warning is None:
        return {"error": "Missing 'warning' in request body"}
    
    set_warning(gazette_number, bool(warning))
    return {"status": "success", "gazette_number": gazette_number, "warning": bool(warning)}