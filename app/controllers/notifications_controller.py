from app import supabase
import uuid

def create_notification(type, sender, receiver, company_id = None, amount = None, same_request = None, sender_company_id = None):

    try:
        notification_id = uuid.uuid4().int & (1<<32)-1
        

        notification_data = {
            'id_notification': notification_id,
            'type': type,
            'sender_email': sender,
            'receiver_email': receiver,
            'status': 'unread',
            'company_id': company_id,
            'requested_token': amount,
            'same_request': same_request,
            'sender_company_id': sender_company_id
        }

        response = supabase.table('notifications').insert(notification_data).execute()
        if response.data:
            return True
    
    except Exception as e:
        print(f"Error creating notification: {e}")
        return False
    

def get_notifications_by_email(email):
    try:
        response = supabase.table('notifications').select('*').eq('receiver_email', email).order('created_at', desc=False).execute()
        # Access the data attribute of the response
        notifications = response.data
        return notifications
    except Exception as e:
        print(f"Error getting notifications: {e}")
        return None
    

def get_unread_notifications_count(receiver_email):
    try:
        response = supabase.table('notifications').select('*').eq('receiver_email', receiver_email).eq('status', 'unread').execute()
        # Access the data attribute of the response
        notifications = response.data
        return len(notifications) if notifications else 0
    except Exception as e:
        print(f"Error getting notifications count: {e}")
        return 0

def delete_notification(notification_id):
    """Delete a notification and return success status"""
    try:
        # Get the notification first to check its existence and type
        notification = supabase.table('notifications') \
            .select('*') \
            .eq('id_notification', notification_id) \
            .execute()
            
        if not notification.data:
            print(f"Notification {notification_id} not found")
            return False
            
        # Delete the notification
        result = supabase.table('notifications') \
            .delete() \
            .eq('id_notification', notification_id) \
            .execute()
            
        return True if result.data else False
    except Exception as e:
        print(f"Error deleting notification: {e}")
        return False
    
def get_notification_by_id(notification_id):
    try:
        notification = supabase.table('notifications') \
            .select('*') \
            .eq('id_notification', notification_id) \
            .execute()
    except Exception as e:
        print(f"Error getting notification: {e}")
        return None
    notification = notification.data[0] if notification.data else None
    return notification

def send_notification_to_admin(type, sender, company_id):
    try:
        # Get all company admins
        admins = supabase.table('roles') \
            .select('email') \
            .eq('admin', True) \
            .execute()
        if not admins.data:
            return False
        
        # Send a notification to each admin
        for admin in admins.data:
            create_notification(type, sender, admin['email'], company_id)
        return True
    except Exception as e:
        print(f"Error sending notification to admins: {e}")
        return False

def mark_as_read(notification_id):
    try:
        response = supabase.table('notifications') \
            .update({'status': 'read'}) \
            .eq('id_notification', notification_id) \
            .execute()
        return bool(response.data)
    except Exception as e:
        print(f"Error marking notification as read: {e}")
        return False

def delete_notification_for_all_admin_company(notification_id):
    try:
        # Get the notification to find related notifications
        notification = get_notification_by_id(notification_id)
        if not notification:
            return False
        
        # Delete all notifications of the same type for the same company
        result = supabase.table('notifications') \
            .delete() \
            .eq('same_request', notification['same_request']) \
            .eq('company_id', notification['company_id']) \
            .execute()
            
        return bool(result.data)
    except Exception as e:
        print(f"Error deleting company notifications: {e}")
        return False

def send_token_notification_to_all_company_admin(type, notificaion_id):
    try:
        # Get the notification to find related notifications
        notification = get_notification_by_id(notificaion_id)
        if not notification:
            return False
        
        # Get all company admins
        admins = supabase.table('company_employe') \
            .select('user_id') \
            .eq('company_id', notification['sender_company_id']) \
            .eq('company_admin', True) \
            .execute()
        if not admins.data:
            return False
        
        admins_email = supabase.table('user')\
            .select('email')\
            .in_('id', [admin['user_id'] for admin in admins.data])\
            .execute()
        if not admins_email.data:
            return False
        
        # Send a notification to each admin
        for admin in admins_email.data:
            create_notification(type, notification['receiver_email'], admin['email'], notification['sender_company_id'], notification['requested_token'], None, notification['company_id'])
        return True
    except Exception as e:
        print(f"Error sending notification to company admins: {e}")
        return False
    