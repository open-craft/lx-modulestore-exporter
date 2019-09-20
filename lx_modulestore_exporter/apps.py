# -*- coding: utf-8 -*-
"""
lx_modulestore_exporter Django application initialization.
"""

from __future__ import absolute_import, unicode_literals

from django.apps import AppConfig

from openedx.core.djangoapps.plugins.constants import PluginSettings, ProjectType, SettingsType


class LxModulestoreExporterAppConfig(AppConfig):
    """
    Configuration for the lx_modulestore_exporter Django plugin application.

    See: https://github.com/edx/edx-platform/blob/master/openedx/core/djangoapps/plugins/README.rst
    """

    name = 'lx_modulestore_exporter'
    plugin_app = {
        PluginSettings.CONFIG: {
            ProjectType.LMS: {
                SettingsType.COMMON: {PluginSettings.RELATIVE_PATH: 'settings'},
                SettingsType.PRODUCTION: {PluginSettings.RELATIVE_PATH: 'settings'},
            },
            ProjectType.CMS: {
                SettingsType.COMMON: {PluginSettings.RELATIVE_PATH: 'settings'},
                SettingsType.PRODUCTION: {PluginSettings.RELATIVE_PATH: 'settings'},
            },
        },
    }

    def ready(self):
        """
        Load signal handlers when the app is ready.
        """
        pass
