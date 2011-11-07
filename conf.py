import os

data_dir = '~/.wl'
editor = 'gvim -f'
tags_label = 'TAGS:'

data_dir = os.path.expanduser(data_dir)

entries_dir = os.path.join(data_dir, 'entries')
diffs_dir = os.path.join(data_dir, 'diffs')
metadata_dir = os.path.join(data_dir, 'metadata')
