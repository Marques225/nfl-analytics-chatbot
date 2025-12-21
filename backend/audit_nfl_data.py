import nfl_data_py as nfl
import pandas as pd

# Set pandas to show all columns
pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', 10)

print("--- 1. AUDITING SEASONAL DATA (The 'Fat' Table) ---")
# Get just one year (2024) to check columns
season_df = nfl.import_seasonal_data([2024])
print(f"Total Columns found: {len(season_df.columns)}")
print("Sample Columns:", list(season_df.columns)[:15]) # Show first 15
print("\n--- CHECKING FOR SPECIFIC ADVANCED STATS ---")
print("Target Share? ", "tgt_sh" in season_df.columns)
print("Fantasy Points? ", "fantasy_points_ppr" in season_df.columns)
print("EPA (Efficiency)? ", "passing_epa" in season_df.columns)

print("\n" + "="*50 + "\n")

print("--- 2. AUDITING NEXT GEN STATS (The 'Holy Grail') ---")
# Get Passing NGS data
ngs_df = nfl.import_ngs_data(stat_type='passing', years=[2024])
print(f"Total Columns found: {len(ngs_df.columns)}")
print("Sample Columns:", list(ngs_df.columns))
print("\n--- KEY METRICS FOUND ---")
print("Time to Throw? ", "avg_time_to_throw" in ngs_df.columns)
print("CPOE (Accuracy)? ", "completion_percentage_above_expectation" in ngs_df.columns)

print("\n" + "="*50 + "\n")

print("--- 3. AUDITING ID MAPPING (The 'Linker') ---")
ids_df = nfl.import_ids()
print("Sample ID Mapping:")
print(ids_df[['name', 'position', 'team', 'gsis_id', 'sleeper_id', 'yahoo_id']].head(5))