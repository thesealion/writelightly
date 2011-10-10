import datetime
import yaml
import os

from calendar import lastday

import conf

data_dir = os.path.expanduser(conf.data_dir)
metadata_dir = os.path.join(data_dir, 'metadata')

def format_size(size):
    if size > 1024:
        kib = size // 1024 + (size % 1024) / 1024.0
        return ('%.2f' % kib).rstrip('0').rstrip('.') + ' KiB'
    return '%d B' % size


class Metadata(object):
    def __init__(self, year, month):
        self.year, self.month = year, month
        self.data = {}
        self._load()

    def get_path(self):
        return os.path.join(metadata_dir, '%d-%d' % (self.year, self.month))

    def _load(self):
        try:
            with open(self.get_path()) as f:
                self.data = yaml.load(f)
        except IOError:
            for day in range(1, lastday(self.year, self.month) + 1):
                self.load_day(day)

    def get_data_for_day(self, day):
        try:
            return self.data[day]
        except KeyError:
            return None

    def load_day(self, day):
        path = os.path.join(data_dir, str(datetime.date(self.year, self.month, day)))
        lines, words, tags = 0, 0, []
        try:
            with open(path) as f:
                for line in f:
                    if not line.strip():
                        continue
                    if line.startswith('TAGS:'):
                        tags += [b.strip() for b in line[5:].split(',')]
                        continue
                    lines += 1
                    words += len(line.split())
        except IOError:
            pass
        else:
            self.data[day] = {'lines': lines, 'words': words, 'tags': tags,
                              'size': format_size(os.path.getsize(path))}

    def write(self):
        try:
            os.mkdir(metadata_dir)
        except OSError:
            pass
        with open(self.get_path(), 'w') as f:
            yaml.dump(self.data, f)
