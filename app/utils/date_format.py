from datetime import datetime

# Format a date string to a more readable format
def format_date(value):
    if not value:
        return ""
    try:
        # Parse the ISO format date string
        if isinstance(value, str):
            date = datetime.fromisoformat(value.replace('Z', '+00:00'))
        else:
            date = value
            
        # Format the date
        return date.strftime('%B %d, %Y %I:%M %p')
    except Exception as e:
        print(f"Error formatting date: {e}")
        return value