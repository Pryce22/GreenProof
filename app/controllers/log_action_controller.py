from app import supabase


# Log user action to database
def log_user_action(log_data):
    try:
        supabase.table('user_logs').insert(log_data).execute()
        return True
    except Exception as e:
        print(f"Error logging to database: {e}")
        return False
