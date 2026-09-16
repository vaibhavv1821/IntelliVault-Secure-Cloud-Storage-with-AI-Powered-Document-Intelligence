import os
import sys
from dotenv import load_dotenv

load_dotenv(".env")
from supabase import create_client

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_SERVICE_KEY")
bucket = os.getenv("SUPABASE_BUCKET_NAME", "intellivault-files")

if not url or not key:
    print("ERROR: Missing SUPABASE_URL or SUPABASE_SERVICE_KEY in .env")
    sys.exit(1)

print(f"Connecting to Supabase Storage at: {url}")
client = create_client(url, key)

try:
    items = client.storage.from_(bucket).list(path="", options={"limit": 10})
    print(f"SUCCESS: Connected to bucket '{bucket}'. Found {len(items)} items in root.")
except Exception as e:
    print(f"FAILED: Could not access bucket '{bucket}': {e}")
    sys.exit(1)
