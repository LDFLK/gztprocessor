from fastapi import APIRouter, Body

from fastapi.params import Body
from typing import List

from state_managers.person_state_manager import PersonStateManager
import gazette_processors.person_gazette_processor as person_gazette_processor
import database_handlers.person_database_handler as person_database
import csv_writer
from routes.state_router import create_state_routes

person_router = APIRouter()
person_state_manager = PersonStateManager()

person_router.include_router(create_state_routes("person", person_state_manager))

@person_router.get("/person/{date}/{gazette_number}")
def get_contents_of_person_gazette(gazette_number: str, date: str):
    """
    Return the predicted transactions from a person gazette.
    """
    try:
        transactions = person_gazette_processor.process_person_gazette(gazette_number, date)
        return transactions
    except FileNotFoundError:
        return {"error": f"Gazette file for {gazette_number}, {date} not found."}


@person_router.post("/person/{date}/{gazette_number}")
def create_state_from_person_gazette(date: str, gazette_number: str, payload: dict = Body(...)):
    """
    Apply user-reviewed transactions and save new state snapshot.
    """
    try:
        transactions = payload.get("transactions", {})

        person_database.apply_transactions_to_db(gazette_number, date, transactions)

        return {
            "message": f"State updated for amendment gazette {gazette_number} on {date}"
        }
    except FileNotFoundError:
        return {
            "error": f"Gazette file for {gazette_number}, {date} not found."
        }
    
    