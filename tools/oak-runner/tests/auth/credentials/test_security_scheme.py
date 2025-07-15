    
from oak_runner.auth.credentials.fetch import (
    create_security_schemes_from_auth_requirements,
)
from oak_runner.auth.models import HttpUrl, OAuth2Scheme, OAuth2Flows, ImplicitFlow, AuthorizationCodeFlow
from oak_runner.auth.auth_parser import AuthType


def test_create_security_schemes_from_auth_requirements():
    # From: googleapis.com/sheets/v4
    auth_requirements = [
        {'api_title': 'Google Sheets API',
        'auth_urls': {'authorization': 'https://accounts.google.com/o/oauth2/auth'},
        'description': 'Oauth 2.0 implicit authentication',
        'flow_type': 'implicit',
        'name': 'Oauth2',
        'required': True,
        'scopes': ['https://www.googleapis.com/auth/drive',
                    'https://www.googleapis.com/auth/drive.file',
                    'https://www.googleapis.com/auth/drive.readonly',
                    'https://www.googleapis.com/auth/spreadsheets',
                    'https://www.googleapis.com/auth/spreadsheets.readonly'],
        'security_scheme_name': 'Oauth2',
        'source_description_id': 'default',
        'type': 'oauth2'},
        {'api_title': 'Google Sheets API',
        'auth_urls': {'authorization': 'https://accounts.google.com/o/oauth2/auth',
                        'token': 'https://accounts.google.com/o/oauth2/token'},
        'description': 'Oauth 2.0 accessCode authentication',
        'flow_type': 'authorizationCode',
        'name': 'Oauth2c',
        'required': True,
        'scopes': ['https://www.googleapis.com/auth/drive',
                    'https://www.googleapis.com/auth/drive.file',
                    'https://www.googleapis.com/auth/drive.readonly',
                    'https://www.googleapis.com/auth/spreadsheets',
                    'https://www.googleapis.com/auth/spreadsheets.readonly'],
        'security_scheme_name': 'Oauth2c',
        'source_description_id': 'default',
        'type': 'oauth2'}]
    
    security_schemes = create_security_schemes_from_auth_requirements(auth_requirements)
    assert security_schemes == {
        'default': {
            'Oauth2': OAuth2Scheme(type=AuthType.OAUTH2,
                                   name='Oauth2',
                                   description='Oauth 2.0 implicit authentication',
                                   flows=OAuth2Flows(authorization_code=None,
                                                    implicit=ImplicitFlow(scopes={'https://www.googleapis.com/auth/drive': 'Scope: https://www.googleapis.com/auth/drive',
                                                                                'https://www.googleapis.com/auth/drive.file': 'Scope: https://www.googleapis.com/auth/drive.file',
                                                                                'https://www.googleapis.com/auth/drive.readonly': 'Scope: https://www.googleapis.com/auth/drive.readonly',
                                                                                'https://www.googleapis.com/auth/spreadsheets': 'Scope: https://www.googleapis.com/auth/spreadsheets',
                                                                                'https://www.googleapis.com/auth/spreadsheets.readonly': 'Scope: https://www.googleapis.com/auth/spreadsheets.readonly'},
                                                                                authorization_url=HttpUrl('https://accounts.google.com/o/oauth2/auth')),
                                   password=None,
                                   client_credentials=None)),
            'Oauth2c': OAuth2Scheme(type=AuthType.OAUTH2,
                                   name='Oauth2c',
                                   description='Oauth 2.0 accessCode authentication',
                                   flows=OAuth2Flows(authorization_code=AuthorizationCodeFlow(scopes={'https://www.googleapis.com/auth/drive': 'Scope: https://www.googleapis.com/auth/drive',
                                                                                                  'https://www.googleapis.com/auth/drive.file': 'Scope: https://www.googleapis.com/auth/drive.file',
                                                                                                  'https://www.googleapis.com/auth/drive.readonly': 'Scope: https://www.googleapis.com/auth/drive.readonly',
                                                                                                  'https://www.googleapis.com/auth/spreadsheets': 'Scope: https://www.googleapis.com/auth/spreadsheets',
                                                                                                  'https://www.googleapis.com/auth/spreadsheets.readonly': 'Scope: https://www.googleapis.com/auth/spreadsheets.readonly'},
                                                                                                  authorization_url=HttpUrl('https://accounts.google.com/o/oauth2/auth'),
                                                                                                  token_url=HttpUrl('https://accounts.google.com/o/oauth2/token'),
                                                                                                  refresh_url=None),
                                                    implicit=None,
                                                    password=None,
                                                    client_credentials=None))}}