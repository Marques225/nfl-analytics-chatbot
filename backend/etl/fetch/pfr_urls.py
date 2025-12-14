def weekly_passing_url(season: int, week: int) -> str:
    return (
        f"https://www.pro-football-reference.com/"
        f"years/{season}/week_{week}.htm"
    )
