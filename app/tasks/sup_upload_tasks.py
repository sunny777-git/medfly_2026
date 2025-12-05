# app/tasks/sup_upload_tasks.py
import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE")
SUPABASE_BUCKET = os.getenv("SUPABASE_BUCKET")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def upload_to_supabase(local_path: str, filename: str):
    try:
        with open(local_path, "rb") as f:
            res = supabase.storage.from_(SUPABASE_BUCKET).upload(filename, f)
            print("[upload_to_supabase] Response:", res)
    except Exception as e:
        print("[upload_to_supabase] Exception:", repr(e))
        try:
            print("[upload_to_supabase] Status code:", e.response.status_code)
            print("[upload_to_supabase] Body:", e.response.text)
        except Exception:
            pass
    finally:
        if os.path.exists(local_path):
            try:
                os.remove(local_path)
                print(f"[upload_to_supabase] Deleted local file: {local_path}")
            except Exception as e:
                print("[upload_to_supabase] Failed to delete local file:", e)
