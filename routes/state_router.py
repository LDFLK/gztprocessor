from fastapi import APIRouter
from gztprocessor.state_managers.state_manager import AbstractStateManager  # the shared base class

def create_state_routes(prefix: str, state_manager: AbstractStateManager) -> APIRouter:
    router = APIRouter(prefix=f"/{prefix}/state")

    @router.get("/latest")
    def get_latest_state():
        try:
            gazette_number, date_str, state = state_manager.get_latest_state()
            return {
                "gazette_number": gazette_number,
                "date": date_str,
                "state": state
            }
        except FileNotFoundError:
            return {"error": "No state versions found."}
        except ValueError as e:
            return {"error": str(e)}

    @router.get("/{date}")
    def get_state_by_date(date: str):
        try:
            result = state_manager.get_state_by_date(date)
            if isinstance(result, dict):
                return {
                    "gazette_number": result["gazette_number"],
                    "date": date,
                    "state": result["state"]
                }
            return {
                "date": date,
                "multiple_gazettes": True,
                "gazette_numbers": result
            }
        except FileNotFoundError:
            return {"error": f"No state found for date {date}"}
        except ValueError as e:
            return {"error": str(e)}

    @router.get("/{date}/{gazette_number}")
    def get_state_by_gazette_and_date(gazette_number: str, date: str):
        try:
            state = state_manager.load_state(gazette_number, date)
            return {"gazette_number": gazette_number, "date": date, "state": state}
        except FileNotFoundError:
            return {"error": "No state version found."}
        
    @router.delete("/reset")
    def reset_state():
         state_manager.clear_all_state_data()
         return {"message": "System reset: all state files deleted and database cleared."}


    return router



