"""
Push OLX to Blockstore
"""
from __future__ import absolute_import, print_function, unicode_literals

import logging
import os
import re
from argparse import ArgumentError
from uuid import UUID

from django.conf import settings
from django.core.management.base import BaseCommand
from lxml import etree
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import UsageKey
from requests.exceptions import HTTPError
import six

from .export_block import dir_path
from ...export_data import export_data
from ...studio_client import StudioClient


class Command(BaseCommand):
    """
    push_olx management command.
    """

    def __init__(self, *args, **kwargs):
        super(Command, self).__init__(*args, **kwargs)
        self.options = {}
        self.help = __doc__
        self.logger = logging.getLogger()
        self.args = {}
        self.studio_client = None

    def add_arguments(self, parser):
        """
        Add named arguments.
        """
        self.args['id_file'] = parser.add_argument(
            '--id-file',
            type=str,
            default='/edx/src/lx-modulestore-exporter/out/id_list',
            help=("File where the first each line has the modulestore and Blockstore block IDs")
        )
        self.args['olx_dir'] = parser.add_argument(
            '--olx-dir',
            type=dir_path,
            default='/edx/src/lx-modulestore-exporter/out',
            help='Directory to find the OLX input files'
        )
        self.args['cms_domain'] = parser.add_argument(
            '--cms-domain',
            type=str,
            required=True,
            help='CMS domain, e.g. studio.edx.org'
        )

    def handle(self, *args, **options):
        """
        Validate the arguments, and start the transfer.
        """
        self.set_logging(options['verbosity'])

        # Create an API client for interacting with Studio:
        self.studio_client = StudioClient(
            studio_url='https://' + options['cms_domain'],
            config=settings.LX_EXPORTER_CMS_TARGETS[options['cms_domain']],
        )

        # Verify that we can connect to Studio:
        response = self.studio_client.api_call('get', '/api/user/v1/me')
        print("Connecting to studio as {}".format(response["username"]))

        # Read in the list of IDs (each line is an old modulestore ID and the new blockstore ID)
        with open(options['id_file'], 'r') as id_fh:
            block_key_list = [line.split() for line in id_fh.readlines() if line.strip() and line.strip()[0] != '#']

        unhandled_items = [] # List of tuples of (old_key, new_key) for any items we can't do automatically

        # Upload the OLX file by file:
        for old_key_str, new_key_str in block_key_list:
            old_key = UsageKey.from_string(old_key_str)
            new_key = UsageKey.from_string(new_key_str)
            print("Processing {} ({})".format(old_key, new_key))

            olx_dir = os.path.join(options["olx_dir"], old_key.block_type + "-" + old_key.block_id)

            # Various cases:
            if old_key.block_type == 'vertical':
                # This is a vertical block. What kind of children does it have?

                def read_olx(filename):
                    with open(olx_dir + '/' + filename, 'r') as fh:
                        return fh.read()

                vertical_olx_str = read_olx('definition-1.xml')
                olx_root = etree.fromstring(vertical_olx_str)
                children_refs = [node.attrib["definition"] for node in olx_root.iter("xblock-include")]
                if len(children_refs) == 1:
                    # This vertical actually contains only a single block:
                    old_block_type, old_block_id = children_refs[0].split("/")
                    self.convert_and_upload_olx_file(
                        olx_dir, "definition-{}-{}.xml".format(old_block_type, old_block_id), old_block_type, new_key,
                    )
                else:
                    print(" -> can't handle this type, no known conversion")
                    unhandled_items.append((old_key, new_key))
            else:
                # This is a single block. Convert and upload it:
                result = self.convert_and_upload_olx_file(olx_dir, "definition-1.xml", old_key.block_type, new_key)
                if not result:
                    print(" -> can't handle this type, no known conversion")
                    unhandled_items.append((old_key, new_key))

        if unhandled_items:
            print("\n\nThe following items could not be migrated:")
            for old_key, new_key in unhandled_items:
                print("{} {}".format(old_key, new_key))

    def set_logging(self, verbosity):
        """
        Set the logging level depending on the desired verbosity
        """
        handler = logging.StreamHandler()
        root_logger = logging.getLogger('')
        root_logger.addHandler(handler)
        handler.setFormatter(logging.Formatter('%(levelname)s|%(message)s'))

        if verbosity == 1:
            self.logger.setLevel(logging.WARNING)
        elif verbosity == 2:
            self.logger.setLevel(logging.INFO)
        elif verbosity == 3:
            self.logger.setLevel(logging.DEBUG)
            handler.setFormatter(logging.Formatter('%(name)s|%(asctime)s|%(levelname)s|%(message)s'))

    def set_block_olx(self, block_key, new_olx):
        """
        Helper method for overwriting an XBlock's OLX

        new_olx can be an OLX string or an etree Element node
        """
        if not isinstance(new_olx, six.string_types):
            new_olx = etree.tostring(new_olx, encoding="utf-8", pretty_print=True)
        try:
            existing_olx = self.studio_client.get_library_block_olx(block_key)
        except HTTPError:
            # For some reason this is sometimes returning a 500? Maybe unicode-related?
            print(" -> Warning: 500 when trying to check existing OLX of {}".format(block_key))
            existing_olx = "unknown"
        if existing_olx.strip() != new_olx.strip():
            self.studio_client.set_library_block_olx(block_key, new_olx)
            self.studio_client.commit_library_changes(block_key.lib_key)
            print(" -> Updated OLX of {}".format(block_key))
        else:
            print(" -> No change to OLX of {}".format(block_key))

    def convert_and_upload_olx_file(self, olx_dir, olx_file, old_block_type, new_key):
        """
        Given a single OLX file (with no children), convert it if necessary from
        old_block_type to new_key.block_type and upload it to Blockstore (as
        new_key).

        Returns True if the block can be migrated and False otherwise
        """

        with open(olx_dir + '/' + olx_file, 'r') as fh:
            olx_string = six.text_type(fh.read(), encoding="utf-8")

        if old_block_type == new_key.block_type:
            if new_key.block_type in ('html', 'video', 'drag-and-drop-v2', 'problem'):
                self.set_block_olx(new_key, olx_string)
            else:
                raise NotImplementedError("Can't handle {} blocks yet.".format(new_key.block_type))
        elif new_key.block_type == 'lx_image' and old_block_type == 'html':
            # Convert from an HTML block to the new image block:
            try:
                image_url = re.search('src=[\'"](?P<img_url>[^\'"]+)[\'"]', olx_string).group('img_url')
            except AttributeError:
                raise ValueError("Unable to find image src in html block OLX")
            try:
                alt_text = re.search('alt=[\'"](?P<alt_text>[^\'"]+)[\'"]', olx_string).group('alt_text')
            except AttributeError:
                alt_text = ""
            olx_root = etree.fromstring(olx_string)
            display_name = olx_root.attrib["display_name"]
            olx_node_out = etree.Element("lx_image")
            olx_node_out.attrib["image_url"] = image_url
            olx_node_out.attrib["alt_text"] = alt_text
            olx_node_out.attrib["display_name"] = display_name
            print(" -> converting to image")
            self.set_block_olx(new_key, olx_node_out)
        elif new_key.block_type == 'lx_simulation' and old_block_type == 'html':
            # Convert from an HTML block to the new simulation block:
            try:
                sim_url = re.search('(src|href)=[\'"](?P<sim_url>[^\'"]+)[\'"]', olx_string).group('sim_url')
            except AttributeError:
                raise ValueError("Unable to find simulation src in html block OLX.")
            olx_root = etree.fromstring(olx_string)
            display_name = olx_root.attrib["display_name"]
            olx_node_out = etree.Element("lx_simulation")
            olx_node_out.attrib["simulation_url"] = sim_url
            olx_node_out.attrib["display_name"] = display_name
            print(" -> converting to simulation")
            self.set_block_olx(new_key, olx_node_out)
        else:
            return False
        return True
