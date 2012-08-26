'''
Settings in Global.sublime-settings are:
- orgmode.open_link.resolver.testrail.pattern: See PATTERN_DEFAULT.
- orgmode.open_link.resolver.testrail.url: See URL_DEFAULT.
'''

import re

from abstract import AbstractRegexLinkResolver


PATTERN_SETTING = 'orgmode.open_link.resolver.testrail.pattern'
PATTERN_DEFAULT = r'^(testrail|test|t):(?P<issue>.+)$'
URL_SETTING = 'orgmode.open_link.resolver.testrail.url'
URL_DEFAULT = 'http://testrail.demo.de/index.php?/tests/view/%s'


class Resolver(AbstractRegexLinkResolver):

    def __init__(self, view):
        super(Resolver, self).__init__(view)
        get = self.settings.get
        pattern = get(PATTERN_SETTING, PATTERN_DEFAULT)
        self.regex = re.compile(pattern)
        self.url = get(URL_SETTING, URL_DEFAULT)

    def replace(self, match):
        return self.url % match.group('issue')
