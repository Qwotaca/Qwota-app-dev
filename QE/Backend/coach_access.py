coach_entrepreneurs = {
    "coach1": ["jdupont", "mathis"],
    "coach01": ["mathis", "admin"],
    "coach2": ["fboucher", "mathis"],
}

def get_entrepreneurs_for_coach(coach_username: str):
    return coach_entrepreneurs.get(coach_username, [])

def get_all_entrepreneurs():
    """Retourne tous les entrepreneurs de toutes les équipes (sans doublons)"""
    all_entrepreneurs = set()
    for entrepreneurs in coach_entrepreneurs.values():
        all_entrepreneurs.update(entrepreneurs)
    return list(all_entrepreneurs)
