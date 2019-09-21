"""
Logic for exporting an XBlock from Open edX as OLX
"""
from __future__ import absolute_import, print_function, unicode_literals

import json
import logging
import os

from django.conf import settings
from django.utils.translation import gettext as _
import boto3
import botocore
import six

from . import compat
from .block_serializer import XBlockSerializer

log = logging.getLogger(__name__)


# Connect to AWS:
session = boto3.Session(
    aws_access_key_id=settings.LX_EXPORTER_AWS_ACCESS_KEY_ID,
    aws_secret_access_key=settings.LX_EXPORTER_AWS_ACCESS_KEY_SECRET,
)
s3 = session.resource('s3')
s3_bucket = s3.Bucket(settings.LX_EXPORTER_STATIC_FILES_BUCKET)


def s3_bucket_has_object(path):
    """
    Does our S3 bucket have the specified file/object/key?
    """
    try:
        s3_bucket.Object(path).load()
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == "404":
            # The object does not exist.
            return False
        else:
            # Something else has gone wrong.
            raise
    else:
        return True


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

    s3_path_prefix = (
        settings.LX_EXPORTER_STATIC_FILES_PATH + root_block_key.block_type + '-' + root_block_key.block_id + '/'
    )
    s3_url_prefix = 'https://' + settings.LX_EXPORTER_STATIC_FILES_BUCKET + '/' + s3_path_prefix
    # For each XBlock that we're exporting:
    for data in serialized_blocks.values():
        olx_str = data.olx_str

        for asset_file in data.static_files:
            dest_path = s3_path_prefix + asset_file.name
            if not s3_bucket_has_object(dest_path):
                print(" -> Uploading static asset file to S3: {} -> {}".format(asset_file.name, dest_path))
                s3_bucket.put_object(Key=dest_path, Body=asset_file.data)
            else:
                print(" -> already uploaded static asset {}".format(asset_file.name))
            dest_url = s3_url_prefix + asset_file.name
            olx_str = olx_str.replace('/static/' + asset_file.name, dest_url)
        
        if data.orig_block_key == root_block_key:
            olx_path = out_dir + 'definition-1.xml'
        else:
            olx_path = out_dir + 'definition-{}.xml'.format(data.def_id.replace('/', '-'))
        with open(olx_path, 'wb') as fh:
            log.info(" -> " + olx_path)
            fh.write(olx_str.encode('utf-8'))

    log.info("  ")
