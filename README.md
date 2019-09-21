LabXchange Exporter
===================

This is a django app plugin for exporting OLX data from modulestore for use in Blockstore.

It spits out each block into OLX files (suitable for Blockstore import), and it uploads all static assets to S3.


## Installation

```
make studio-shell
cd /edx/src
git clone https://github.com/open-craft/lx-modulestore-exporter.git
pip install -e /edx/src/lx-modulestore-exporter
```

Then put

```
LX_EXPORTER_AWS_ACCESS_KEY_SECRET = "..."
LX_EXPORTER_CMS_TARGETS = {
    'studio.stage.example.com': {
        'lms_oauth2_url': 'https://courses.stage.example.com/oauth2',
        'oauth_key': '...',
        'oauth_secret': '...',
    }
}

```

into `cms/envs/private.py` (get the `LX_EXPORTER_AWS_ACCESS_KEY_SECRET` value from Vault, "IAM user for manually uploading to content.labxchange.org"). Set `oauth_key` and `oauth_secret` to the values of `DJANGO_LMS_API_AUTH_KEY` and `DJANGO_LMS_API_AUTH_SECRET` respectively.

## Usage

```
./manage.py cms export_block --block-key block-v1:...
```

## Usage (multiple blocks)

First:

```
from labxchange.apps.library.models import ItemMetadata
for row in ItemMetadata.objects.exclude(migration_id='').order_by('migration_id').values_list('migration_id', 'id'):
    print(f'{row[0]} {row[1]}')
```

Then save that into `/edx/src/lx-modulestore-exporter/out/id_list` and run:

```
./manage.py cms export_blocks
```

## Usage (pushing OLX to Blockstore)

```
./manage.py cms push_olx --cms-domain studio.stage.example.com
```
