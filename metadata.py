import datetime
import os
import yaml

from writelightly import conf
from writelightly.edit import get_edits
from writelightly.utils import lastday, format_size, format_date, format_time

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
        if k not in cls.instances:
            cls.instances[k] = cls(year, month)
        return cls.instances[k]

    @classmethod
    def write_all(cls):
        for obj in cls.instances.values():
            obj.write()

    def get_path(self):
        return os.path.join(conf.metadata_dir, '%d-%d' % (self.year, self.month))

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
        date = datetime.date(self.year, self.month, day)
        month_dir = os.path.join(conf.entries_dir, date.strftime('%Y-%m'))
        path = os.path.join(month_dir, date.strftime('%d'))

        lines, words, tags = 0, 0, []
        try:
            with open(path) as f:
                for line in f:
                    if not line.strip():
                        continue
                    if line.startswith(conf.tags_label):
                        tags += [b.strip() for b in
                            line[len(conf.tags_label):].split(',')]
                        continue
                    lines += 1
                    words += len(line.split())
        except IOError:
            pass
        else:
            self.data[day] = {'lines': lines, 'words': words, 'tags': tags,
                              'size': format_size(os.path.getsize(path)),
                              'edits': self._get_edits(day)}
            self._dirty = True

    def _get_edits(self, day):
        date = datetime.date(self.year, self.month, day)
        edits = get_edits(date)
        if edits:
            data = [edits[0][0]] # creation time
            if len(edits) > 1: # include last edit time and number of edits if any
                data += [edits[-1][0], len(edits) - 1]
            return data

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
            os.mkdir(conf.metadata_dir)
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
            m = '%(lines)d lines, %(words)d words, %(size)s' % data
            tags = ', '.join(data['tags'])
            edits = 'Created: %s' % format_time(data['edits'][0])
            try:
                edits += ', edited %d times, last: %s' % (data['edits'][2],
                    format_time(data['edits'][1]))
            except IndexError:
                pass
        except (TypeError, KeyError):
            m = 'No entry for selected date'
            tags = edits = None
        output.append(m)
        if tags:
            output.append('Tags: %s' % tags)
        if edits:
            output.append(edits)
        return '\n'.join(output)
