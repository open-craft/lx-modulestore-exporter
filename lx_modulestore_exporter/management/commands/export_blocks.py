"""
Export multiple blocks and their children as OLX. Reads 
"""
from __future__ import absolute_import, print_function, unicode_literals

import logging
import os
from argparse import ArgumentError
from uuid import UUID

from django.core.management.base import BaseCommand
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import UsageKey

from .export_block import dir_path
from ...export_data import export_data


class Command(BaseCommand):
    """
    export_blocks management command.
    """

    def __init__(self, *args, **kwargs):
        super(Command, self).__init__(*args, **kwargs)
        self.options = {}
        self.help = __doc__
        self.logger = logging.getLogger()
        self.args = {}

    def add_arguments(self, parser):
        """
        Add named arguments.
        """
        self.args['id_file'] = parser.add_argument(
            '--id-file',
            type=str,
            default='/edx/src/lx-modulestore-exporter/out/id_list',
            help=("File where the first word on each line is the ID of an XBlock to export")
        )
        self.args['out_dir'] = parser.add_argument(
            '--out-dir',
            type=dir_path,
            default='/edx/src/lx-modulestore-exporter/out',
            help='Directory to put the OLX output files'
        )

    def handle(self, *args, **options):
        """
        Validate the arguments, and start the transfer.
        """
        self.set_logging(options['verbosity'])

        with open(options['id_file'], 'r') as id_fh:
            block_key_list = [line.split()[0] for line in id_fh.readlines() if line.strip() and line.strip()[0] != '#']

        for block_key_str in block_key_list:
            block_key = UsageKey.from_string(block_key_str)
            export_data(root_block_key=block_key, out_dir=options['out_dir'])

    def set_logging(self, verbosity):
        """
        Set the logging level depending on the desired vebosity
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
