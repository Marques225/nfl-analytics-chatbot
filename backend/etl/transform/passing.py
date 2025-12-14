# etl/transform/passing.py
def normalize_passing(df, season, week):
    # 1️⃣ Normalize column names (fully defensive)
    df.columns = (
        df.columns
        .map(str)
        .str.lower()
        .str.replace("%", "_pct")
        .str.replace(" ", "_")
    )

    # 2️⃣ Drop duplicated columns (PFR tables often contain these)
    df = df.loc[:, ~df.columns.duplicated()]

    # 3️⃣ Enforce required ETL dimensions
    df["season"] = season
    df["week"] = week

    return df
