#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Tests for the `lx-modulestore-exporter` transfer_to_blockstore command.
"""
from __future__ import absolute_import, division, print_function, unicode_literals

from argparse import ArgumentError

import mock
from django.core.management import CommandError, call_command
from django.test import TestCase


class TransferToBlockstoreCommandTestCase(TestCase):
    """
    Tests for the transfer_to_blockstore command.
    """

    BLOCK_KEY = 'block-v1:edX+DemoX+Demo_Course+type@vertical+block@vertical_0270f6de40fc'

    INVALID_COLLECTION_UUID = 'invalid_bundle_uuid'
    INVALID_BUNDLE_UUID = 'invalid_bundle_uuid'

    COLLECTION_UUID = 'd3e311a8-b3a8-439d-a111-cc6cb99790e8'
    BUNDLE_UUID = '93fc9c6e-4249-4d57-a63c-b08be9f4fe02'

    def setUp(self):

        super(TransferToBlockstoreCommandTestCase, self).setUp()

        patch = mock.patch(
            'lx_modulestore_exporter.management.commands.transfer_to_blockstore.transfer_to_blockstore'
        )
        patch.start()

    def test_command(self):

        with self.assertRaisesRegexp(CommandError, 'argument --block-key is required'):
            call_command('transfer_to_blockstore')

        with self.assertRaisesRegexp(ArgumentError, 'Invalid block usage key'):
            call_command('transfer_to_blockstore', '--block-key', 'invalid_key')

        with self.assertRaisesRegexp(ArgumentError, 'Either collection OR bundle UUID is required'):
            call_command('transfer_to_blockstore', '--block-key', self.BLOCK_KEY)

        with self.assertRaisesRegexp(ArgumentError, 'Invalid bundle UUID'):
            call_command(
                'transfer_to_blockstore', '--block-key', self.BLOCK_KEY, '--bundle-uuid', self.INVALID_BUNDLE_UUID
            )

        with self.assertRaisesRegexp(ArgumentError, 'Invalid collection UUID'):
            call_command(
                'transfer_to_blockstore',
                '--block-key', self.BLOCK_KEY,
                '--collection-uuid', self.INVALID_COLLECTION_UUID,
            )

        call_command('transfer_to_blockstore', '--block-key', self.BLOCK_KEY, '--bundle-uuid', self.BUNDLE_UUID)
        call_command('transfer_to_blockstore', '--block-key', self.BLOCK_KEY, '--collection-uuid', self.COLLECTION_UUID)
