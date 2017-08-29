#!/usr/bin/env python3
"""Module provides parser to convert BYOND interface .dmf format to json."""
import collections
import json


def to_ints(string: str, delimiter: str):
    """Extract values separated by `delimiter` and return them as ints in tuple

    Args:
        string (str):
        delimiter (str):
    Returns:
        tuple of ints
    Examples:
        >>> to_ints('3,4,5', ',')
        (3, 4, 5)
        >>> to_ints('20x50', 'x')
        (20, 50)
    """
    return tuple(map(int, string.split(delimiter)))

DEFAULT_VALUES_MAP = {
    'none': None,
    'false': False,
    'true': True,
}

DELIMITER_MAP = {
    'anchor1': ',',
    'anchor2': ',',
    'pos': ',',
    'size': 'x',
    'cell_span': 'x',
    'cells': 'x',
    'current_cell': 'x',
}


class DMFParser:
    """Parser of BYOND interface .dmf format to json."""
    def __init__(self, input_filename: str, output_filename: str = 'byond.json'):
        self.input_filename = input_filename
        self.output_filename = output_filename
        self.macrolists = []
        self.menubars = []
        self.windows = []
        self.category = None
        self.element = None

    @staticmethod
    def _parse_key_value(string: str):
        """Parse string containing key and (optionaly quote-surrounded)
        value separated by space

        Args:
            string (str): must contain one or two space-separated values
        Returns:
            (key, value) if `string` contained two space-separated values
            (key, None) otherwise
        Examples:
            >>> DMFParser._parse_key_value('eyes "blue"')
            ('eyes', 'blue')
            >>> DMFParser._parse_key_value('mouth')
            ('mouth', None)
        """
        if ' ' in string:
            key, value = string.split()
            value = value.strip('"')
        else:
            key, value = string, None
        return key, value

    @staticmethod
    def _parse_key_eq_sign_value(string: str):
        """Parse string containing key and (optionaly quote-surrounded)
        value separated by ' = '

        Args:
            string (str): must contain two ' = '-separated values
        Returns:
            (key, value)
        Examples:
            >>> DMFParser._parse_key_eq_sign_value('eyes = "blue"')
            ('eyes', 'blue')
        """
        key, value = string.split(' = ')
        return key, value.strip('"')

    def _parse_category(self, line: str):
        category_type, category_id = self._parse_key_value(line)

        self.category = collections.OrderedDict()
        self.category['type'] = category_type
        if category_id:
            self.category['id'] = category_id
        self.category['controls'] = []

        if category_type == 'macro':
            self.macrolists.append(self.category)
        elif category_type == 'menu':
            self.menubars.append(self.category)
        elif category_type == 'window':
            self.windows.append(self.category)

    def _parse_element(self, line: str):
        line = line.lstrip()
        element_type, element_id = self._parse_key_value(line)

        self.element = collections.OrderedDict()
        self.element['type'] = element_type
        if element_id:
            self.element['id'] = element_id
        self.category['controls'].append(self.element)

    def _parse_attribute(self, line: str):
        line = line.lstrip()
        name, value = self._parse_key_eq_sign_value(line)
        name = name.replace('-', '_')
        value = value.replace('-', '_')
        value = value.strip('\n"')
        if value in DEFAULT_VALUES_MAP:
            value = DEFAULT_VALUES_MAP[value]
        elif name in DELIMITER_MAP:
            delimiter = DELIMITER_MAP[name]
            value = to_ints(value, delimiter)
        elif value.isdigit():
            value = int(value)
        elif name == 'saved_params':
            value = value.split(';')

        if name == 'type':
            if value == 'MAIN':
                value = 'WINDOW'
            self.element['type'] = value
        else:
            self.element[name] = value

    def parse_file(self, filename: str):
        """Parse dmf file, results will be saved in macrolists, menubars and
        windows attributes of `self` object.
        """
        with open(filename) as file:
            for line in file:
                line = line.rstrip()
                if not line:
                    continue
                if line.startswith('\t\t'):
                    self._parse_attribute(line)
                elif line.startswith('\t'):
                    self._parse_element(line)
                else:
                    self._parse_category(line)

        for window in self.windows:
            element = window['controls'][0]
            if 'is_pane' in element:
                is_pane = element.pop('is_pane')
                if is_pane:
                    element['type'] = 'PANE'

    def post_process(self):
        """Change structure of stored data to more friendly form"""
        for macrolist in self.macrolists:
            macrolist['type'] = 'MACROLIST'
            macrolist['macros'] = macrolist.pop('controls')
            for macro in macrolist['macros']:
                macro['type'] = 'MACRO'

        for menubar in self.menubars:
            categories = collections.OrderedDict()
            menus = menubar.pop('controls')
            groups = set()
            for menu in menus:
                if 'category' not in menu:
                    menu['type'] = 'MENU'
                    menu['actions'] = []
                    if 'command' in menu:
                        menu.pop('command')
                    if 'saved_params' in menu:
                        menu.pop('saved_params')
                    categories[menu['name']] = menu
                else:
                    category_name = menu.pop('category')
                    if category_name not in categories:
                        categories[category_name] = {
                            'name': category_name,
                            'command': '',
                            'saved_params': 'is_checked',
                            'actions': [],
                        }

                    if menu.get('name'):
                        menu['type'] = 'ACTION'
                        if menu.get('group'):
                            groups.add(menu['group'])
                    else:
                        menu = {'type': 'SEPARATOR'}

                    categories[category_name]['actions'].append(menu)

            menubar['type'] = 'MENUBAR'
            menubar['menus'] = list(categories.values())
            menubar['groups'] = list(groups)

        for i, window in enumerate(self.windows):
            controls = window['controls']
            true_window = controls.pop(0)
            true_window['controls'] = controls
            self.windows[i] = true_window

    def parse(self):
        self.parse_file(self.input_filename)
        self.post_process()

    def save_json(self):
        """Creates new json file named `self.output_filename` with parsed cntent from
        dmf file named `self.input_filename`"""

        with open(self.output_filename, 'w') as file:
            file.write(self.to_json())

    def to_json(self):
        """Generate json from parsed dmf file

        Returns:
            json containing parsed data
        """
        return json.dumps(
            [
                self.macrolists,
                self.menubars,
                self.windows
            ],
            indent=4
        )


if __name__ == '__main__':
    parser = DMFParser(input_filename='byond.dmf', output_filename='byond.json')
    parser.parse()
    parser.save_json()
