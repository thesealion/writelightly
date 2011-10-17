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

def format_date(date):
    return '%s %d, %d' % (date.strftime('%B'), date.day, date.year)

class Metadata(object):
    instances = {}
    def __init__(self, year, month):
        self.year, self.month = year, month
        self._dirty = False
        self.data = {}
        self.tags = {}
        self._load()

    @classmethod
    def get(cls, year, month):
        k = (year, month)
        if k in cls.instances:
            return cls.instances[k]
        m = cls(year, month)
        cls.instances[k] = m
        return m

    def get_path(self):
        return os.path.join(metadata_dir, '%d-%d' % (self.year, self.month))

    def _load(self):
        try:
            with open(self.get_path()) as f:
                loaded = yaml.load(f)
                self.data, self.tags = loaded['data'], loaded['tags']
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
            self._dirty = True

    def _load_tags(self):
        self.tags = {}
        for day, data in self.data.items():
            for tag in data['tags']:
                try:
                    self.tags[tag].append(day)
                except KeyError:
                    self.tags[tag] = [day]

    def write(self):
        try:
            os.mkdir(metadata_dir)
        except OSError:
            pass
        if self._dirty:
            self._load_tags()
            with open(self.get_path(), 'w') as f:
                yaml.dump({'data': self.data, 'tags': self.tags}, f)
            self._dirty = False

    def show(self, day, window):
        data = self.get_data_for_day(day)
        window.clear()
        window.addstr(0, 0, format_date(datetime.date(self.year, self.month, day)))
        try:
            m = '%(lines)d lines, %(words)d words, %(size)s' % (data)
            tags = ', '.join(data['tags'])
        except TypeError:
            m = 'No entry for selected date'
            tags = None
        window.addstr(1, 0, m)
        if tags:
            window.addstr(2, 0, 'Tags: %s' % tags)
        window.refresh()
