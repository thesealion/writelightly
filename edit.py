import os
import tempfile
import subprocess
import conf

data_dir = os.path.expanduser(conf.data_dir)

def edit_date(date):
    filename = str(date)
    if os.path.isfile(data_dir):
        print '%s is not a directory' % data_dir
        sys.exit()
    try:
        os.mkdir(data_dir)
    except OSError:
        pass

    path = os.path.join(data_dir, filename)
    if os.path.exists(path):
        with open(path) as f:
            content = f.read()
        new = False
    else:
        content = '\n'
        new = True

    _, tmpfn = tempfile.mkstemp(text=True)

    action = 'new entry' if new else 'editing entry'
    header = '#%s %d, %d: %s\n' % (date.strftime('%B'), date.day, date.year,
                                   action)
    with open(tmpfn, 'w') as f:
        f.write(header)
        f.write(content)
    exit_code = subprocess.call('%s %s' % (conf.editor, tmpfn), shell=True)

    with open(tmpfn) as f:
        new_content = f.read()
    if new_content.startswith(header):
        new_content = new_content.replace(header, '', 1)

    if new_content.strip():
        with open(path, 'w') as f:
            f.write(new_content)
    else:
        if os.path.exists(path):
            os.remove(path)

    os.remove(tmpfn)

