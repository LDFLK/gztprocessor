from fastapi import APIRouter, Body

from fastapi.params import Body
from typing import List

from state_managers.mindep_state_manager import MindepStateManager
import gazette_processors.mindep_gazette_processor as mindep_gazette_processor
import database_handlers.mindep_database_handler as mindep_database
import csv_writer
from routes.state_router import create_state_routes

mindep_router = APIRouter()
mindep_state_manager = MindepStateManager()

mindep_router.include_router(create_state_routes("mindep", mindep_state_manager))


@mindep_router.get("/mindep/initial/{date}/{gazette_number}")
def get_contents_of_initial_gazette(gazette_number: str, date: str):
    """
    Return contents of the initial gazette for given gazette number and date.
    """
    try:
        data = mindep_gazette_processor.extract_initial_gazette_data(gazette_number, date)
        return data
    except FileNotFoundError:
        return {"error": f"Gazette file for {gazette_number}, {date} not found."}



@mindep_router.post("/mindep/initial/{date}/{gazette_number}")
def create_state_from_initial_gazette(gazette_number: str, date: str, ministries: List[dict] = Body(...)):
    """
    Load ministries to DB and save state snapshot for initial gazette.
    """
    try:
        mindep_database.load_initial_state_to_db(gazette_number, date, ministries)
        csv_writer.generate_initial_add_csv(gazette_number, date, ministries)
        return {"message": f"State created for initial gazette {gazette_number} on {date}"}
    except FileNotFoundError:
        return {"error": f"Gazette file for {gazette_number}, {date} not found."}



@mindep_router.get("/mindep/amendment/{date}/{gazette_number}")
def get_contents_of_amendment_gazette(gazette_number: str, date: str):
    """
    Return the predicted transactions from the amendment gazette.
    """
    try:
        transactions = mindep_gazette_processor.process_amendment_gazette(gazette_number, date)
        return transactions
    except FileNotFoundError:
        return {"error": f"Gazette file for {gazette_number}, {date} not found."}


@mindep_router.post("/mindep/amendment/{date}/{gazette_number}")
def create_state_from_amendment_gazette(gazette_number: str, date: str, transactions: dict = Body(...)):
    """
    Apply user-reviewed transactions and save new state snapshot.
    """
    try:
        mindep_database.apply_transactions_to_db(gazette_number, date, transactions)
        csv_writer.generate_amendment_csvs(gazette_number, date, transactions)
        return {"message": f"State updated for amendment gazette {gazette_number} on {date}"}
    except FileNotFoundError:
        return {"error": f"Gazette file for {gazette_number}, {date} not found."}
