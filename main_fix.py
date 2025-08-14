# Add this safety check in main.py where get_user_data is called

def get_user_data_safe(user_id):
    """Safe wrapper for get_user_data that handles None returns"""
    user = get_user_data(user_id)
    if user is None:
        # Return default values if user not found
        return {
            'UserID': str(user_id),
            'Name': 'Unknown',
            'Username': '',
            'Tokens': 0,
            'Points': 0,
            'ReferralEarnings': 0,
            'MoMoNumber': '',
            'referral_code': f"REF{str(user_id)[-6:]}"
        }
    return user

# Use this instead of direct get_user_data calls
