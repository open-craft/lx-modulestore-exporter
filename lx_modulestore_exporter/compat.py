"""
Code used to interface with edx-platform.

This needs to be stubbed out for tests.  If a module, `caller` calls:

    from lx_modulestore_exporter import compat

It can be stubbed out using:

    import test_utils.compat
    mock.patch('caller.compat', test_utils.compat.StubCompat())

`StubCompat` is a class which implements all the below methods in a way that
eliminates external dependencies
"""
from __future__ import absolute_import, unicode_literals

import logging
import re

import six

LOG = logging.getLogger(__name__)


class EdXPlatformImportError(ImportError):
    """
    Custom exception class to explain ImportErrors from edx-platform code.
    """

    def __init__(self, import_error):
        """
        Construct a message from the given import_error's message.
        """
        message = 'Must run inside an edx-platform virtualenv: {}'.format(import_error.message)
        super(EdXPlatformImportError, self).__init__(message)


def get_block(usage_key):
    """
    Return block from the modulestore.
    """
    try:
        from xmodule.modulestore.django import modulestore as store
    except ImportError as exc:
        raise EdXPlatformImportError(exc)

    return store().get_item(usage_key)


def get_asset_content_from_path(course_key, asset_path):
    """
    Locate the given asset content, load it into memory, and return it.

    Returns None if the asset is not found.
    """
    try:
        from xmodule.contentstore.content import StaticContent
        from xmodule.assetstore.assetmgr import AssetManager
        from xmodule.modulestore.exceptions import ItemNotFoundError
        from xmodule.exceptions import NotFoundError
    except ImportError as exc:
        raise EdXPlatformImportError(exc)

    try:
        asset_key = StaticContent.get_asset_key_from_path(course_key, asset_path)
        return AssetManager.find(asset_key)
    except (ItemNotFoundError, NotFoundError) as exc:
        return None


def rewrite_absolute_static_urls(text, course_id):
    """
    Convert absolute URLs like
        https://studio-site.opencraft.hosting/asset-v1:LabXchange+101+2019+type@asset+block@SCI_1.2_Image_.png
    to the proper
        /static/SCI_1.2_Image_.png
    format for consistency and portability.
    """
    course_part = re.escape(six.text_type(course_id).replace('course-v1:', ''))
    asset_full_url_re = r'https?://[^/]+/asset-v1:' + course_part + '\+type@asset\+block@(?P<filename>[\w\-\. \+]+)'
    return re.sub(asset_full_url_re, r'/static/\g<filename>', text)


def collect_assets_from_text(text, course_id):
    """
    Yield dicts of asset content and path from static asset paths found in the given text.

    Make sure to have replaced the URLs with rewrite_absolute_static_urls first.
    """
    try:
        from static_replace import replace_static_urls
    except ImportError as exc:
        raise EdXPlatformImportError(exc)

    # Replace static urls like '/static/foo.png'
    static_paths = []
    replace_static_urls(text=text, course_id=course_id, static_paths_out=static_paths)
    for (path, uri) in static_paths:
        content = get_asset_content_from_path(course_id, path)
        if content is None:
            LOG.error("Static asset not found: (%s, %s)", path, uri)
        else:
            yield {'content': content, 'path': path}
