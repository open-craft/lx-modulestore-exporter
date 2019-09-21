"""
Export a block and its children as OLX
"""
from __future__ import absolute_import, print_function, unicode_literals

import logging
import os
from argparse import ArgumentError
from uuid import UUID

from django.core.management.base import BaseCommand
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import UsageKey

from ...export_data import export_data


def dir_path(string):
    """ Check that an argument is a valid directory """
    if os.path.isdir(string):
        return string
    else:
        raise ValueError("{} is not a directory".format(string))


class Command(BaseCommand):
    """
    export_block management command.
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
        self.args['block_key'] = parser.add_argument(
            '--block-key',
            type=str,
            required=True,
            help='Usage key of the source Open edX XBlock, '
                 'e.g., "block-v1:edX+DemoX+Demo_Course+type@html+block@030e35c4756a4ddc8d40b95fbbfff4d4"'
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
        try:
            block_key = UsageKey.from_string(options['block_key'])
        except InvalidKeyError:
            raise ArgumentError(message='Invalid block usage key', argument=self.args['block_key'])
 
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
