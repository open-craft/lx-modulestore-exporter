"""
Common settings for the lx-modulestore-exporter app.

See apps.py for details on how this sort of plugin configures itself for
integration with Open edX.
"""
from __future__ import absolute_import, division, print_function, unicode_literals

# Declare defaults: ############################################################

LX_EXPORTER_STATIC_FILES_BUCKET = 'content.labxchange.org'
LX_EXPORTER_STATIC_FILES_PATH = 'learning-item-assets/'
LX_EXPORTER_AWS_ACCESS_KEY_ID = 'AKIA6FHROMDTIHAZSHHW'
LX_EXPORTER_AWS_ACCESS_KEY_SECRET = 'set-me'

# Register settings: ###########################################################


def plugin_settings(settings):
    """
    Add our default settings to the edx-platform settings. Other settings files
    may override these values later, e.g. via envs/private.py.
    """
    settings.LX_EXPORTER_STATIC_FILES_BUCKET = LX_EXPORTER_STATIC_FILES_BUCKET
    settings.LX_EXPORTER_STATIC_FILES_PATH = LX_EXPORTER_STATIC_FILES_PATH
    settings.LX_EXPORTER_AWS_ACCESS_KEY_ID = LX_EXPORTER_AWS_ACCESS_KEY_ID
    settings.LX_EXPORTER_AWS_ACCESS_KEY_SECRET = LX_EXPORTER_AWS_ACCESS_KEY_SECRET
