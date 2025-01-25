
from supabase import create_client, Client
import uuid

SUPABASE_URL = "https://cjoykzgrtvlghogxzdjq.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImNqb3lremdydHZsZ2hvZ3h6ZGpxIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTczNDMwMDY4NiwiZXhwIjoyMDQ5ODc2Njg2fQ.JkShNd00ZSc7QmsthH49aS8fQPqmHuM-Xj3WuSgEsPc"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


def add_data(data):
    print("ciao")
    try:
        print("ciao")
        response = supabase.table('User').insert(data).execute()
        return ({"message": "Data inserted successfully", "response": response.data})
    except Exception as e:
        return ({"error": str(e)})



if __name__ == '__main__':
    email = None
    name = None
    surname =  None
    password = None
    phone_number = None
    created_at = None
    id = uuid.uuid4().int & (1<<32)-1
    print(id)
    data = {
        'id': id,
        'email': "valerio",
        'name': "a",
        'surname': "b",
        'password': "c",
        'phone_number': "d",
        'created_at': "01/01/2025"
    }
    e = add_data(data)
    print(str(e))
    
    

