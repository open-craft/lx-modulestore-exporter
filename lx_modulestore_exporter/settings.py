"""
Common settings for the lx-modulestore-exporter app.

See apps.py for details on how this sort of plugin configures itself for
integration with Open edX.
"""
from __future__ import absolute_import, division, print_function, unicode_literals

# Declare defaults: ############################################################

# BLOCKSTORE_API_URL = 'http://edx.devstack.blockstore:18250/api/v1/'

# Register settings: ###########################################################


def plugin_settings(settings):
    """
    Add our default settings to the edx-platform settings. Other settings files
    may override these values later, e.g. via envs/private.py.
    """
    pass
    #settings.BLOCKSTORE_API_URL = BLOCKSTORE_API_URL
