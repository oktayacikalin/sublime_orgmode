import os

from abstract import AbstractLinkResolver


class Resolver(AbstractLinkResolver):
    '''
    @todo: If the link is a local org-file open it directly via sublime, otherwise use OPEN_LINK_COMMAND.
    '''

    def expand_path(self, filepath):
        filepath = os.path.expandvars(filepath)
        filepath = os.path.expanduser(filepath)

        drive, filepath = os.path.splitdrive(filepath)
        if not filepath.startswith('/'):  # If filepath is relative...
            cwd = os.path.dirname(self.view.file_name())
            testfile = os.path.join(cwd, filepath)
            if os.path.exists(testfile):  # See if it exists here...
                filepath = testfile

        return ':'.join([drive, filepath]) if drive else filepath

    def replace(self, content):
        content = self.expand_path(content)
        return content
