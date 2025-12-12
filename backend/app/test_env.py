from dotenv import load_dotenv
import os

load_dotenv()

print("SUPABASE_URL:", os.getenv("SUPABASE_URL"))
print("SUPABASE_SERVICE_ROLE_KEY:", os.getenv("SUPABASE_SERVICE_ROLE_KEY"))
print("DATABASE_URL:", os.getenv("DATABASE_URL"))
