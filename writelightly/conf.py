from ConfigParser import SafeConfigParser
import os

home_dir = os.path.expanduser('~')

data_dir = os.path.join(home_dir, '.wl')

default_config = {
    'general': {
        'data_dir': data_dir,
        'editor': os.environ.get('EDITOR', os.environ.get('VISUAL', 'vim')),
        'tags_label': 'TAGS:',
        'color': True,
    },
}

default_keys = {
    'general': {
        'quit_mode': 'q',
        'quit': 'Q',
    },
    'calendar': {
        'left': ['h', 'KEY_LEFT'],
        'right': ['l', 'KEY_RIGHT'],
        'down': ['j', 'KEY_DOWN'],
        'up': ['k', 'KEY_UP'],
        'edit': ['e', '^J'],
        'tags': ['t'],
        'edits': ['d'],
        'next_month': ['L'],
        'prev_month': ['H'],
    },
    'tags': {
        'details': ['^J'],
    },
    'tag_details': {
        'edit': ['e', '^J'],
        'edits': ['d'],
    },
    'list': {
        'down': ['j', 'KEY_DOWN'],
        'up': ['k', 'KEY_UP'],

        'scroll_down': ['^E'],
        'scroll_up': ['^Y'],
        'page_down': ['^F', 'KEY_NPAGE'],
        'page_up': ['^B', 'KEY_PPAGE'],
        'halfpage_down': ['^D'],
        'halfpage_up': ['^U'],
        'top': ['g', 'KEY_HOME'],
        'bottom': ['G', 'KEY_END'],

        'search': ['/'],
        'find_next': ['n'],
        'find_prev': ['N'],
    },
    'edits': {
        'open': ['^J', 'o'],
    },
}

class ConfigManager(object):
    def __init__(self):
        self.config = default_config
        for section, params in default_keys.items():
            self.config['%s_keys' % section] = params

        cp = SafeConfigParser()
        cp.read(os.path.join(home_dir, '.writelightlyrc'))
        for section in cp.sections():
            for param, value in cp.items(section):
                if section not in self.config:
                    self.config[section] = {}
                value = self._process_value(section, value)
                self.config[section][param] = value
        self._add_dynamic_values()

    def _add_dynamic_values(self):
        section = self.general
        for label in ('entries', 'diffs', 'metadata'):
            dn = '%s_dir' % label
            if dn not in section:
                section[dn] = os.path.join(section['data_dir'], label)

    @staticmethod
    def _process_value(section, value):
        if section.endswith('_keys'):
            return value.split()
        if value in ('yes', 'no'):
            return value == 'yes'
        return value

    def __getattr__(self, name):
        try:
            return self.config[name]
        except KeyError:
            return object.__getattr__(self, name)

Config = ConfigManager()

