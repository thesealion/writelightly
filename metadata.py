import datetime
import os
import yaml

from writelightly.conf import Config
from writelightly.edit import get_edits
from writelightly.utils import lastday, format_size, format_date, format_time

conf = Config.general

class Metadata(object):
    """A collection of information about entries in a month.

    Stored on disk and updated when an entry is updated. Doesn't keep any
    important data, it's just a cache.
    """
    instances = {}

    def __init__(self, year, month):
        """Initialize with the given month and load data."""
        self.year, self.month = year, month
        self._dirty = False
        self.data = {}
        self.tags = {}
        self._load()

    @classmethod
    def get(cls, year, month):
        """Get an existing instance for month or create a new one."""
        k = (year, month)
        if k not in cls.instances:
            cls.instances[k] = cls(year, month)
        return cls.instances[k]

    @classmethod
    def write_all(cls):
        """Synchronize all existing instances with the filesystem."""
        for obj in cls.instances.values():
            obj.write()

    def get_path(self):
        """Get path to the file with metadata for this month."""
        return os.path.join(conf['metadata_dir'], '%d-%d' % (self.year, self.month))

    def _load(self):
        """Load data from a file saved earlier or directly from entries."""
        try:
            with open(self.get_path()) as f:
                loaded = yaml.load(f)
                self.data, self.tags = loaded['data'], loaded['tags']
        except IOError:
            for day in range(1, lastday(self.year, self.month) + 1):
                self.load_day(day)
            self._load_tags()

    def get_data_for_day(self, day):
        """Return metadata for the given day."""
        try:
            return self.data[day]
        except KeyError:
            return None

    def load_day(self, day):
        """Read an entry and load metadata for it."""
        date = datetime.date(self.year, self.month, day)
        month_dir = os.path.join(conf['entries_dir'], date.strftime('%Y-%m'))
        path = os.path.join(month_dir, date.strftime('%d'))

        lines, words, tags = 0, 0, []
        try:
            with open(path) as f:
                for line in f:
                    if not line.strip():
                        continue
                    if line.startswith(conf['tags_label']):
                        tags += [b.strip() for b in
                            line[len(conf['tags_label']):].split(',')]
                        continue
                    lines += 1
                    words += len(line.split())
        except IOError:
            pass
        else:
            self.data[day] = [lines, words, tags, int(os.path.getsize(path)),
                              self._get_edits(day)]
            self._dirty = True

    def _get_edits(self, day):
        """Get edits in a format suitable for storing with metadata."""
        date = datetime.date(self.year, self.month, day)
        edits = get_edits(date)
        if edits:
            data = [edits[0][0]] # creation time
            if len(edits) > 1:   # include last edit time and number of edits
                data += [edits[-1][0], len(edits) - 1]
            return data

    def _load_tags(self):
        """Generate tag dictionary for month.

        It is stored to be able to faster retrieve entries for given tag.
        """
        self.tags = {}
        for day, data in self.data.items():
            lines, words, tags, size, edits = data
            for tag in tags:
                try:
                    self.tags[tag].append(day)
                except KeyError:
                    self.tags[tag] = [day]

    def write(self):
        """Write metadata to disk if it has changed since the last sync."""
        try:
            os.mkdir(conf['metadata_dir'])
        except OSError:
            pass
        if self._dirty:
            self._load_tags()
            with open(self.get_path(), 'w') as f:
                yaml.dump({'data': self.data, 'tags': self.tags}, f)
            self._dirty = False

    def text(self, day):
        """Get a textual representation of metadata for an entry."""
        data = self.get_data_for_day(day)
        output = [format_date(datetime.date(self.year, self.month, day))]
        tags = edits_info = None
        try:
            lines, words, tags, size, edits = data
        except TypeError:
            m = 'No entry for selected date'
        else:
            m = '%d lines, %d words, %s' % (lines, words, format_size(size))
            tags = ', '.join(tags)
            if edits:
                edits_info = 'Created: %s' % format_time(edits[0])
                try:
                    edits_info += ', edited %d times, last: %s' % (edits[2],
                        format_time(edits[1]))
                except IndexError:
                    pass
        output.append(m)
        if tags:
            output.append('Tags: %s' % tags)
        if edits_info:
            output.append(edits_info)
        return '\n'.join(output)
