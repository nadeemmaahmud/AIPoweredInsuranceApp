from google.oauth2 import id_token
from google.auth.transport import requests
from django.conf import settings
from users.models import CustomUser
import requests as http_requests

class GoogleAuthService:
    
    @staticmethod
    def exchange_code_for_token(code):
        token_url = 'https://oauth2.googleapis.com/token'
        
        data = {
            'code': code,
            'client_id': settings.GOOGLE_OAUTH2_CLIENT_ID,
            'client_secret': settings.GOOGLE_OAUTH2_CLIENT_SECRET,
            'redirect_uri': settings.GOOGLE_OAUTH2_REDIRECT_URI,
            'grant_type': 'authorization_code'
        }
        
        response = http_requests.post(token_url, data=data)
        
        if response.status_code != 200:
            raise Exception(f'Failed to obtain access token: {response.text}')
        
        return response.json()
    
    @staticmethod
    def verify_google_token(token):
        try:
            idinfo = id_token.verify_oauth2_token(
                token,
                requests.Request(),
                settings.GOOGLE_OAUTH2_CLIENT_ID
            )
            
            if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
                raise ValueError('Wrong issuer.')
            
            return idinfo
            
        except ValueError as e:
            raise Exception(f'Invalid token: {str(e)}')
    
    @staticmethod
    def get_or_create_user_from_google(google_user_data):
        google_id = google_user_data.get('sub')
        email = google_user_data.get('email')
        
        if not google_id or not email:
            raise Exception('Missing required user data from Google')
        
        try:
            user = CustomUser.objects.get(google_id=google_id)
            user.email = email
            user.name = google_user_data.get('name', '')
            user.profile_picture = google_user_data.get('picture', '')
            user.save()
            return user
            
        except CustomUser.DoesNotExist:
            pass
        
        try:
            user = CustomUser.objects.get(email=email)
            user.google_id = google_id
            user.profile_picture = google_user_data.get('picture', '')
            user.save()
            return user
            
        except CustomUser.DoesNotExist:
            pass
        
        username = email.split('@')[0]
        
        base_username = username
        counter = 1
        while CustomUser.objects.filter(username=username).exists():
            username = f"{base_username}{counter}"
            counter += 1
        
        user = CustomUser.objects.create(
            google_id=google_id,
            email=email,
            username=username,
            first_name=google_user_data.get('given_name', ''),
            last_name=google_user_data.get('family_name', ''),
            profile_picture=google_user_data.get('picture', ''),
        )
        
        return user