import os
import subprocess
import re

import sublime
import sublime_plugin


OPEN_LINK_COMMAND = ['open']


class OrgmodeOpenLinkCommand(sublime_plugin.TextCommand):
    '''
    @todo: If the link is a local org-file open it via sublime, otherwise use OPEN_LINK_COMMAND.
    @todo: Implement mechanisms for Linux and Windows.
    '''

    def run(self, edit):
        view = self.view
        for sel in view.sel():
            if 'orgmode.link' not in view.scope_name(sel.end()):
                continue
            region = view.extract_scope(sel.end())
            content = view.substr(region)
            if content.startswith('[[') and content.endswith(']]'):
                content = content[2:-2]
            content = os.path.expandvars(content)
            content = os.path.expanduser(content)
            cmd = OPEN_LINK_COMMAND + [content]
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = process.communicate()
            if stdout:
                sublime.status_message(stdout)
            if stderr:
                sublime.error_message(stderr)


class OrgmodeCycleInternalLinkCommand(sublime_plugin.TextCommand):

    def run(self, edit):
        view = self.view
        sels = view.sel()
        sel = sels[0]
        if 'orgmode.link.internal' not in view.scope_name(sel.end()):
            return
        region = view.extract_scope(sel.end())
        content = view.substr(region).strip()
        found = self.view.find(content, region.end(), sublime.LITERAL)
        if not found:  # Try wrapping around buffer.
            found = self.view.find(content, 0, sublime.LITERAL)
        same = region.a == found.a and region.b == found.b
        if not found or same:
            sublime.status_message('No sibling found for: %s' % content)
            return
        sels.clear()
        sels.add(sublime.Region(found.begin()))
        try:
            import show_at_center_and_blink
            view.run_command('show_at_center_and_blink')
        except ImportError:
            view.show_at_center(found)


class AbstractCheckboxCommand(sublime_plugin.TextCommand):

    def __init__(self, *args, **kwargs):
        super(AbstractCheckboxCommand, self).__init__(*args, **kwargs)
        indent_pattern = r'^(\s*).*$'
        summary_pattern = r'(\[\d*[/]\d*\])'
        self.indent_regex = re.compile(indent_pattern)
        self.summary_regex = re.compile(summary_pattern)

    def get_indent(self, content):
        if type(content) is sublime.Region:
            content = self.view.substr(content)
        match = self.indent_regex.match(content)
        indent = match.group(1)
        return indent

    def find_parent(self, region):
        view = self.view
        row, col = view.rowcol(region.begin())
        line = view.line(region)
        content = view.substr(line)
        # print content
        indent = self.get_indent(content)
        # print repr(indent)
        row -= 1
        found = False
        while row >= 0:
            point = view.text_point(row, 0)
            line = view.line(point)
            content = view.substr(line)
            if len(content.strip()):
                cur_indent = self.get_indent(content)
                if len(cur_indent) < len(indent):
                    found = True
                    break
            row -= 1
        if found:
            # print row
            point = view.text_point(row, 0)
            line = view.line(point)
            return line

    def find_child(self, region):
        view = self.view
        row, col = view.rowcol(region.begin())
        line = view.line(region)
        content = view.substr(line)
        # print content
        indent = self.get_indent(content)
        # print repr(indent)
        row += 1
        found = False
        last_row, _ = view.rowcol(view.size())
        while row <= last_row:
            point = view.text_point(row, 0)
            line = view.line(point)
            content = view.substr(line)
            if len(content.strip()):
                cur_indent = self.get_indent(content)
                if len(cur_indent) > len(indent):
                    found = True
                    break
            row += 1
        if found:
            # print row
            point = view.text_point(row, 0)
            line = view.line(point)
            return line

    def find_siblings(self, child, parent):
        view = self.view
        row, col = view.rowcol(parent.begin())
        parent_indent = self.get_indent(parent)
        child_indent = self.get_indent(child)
        # print '***', repr(parent_indent), repr(child_indent)
        siblings = []
        row += 1
        last_row, _ = view.rowcol(view.size())
        while row <= last_row:  # Don't go past end of document.
            line = view.text_point(row, 0)
            line = view.line(line)
            content = view.substr(line)
            # print content
            if len(content.strip()):
                cur_indent = self.get_indent(content)
                if len(cur_indent) <= len(parent_indent):
                    # print 'OUT'
                    break  # Indent same as parent found!
                if len(cur_indent) == len(child_indent):
                    # print 'MATCH'
                    siblings.append((line, content))
            row += 1
        return siblings

    def get_summary(self, line):
        view = self.view
        row, _ = view.rowcol(line.begin())
        content = view.substr(line)
        # print content
        match = self.summary_regex.search(content)
        if not match:
            return None
        # summary = match.group(1)
        # print repr(summary)
        # print dir(match), match.start(), match.span()
        col_start, col_stop = match.span()
        return sublime.Region(
            view.text_point(row, col_start),
            view.text_point(row, col_stop),
        )

    def recalc_summary(self, edit, parent, child):
        view = self.view
        # print parent, child
        summary = self.get_summary(parent)
        if not summary:
            return False
        children = self.find_siblings(view.line(child), parent)
        # print children
        num_children = len(children)
        checked_children = len(filter(lambda child: '[X]' in child[1], children))
        # print checked_children, num_children
        view.replace(edit, summary, '[%d/%d]' % (checked_children, num_children))
        return True


class OrgmodeToggleCheckboxCommand(AbstractCheckboxCommand):

    def run(self, edit):
        view = self.view
        backup = []
        for sel in view.sel():
            if 'orgmode.checkbox' not in view.scope_name(sel.end()):
                continue
            backup.append(sel)
            child = view.extract_scope(sel.end())
            content = view.substr(child)
            if '[X]' in content:
                content = content.replace('[X]', '[ ]')
            elif '[ ]' in content:
                content = content.replace('[ ]', '[X]')
            view.replace(edit, child, content)
            parent = self.find_parent(child)
            if parent:
                self.recalc_summary(edit, parent, child)
        view.sel().clear()
        for region in backup:
            view.sel().add(region)


class OrgmodeRecalcCheckboxSummaryCommand(AbstractCheckboxCommand):

    def run(self, edit):
        view = self.view
        backup = []
        for sel in view.sel():
            if 'orgmode.checkbox.summary' not in view.scope_name(sel.end()):
                continue
            backup.append(sel)
            summary = view.extract_scope(sel.end())
            parent = view.line(summary)
            child = self.find_child(parent)
            if child:
                self.recalc_summary(edit, parent, child)
        view.sel().clear()
        for region in backup:
            view.sel().add(region)
