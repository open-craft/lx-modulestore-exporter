"""
Logic for exporting an XBlock from Open edX as OLX
"""
from __future__ import absolute_import, print_function, unicode_literals

import json
import logging
import os

from django.utils.translation import gettext as _

from . import compat
from .block_serializer import XBlockSerializer

log = logging.getLogger(__name__)


def export_data(root_block_key, out_dir):
    """
    Transfer the given block (and its children) to Blockstore.

    Args:
    * block_key: usage key of the Open edX block to transfer
    * bundle_uuid: UUID of the destination block
    * collection_uuid: UUID of the destination collection
      If no bundle_uuid provided, then a new bundle will be created here and that becomes the destination bundle.
    """
    log.info(root_block_key)

    # Step 1: Serialize the XBlocks to OLX files + static asset files

    serialized_blocks = {}  # Key is each XBlock's original usage key

    def serialize_block(block_key):
        """ Inner method to recursively serialize an XBlock to OLX """
        if block_key in serialized_blocks:
            return

        block = compat.get_block(block_key)
        serialized_blocks[block_key] = XBlockSerializer(block)

        if block.has_children:
            for child_id in block.children:
                serialize_block(child_id)

    serialize_block(root_block_key)

    root_block = compat.get_block(root_block_key)

    out_dir = os.path.join(out_dir, root_block_key.block_type) + '-' + root_block_key.block_id + '/'
    if not os.path.isdir(out_dir):
        os.mkdir(out_dir)

    # For each XBlock that we're exporting:
    for data in serialized_blocks.values():
        if data.orig_block_key == root_block_key:
            olx_path = out_dir + 'definition-1.xml'
        else:
            olx_path = out_dir + 'definition-{}.xml'.format(data.def_id.replace('/', '-'))
        with open(olx_path, 'wb') as fh:
            log.info(" -> " + olx_path)
            fh.write(data.olx_str)

        for asset_file in data.static_files:
            print("Uploading static asset file to S3: {}".format(asset_file.name))
            # TODO: upload asset_file.data to S3, ensure OLX is rewritten

    log.info("  ")
