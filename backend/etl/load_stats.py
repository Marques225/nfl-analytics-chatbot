import supabase
import os 

def get_client():
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    return supabase.create_client(url, key)

def load(data):
    client = get_client()
    if not data:
        print("No data to load.")
        return
    client.table("weekly_stats").insert(data).execute()
