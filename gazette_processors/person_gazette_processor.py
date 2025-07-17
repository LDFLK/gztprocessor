import re
from rapidfuzz import fuzz
from db_connections.db_person import get_connection
from nltk.stem import PorterStemmer
from utils import load_person_gazette_data_from_JSON

stemmer = PorterStemmer()


def clean_ministry_name(name: str) -> str:
    """
    Lowercase, remove stopwords, stem the rest of the words.
    """
    stopwords = {"ministry", "of", "and", "for", "&", "the"}
    words = re.findall(r"\b\w+\b", name.lower())
    filtered = [stemmer.stem(word) for word in words if word not in stopwords]
    return " ".join(filtered)


def get_fuzzy_matches_for_ministry(ministry_name: str, threshold=70) -> list[dict]:
    """
    Fuzzy match a given ministry name against current ministry-person assignments in DB.
    Uses cleaned & stemmed names for comparison, but returns original labels.
    If DB is empty (first gazette), returns empty list.
    """
    matches = []
    cleaned_target = clean_ministry_name(ministry_name)
    target_tokens = set(cleaned_target.split())

    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT portfolio.name, portfolio.position, person.name
            FROM portfolio
            LEFT JOIN person ON portfolio.person_id = person.id
         """
        )
        db_ministries = cur.fetchall()

        if not db_ministries:
            # First gazette case — DB is empty
            return []

        for db_name, db_position, db_person in db_ministries:
            cleaned_db_name = clean_ministry_name(db_name)
            db_tokens = set(cleaned_db_name.split())
            score = fuzz.token_sort_ratio(cleaned_target, cleaned_db_name)
            word_overlap = len(target_tokens & db_tokens)

            if score >= threshold or word_overlap >= 1:
                matches.append(
                    {
                        "existing_ministry": db_name,
                        "existing_position": db_position,
                        "existing_person": db_person,
                        "score": score,
                    }
                )

    return sorted(matches, key=lambda x: x["score"], reverse=True)


def process_person_gazette(gazette_number: str, date_str: str) -> dict:
    data = load_person_gazette_data_from_JSON(gazette_number, date_str)
    adds = data.get("ADD", [])
    terminates = data.get("TERMINATE", [])

    adds_by_name = {entry["name"]: entry for entry in adds}
    terminates_by_name = {entry["name"]: entry for entry in terminates}

    moves = []
    used_terminate_names = set()

    for name in set(adds_by_name.keys()) & set(terminates_by_name.keys()):
        add_entry = adds_by_name[name]
        terminate_entry = terminates_by_name[name]
        used_terminate_names.add(name)

        raw_suggestions = get_fuzzy_matches_for_ministry(
            add_entry.get("Ministry", ""), threshold=70
        )

        filtered_suggestions = [
            suggestion
            for suggestion in raw_suggestions
            if suggestion["existing_ministry"] != terminate_entry.get("Ministry")
            or suggestion["existing_position"] != terminate_entry.get("position")
        ]

        moves.append(
            {
                "type": "MOVE",
                "name": name,
                "from_ministry": terminate_entry.get("Ministry"),
                "from_position": terminate_entry.get("position"),
                "to_ministry": add_entry.get("Ministry"),
                "to_position": add_entry.get("position"),
                "date": add_entry.get("date"),
                "suggested_terminates": filtered_suggestions,
            }
        )

    remaining_adds = []
    for entry in adds:
        if entry["name"] not in used_terminate_names:
            remaining_adds.append(
                {
                    "type": "ADD",
                    "new_person": entry["name"],
                    "new_ministry": entry["Ministry"],
                    "new_position": entry["position"],
                    "date": entry["date"],
                    "suggested_terminates": get_fuzzy_matches_for_ministry(
                        entry.get("Ministry", ""), threshold=70
                    ),
                }
            )

    remaining_terminates = []
    for entry in terminates:
        if entry["name"] not in used_terminate_names:
            remaining_terminates.append(
                {
                    "type": "TERMINATE",
                    "name": entry["name"],
                    "ministry": entry["Ministry"],
                    "position": entry["position"],
                    "date": entry["date"],
                }
            )

    return {
        "transactions": {
            "moves": moves,
            "adds": remaining_adds,
            "terminates": remaining_terminates,
        }
    }
