"""
Logic for exporting an XBlock from Open edX as OLX
"""
from __future__ import absolute_import, print_function, unicode_literals

import json
import logging

from django.utils.translation import gettext as _

from . import compat
from .block_serializer import XBlockSerializer

log = logging.getLogger(__name__)


def export_data(root_block_key):
    """
    Transfer the given block (and its children) to Blockstore.

    Args:
    * block_key: usage key of the Open edX block to transfer
    * bundle_uuid: UUID of the destination block
    * collection_uuid: UUID of the destination collection
      If no bundle_uuid provided, then a new bundle will be created here and that becomes the destination bundle.
    """

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

    # # Step 2: Create a bundle and draft to hold the incoming data:
    # if bundle_uuid is None:
    #     log.debug('Creating bundle')
    #     bundle_data = create_bundle(
    #         collection_uuid=collection_uuid,
    #         title=getattr(root_block, 'display_name', root_block_key),
    #         slug=root_block_key.block_id,
    #         description=_("Transferred to Blockstore from Open edX {block_key}").format(block_key=root_block_key),
    #     )
    #     bundle_uuid = bundle_data["uuid"]
    # log.debug('Creating "%s" draft to hold incoming files', BUNDLE_DRAFT_NAME)
    # draft_data = create_draft(
    #     bundle_uuid=bundle_uuid,
    #     name=BUNDLE_DRAFT_NAME,
    #     title="OLX imported via lx-modulestore-exporter",
    # )
    # bundle_draft_uuid = draft_data['uuid']

    # # Step 3: Upload files into the draft

    # manifest = {
    #     'schema': BUNDLE_SCHEMA_VERSION,
    #     'type': _bundle_type(root_block_key.block_type),
    #     'assets': [],
    #     'components': [],
    #     'dependencies': [],
    # }

    # # For each XBlock that we're exporting:
    # for data in serialized_blocks.values():
    #     # Add the OLX to the draft:
    #     folder_path = '{}/'.format(data.def_id)
    #     path = folder_path + 'definition.xml'
    #     log.info('Uploading {} to {}'.format(data.orig_block_key, path))
    #     add_file_to_draft(bundle_draft_uuid, path, data.olx_str)
    #     manifest['components'].append(path)
    #     # If the block depends on any static asset files, add those too:
    #     for asset_file in data.static_files:
    #         asset_path = folder_path + 'static/' + asset_file.name
    #         add_file_to_draft(bundle_draft_uuid, asset_path, asset_file.data)
    #         manifest['assets'].append(asset_path)

    # # Commit the manifest file. TODO: do we actually need this?
    # add_file_to_draft(bundle_draft_uuid, 'bundle.json', json.dumps(manifest, ensure_ascii=False))

    # # Step 4: Commit the draft
    # commit_draft(bundle_draft_uuid)
    # log.info('Finished import into bundle {}'.format(bundle_uuid))
