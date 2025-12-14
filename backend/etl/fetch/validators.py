def validate_week(df, season, week):
    assert not df.empty, "Empty dataframe"
    assert df["season"].iloc[0] == season
    assert df["week"].iloc[0] == week
    assert "player" in df.columns or "player_name" in df.columns
