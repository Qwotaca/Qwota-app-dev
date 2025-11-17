coach_entrepreneurs = {
    "coach01": ["mathis", "admin"],
}

def get_entrepreneurs_for_coach(coach_username: str):
    return coach_entrepreneurs.get(coach_username, [])
