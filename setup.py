from distutils.core import setup

import os
home_dir = os.path.expanduser('~')

setup(
    name='WriteLightly',
    version='0.1.0',
    author='Sergey Morozov',
    author_email='sealion@charadeyouare.org',
    packages=['writelightly', 'writelightly.tests'],
    py_modules=['diff_match_patch'],
    scripts=['wl'],
    url='http://writelightly.com/',
    description='Console based personal journal/diary manager.',
    data_files=[(home_dir, ['.writelightlyrc'])]
)
