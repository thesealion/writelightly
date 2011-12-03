# WriteLightly
WriteLightly is a console based personal journal/diary manager that uses the
curses library to build a minimalistic user interface. It features an
interactive calendar, support for tags, edit history for each entry and more.

Diary entries are date-based - you can create one entry for one day. To write
entries you can use your favorite editor (I use Vim, for example) which will
be invoked each time you need to create a new entry or edit an existing one.
After editing the difference between the old version and the new one (if any)
along with the time of modification will be saved.

To use tags, include a line of comma-delimited words prepended by a label.
Default label is **TAGS:** (can be changed in the configuration file).
For example:
> TAGS: flowers, waterfalls

## Installation
`python setup.py install`

Then you can use `wl` to run WriteLightly.

## Usage
* `wl` - show a calendar for the current month
* `wl today` - open up editor to edit the entry for today
* `wl 2011-01-01` - open up editor to edit the entry for 1 January 2011
* `wl -t` - show a list of all tags ever used
* `wl -t flowers` - show a list of entries for tag "flowers"

### Default keys
Calendar mode: use arrow keys and **hjkl** to move around, **H** and **L** to switch
months, **Enter** to edit the selected entry.
List mode: **down arrow**/**j**, **up arrow**/**k** to move down or up; **Ctrl-E**, **Ctrl-Y** to
scroll; **g**, **G** to go to bottom or top, **/** to search.

## Configuration
Configuration file is stored in `~/.writelightlyrc`. Default config is created by
setup.py. You can change there all key bindings used by the program and some
general options like the directory for storing data, external editor, etc.
