"""
API client for connecting to Studio
"""
from __future__ import absolute_import, print_function, unicode_literals

import requests
from django.conf import settings
from oauthlib.oauth2 import BackendApplicationClient, TokenExpiredError
from requests_oauthlib import OAuth2Session

URL_LIB_PREFIX = '/api/libraries/v2/'
URL_LIB_CREATE = URL_LIB_PREFIX
URL_LIB_DETAIL = URL_LIB_PREFIX + '{lib_key}/'  # Get data about a library, update or delete library
URL_LIB_BLOCK_TYPES = URL_LIB_DETAIL + 'block_types/'  # Get the list of XBlock types that can be added to this library
URL_LIB_COMMIT = URL_LIB_DETAIL + 'commit/'  # Commit (POST) or revert (DELETE) all pending changes to this library
URL_LIB_BLOCKS = URL_LIB_DETAIL + 'blocks/'  # Get the list of XBlocks in this library, or add a new one
URL_LIB_BLOCK = URL_LIB_PREFIX + 'blocks/{block_key}/'  # Get data about a block, or delete it
URL_LIB_BLOCK_OLX = URL_LIB_BLOCK + 'olx/'  # Get or set the OLX of the specified XBlock

URL_BLOCK_RENDER_VIEW = '/api/xblock/v2/xblocks/{block_key}/view/{view_name}/'
URL_BLOCK_GET_HANDLER_URL = '/api/xblock/v2/xblocks/{block_key}/handler_url/{handler_name}/'


class StudioClient(object):
    """
    API client for Studio
    """

    def __init__(self, studio_url, config):
        self.studio_url = studio_url
        self.client_oauth_key = config['oauth_key']
        self.client_oauth_secret = config['oauth_secret']
        self.client = BackendApplicationClient(client_id=self.client_oauth_key)
        self.session = OAuth2Session(client=self.client)
        self.token_url = config['lms_oauth2_url'] + '/access_token'

    def refresh_session_token(self):
        """
        Refreshes the authenticated session with a new token.
        """
        # We cannot use lms_session.fetch_token() because it sends the client
        # credentials using HTTP basic auth instead of as POST form data.
        res = requests.post(self.token_url, data={
            'client_id': self.client_oauth_key,
            'client_secret': self.client_oauth_secret,
            'grant_type': 'client_credentials'
        })
        res.raise_for_status()
        data = res.json()
        self.session.token = {'access_token': data['access_token']}

    def api_call_raw(self, method, path, **kwargs):
        """
        Make a Studio API call and return the HTTP response.
        """
        url = self.studio_url + path
        try:
            response = self.session.request(method, url, **kwargs)
            if response.status_code == 401:
                raise TokenExpiredError
        except TokenExpiredError:
            self.refresh_session_token()
            response = self.session.request(method, url, **kwargs)
        return response

    def api_call(self, method, path, **kwargs):
        """
        Make an API call from Studio. Returns the parsed JSON response.
        """
        response = self.api_call_raw(method, path, **kwargs)
        response.raise_for_status()
        if response.status_code == 204:  # No content
            return None
        return response.json()

    def get_library_block_olx(self, block_key):
        """ Get the OLX of a specific block in a library """
        data = self.api_call('get', URL_LIB_BLOCK_OLX.format(block_key=block_key))
        return data["olx"]

    def set_library_block_olx(self, block_key, new_olx):
        """ Overwrite the OLX of a specific block in the library """
        self.api_call('post', URL_LIB_BLOCK_OLX.format(block_key=block_key), json={"olx": new_olx})

    def commit_library_changes(self, lib_key):
        """ Commit changes to an existing library """
        self.api_call('post', URL_LIB_COMMIT.format(lib_key=lib_key))
