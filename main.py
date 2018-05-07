# Copyright 2016 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import urllib

from google.appengine.api import datastore, datastore_types
import requests
import webapp2

import httplib

def patch_http_response_read(func):
    def inner(*args):
        try:
            return func(*args)
        except httplib.IncompleteRead, e:
            return e.partial

    return inner

httplib.HTTPResponse.read = patch_http_response_read(httplib.HTTPResponse.read)

SPOTIFY_CLIENT_ID = 'f4b98baded8941af9e88ef500ef4af0b'
CALLBACK_URL = 'https://newagent-6f7b4.appspot.com/callback'
SCOPE = 'user-modify-playback-state'
TOKEN_URL = 'https://accounts.spotify.com/api/token'
ACCESS_TOKENS_DATASTORE_KIND = 'spotifyAccessTokens'
SPOTIFY_CREDENTIALS_DATASTORE_KIND = 'spotifyCredentials'
PROJECT_ID = 'newagent-6f7b4'


class Login(webapp2.RequestHandler):
    def get(self):
        user_id = self.request.get('user_id')
        redirect_url = 'https://accounts.spotify.com/authorize/?client_id={}&response_type=code' \
                       '&redirect_uri={}&scope={}&state={}'
        callback_url = urllib.quote(CALLBACK_URL, '')
        redirect_url = redirect_url.format(SPOTIFY_CLIENT_ID, callback_url, SCOPE, user_id)
        self.redirect(redirect_url)


class Callback(webapp2.RequestHandler):
    def get(self):
        auth_code = self.request.get('code')
        user_id = self.request.get('state')

        spotify_credentials_key = datastore_types.Key.from_path(
            kind=SPOTIFY_CREDENTIALS_DATASTORE_KIND,
            id_or_name='default')
        spotify_credentials_entity = datastore.Get(spotify_credentials_key)

        req_data = {
            'grant_type': 'authorization_code',
            'code': auth_code,
            'redirect_uri': CALLBACK_URL,
            'client_id': SPOTIFY_CLIENT_ID,
            'client_secret': spotify_credentials_entity['clientSecret']
        }
        req = requests.post(TOKEN_URL, req_data)
        resp = req.json()
        print(resp)

        entity = datastore.Entity(kind=ACCESS_TOKENS_DATASTORE_KIND, name=user_id)
        entity.update({'accessToken': resp['access_token']})
        datastore.Put(entity)

        self.response.write('OK')


app = webapp2.WSGIApplication([
    ('/login', Login),
    ('/callback', Callback),
], debug=True)
