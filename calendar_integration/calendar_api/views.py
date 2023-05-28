from django.shortcuts import redirect
from django.conf import settings
from rest_framework.decorators import api_view
from rest_framework.response import Response
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
import os
import json


os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

SCOPE = ['https://www.googleapis.com/auth/calendar.readonly']
REDIRECT_URL = 'https://localhost:8000/rest/v1/calendar/redirect/'


@api_view(['GET'])
def GoogleCalendarInitView(request):
    flow = Flow.from_client_secrets_file(
        settings.GOOGLE_OAUTH_CLIENT_SECRET,
        scopes=SCOPE,
        redirect_uri = REDIRECT_URL
    )
    authorization_url, state = flow.authorization_url(
        access_type='offline',
    )
    request.session['state'] = state
    return Response({"authorization_url": authorization_url})


@api_view(['GET'])
def GoogleCalendarRedirectView(request):
    state = request.session['state']
    print(state)
    if state is None:
        return Response({"error": "State parameter missing."})

    flow = Flow.from_client_secrets_file(
        settings.GOOGLE_OAUTH_CLIENT_SECRET,
        scopes=SCOPE,
        state=state,
        redirect_uri=REDIRECT_URL
    )
    authorization_response = request.get_full_path()
    print(authorization_response)
    flow.fetch_token(authorization_response=authorization_response)
    credentials = flow.credentials
    request.session['credentials'] = credentials_to_dict(credentials)
    if 'credentials' not in request.session:
        return redirect('v1/calendar/init')
    credentials = Credentials(**request.session['credentials'])
    print(credentials.valid)
    service = build(
        'calendar', 'v3', credentials=credentials)
    calendar_list = service.calendarList().list().execute()
    calendar_id_list = [(item['id'], item['summary'])
                        for item in calendar_list['items']]
    events_list = []
    for x in calendar_id_list:
        events = service.events().list(
            calendarId=x[0], maxResults=10).execute()
        events_list.append({x[1]: events['items']})
    return Response(events_list)


def credentials_to_dict(credentials):
    return {'token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'token_uri': credentials.token_uri,
            'client_id': credentials.client_id,
            'client_secret': credentials.client_secret,
            'scopes': credentials.scopes}

