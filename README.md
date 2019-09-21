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
