import datetime
import yaml
import os
from utils import lastday, format_size, format_date
import conf

data_dir = os.path.expanduser(conf.data_dir)
metadata_dir = os.path.join(data_dir, 'metadata')

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

    @classmethod
    def write_all(cls):
        for obj in cls.instances.values():
            obj.write()

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
            self._load_tags()

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

    def text(self, day):
        data = self.get_data_for_day(day)
        output = [format_date(datetime.date(self.year, self.month, day))]
        try:
            m = '%(lines)d lines, %(words)d words, %(size)s' % (data)
            tags = ', '.join(data['tags'])
        except TypeError:
            m = 'No entry for selected date'
            tags = None
        output.append(m)
        if tags:
            output.append('Tags: %s' % tags)
        return '\n'.join(output)
