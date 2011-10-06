import datetime
import os
import re
import subprocess
import sys
import tempfile

data_dir = '~/.wl'
editor = 'gvim -f'

def parse_date(date):
    if date == 'today':
        return datetime.date.today()
    if date == 'yesterday':
        return datetime.date.today() - datetime.timedelta(days=1)
    for p in ['(?P<year>\d{4})-(?P<month>\d{2})-(?P<day>\d{2})',
              '(?P<month>\d{2})/(?P<day>\d{2})/(?P<year>\d{4})',
              '(?P<day>\d{2}).(?P<month>\d{2}).(?P<year>\d{4})']:
        m = re.match(p, date)
        if m:
            d = m.groupdict()
            return datetime.date(int(d['year']), int(d['month']), int(d['day']))
    return None

if __name__ == '__main__':
    args = sys.argv[1:]
    date = parse_date(args[0] if args else 'today')
    if not date:
        print 'Usage: %s [<date>]' % sys.argv[0]
        sys.exit()

    filename = str(date)
    dir_path = os.path.expanduser(data_dir)
    if os.path.isfile(dir_path):
        print '%s is not a directory' % dir_path
        sys.exit()
    try:
        os.mkdir(dir_path)
    except OSError:
        pass

    path = os.path.join(dir_path, filename)
    if os.path.exists(path):
        with open(path) as f:
            content = f.read()
    else:
        content = ''

    _, tmpfn = tempfile.mkstemp(text=True)
    with open(tmpfn, 'w') as f:
        f.write(content)
    exit_code = subprocess.call('%s %s' % (editor, tmpfn), shell=True)

    with open(tmpfn) as f:
        new_content = f.read()

    with open(path, 'w') as f:
        f.write(new_content)

    os.remove(tmpfn)


