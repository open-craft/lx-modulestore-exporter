LabXchange Exporter
===================

This is a django app plugin for exporting OLX data from modulestore for use in Blockstore.

It spits out each block into OLX files (suitable for Blockstore import), and it uploads all static assets to S3.


## Installation

```
make studio-shell
pip install https://github.com/open-craft/lx-modulestore-exporter/archive/master.zip
```

Then put

```
LX_EXPORTER_AWS_ACCESS_KEY_SECRET = "..."
```

into `cms/envs/private.py` (get the value from Vault, "IAM user for manually uploading to content.labxchange.org").

## Usage

```
./manage.py cms export_block --out-dir ~/olx-exports --block-key block-v1:...
```

## Usage (multiple blocks)

First:

```
from labxchange.apps.library.models import ItemMetadata
for row in ItemMetadata.objects.exclude(migration_id='').values_list('migration_id', 'id'):
    print(f'{row[0]} {row[1]}')
```

Then save that into a file and run:

```
./manage.py cms export_blocks --out-dir /edx/src/lx-modulestore-exporter/out \
  --id-file /edx/src/lx-modulestore-exporter/out/id_list
```
