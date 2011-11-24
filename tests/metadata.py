import datetime
import os
import random
import shutil
import unittest

from writelightly import conf
from writelightly.metadata import Metadata
from writelightly.utils import lastday

class TestMetadata(unittest.TestCase):

    @staticmethod
    def _gen_name():
        chars = [chr(i) for i in range(97, 123)] + [str(i) for i in range(10)]
        return ''.join([random.choice(chars) for i in range(10)])

    @staticmethod
    def _gen_text():
        ri = random.randint
        signs = ('.', '!', '?', '...')
        def word():
            return ''.join(map(chr, [ri(97, 122) for i in range(ri(1, 8))]))
        def sentence():
            s = ' '.join(word() for i in range(ri(2, 12)))
            return s.capitalize() + random.choice(signs)
        def paragraph():
            return ' '.join(sentence() for i in range(ri(1, 6)))
        return '\n'.join(paragraph() for i in range(ri(10, 20)))

    def setUp(self):
        cd = os.path.dirname(os.path.abspath(__file__))
        test_dir = cd
        while os.path.exists(test_dir):
            test_dir = os.path.join(cd, self._gen_name())
        self.dir = test_dir
        conf.data_dir = test_dir
        conf.entries_dir = os.path.join(test_dir, 'entries')
        conf.metadata_dir = os.path.join(test_dir, 'metadata')

        today = datetime.date.today()
        start = datetime.date(today.year, today.month, 1)
        stop = datetime.date(today.year, today.month, lastday(today))
        month_dir = os.path.join(conf.entries_dir, today.strftime('%Y-%m'))
        os.makedirs(month_dir)
        while start <= stop:
            path = os.path.join(month_dir, start.strftime('%d'))
            with open(path, 'w') as f:
                f.write(self._gen_text())
            start += datetime.timedelta(days=1)

    def tearDown(self):
        shutil.rmtree(self.dir)

    def _check_entries(self, year, month, metadata, should_fail=[]):
        start = datetime.date(year, month, 1)
        stop = datetime.date(year, month, lastday(year, month))
        month_dir = os.path.join(conf.entries_dir, start.strftime('%Y-%m'))
        while start <= stop:
            path = os.path.join(month_dir, start.strftime('%d'))
            with open(path) as f:
                text = f.read()
            lines = [line for line in text.split('\n') if line.strip()]
            data = metadata.get_data_for_day(start.day)
            test = (self.assertNotEqual if start.day in should_fail
                else self.assertEqual)

            lines_from_data, words, tags, size, edits = data
            test(len(lines), lines_from_data)
            test(sum(len(line.split()) for line in lines), words)
            start += datetime.timedelta(days=1)

    def test_loading(self):
        today = datetime.date.today()
        m = Metadata(today.year, today.month)
        m.write()
        self._check_entries(today.year, today.month, m)

        date = datetime.date(today.year, today.month,
                             random.randint(1, lastday(today)))
        month_dir = os.path.join(conf.entries_dir, date.strftime('%Y-%m'))
        path = os.path.join(month_dir, date.strftime('%d'))
        with open(path) as f:
            lines = f.read().split('\n')
        lines.pop(random.randint(0, len(lines) - 1))
        with open(path, 'w') as f:
            f.write('\n'.join(lines))
        self._check_entries(today.year, today.month, m, [date.day])

        m.load_day(date.day)
        self._check_entries(today.year, today.month, m)

        m1 = Metadata(today.year, today.month)
        self._check_entries(today.year, today.month, m1, [date.day])

        m.write()
        m2 = Metadata(today.year, today.month)
        self._check_entries(today.year, today.month, m2)

if __name__ == '__main__':
    unittest.main()

