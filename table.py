# encoding: utf-8

# NOTE Round border edges are not available in all fonts. E.g. on windows use "DejaVu Sans Mono" instead of "Consolas". "Menlo" on OSX works fine. Linux?

# TODO Hit tab on vert border to add column after cursor.
# TODO Hit tab on horiz border to add row below cursor.
# TODO Hit enter within field to insert linebreak in cell.
# TODO Hit ctrl+r to select complete row.
# TODO Hit ctrl+c to select complete col.
# TODO Hitting backspace or delete while having one or more complete rows selected should delete them.
# TODO Hitting backspace or delete while having one or more complete columns selected should delete them.
# TODO Hitting backspace at the end of a table should not delete the bottom right corner.
# TODO Having two tables right below each other should not merge them.

import os
import textwrap

# Uses asciitable for interpreting data.
# http://pypi.python.org/pypi/asciitable
# https://github.com/taldcroft/asciitable
# http://cxc.harvard.edu/contrib/asciitable/
from thirdparty import asciitable
reload(asciitable)

import sublime
import sublime_plugin


# Begin: Header table elements.
LINE_H_HEAD = u'═'  # Horizontal line.
LINE_H_T_HEAD = u'╤'  # Horizontal top join.
LINE_H_TL_HEAD = u'╒'  # Horizontal top left edge.
LINE_H_TR_HEAD = u'╕'  # Horizontal top right edge.
LINE_V_L_HEAD = u'│'  # Vertical left line.
LINE_V_HEAD = u'│'  # Vertical line.
LINE_V_HEAD_VALUE = u'%%-%ds'  # Value pattern.
LINE_V_HEAD_PADDING = u' %s ' # Padding pattern.
LINE_V_R_HEAD = u'│'  # Vertical right line.
LINE_H_L_HEAD = u'╞'  # Horizontal left join.
LINE_H_C_HEAD = u'╪'  # Horizontal center join.
LINE_H_R_HEAD = u'╡'  # Horizontal right join.
# End: Header table elements.

# Begin: Normal table elements.
LINE_H_NORM = u'─'  # Horizontal line.
LINE_H_T_NORM = u'┬'  # Horizontal top join.
LINE_H_TL_NORM = u'╭'  # Horizontal top left edge.
LINE_H_TR_NORM = u'╮'  # Horizontal top right edge.
LINE_V_L_NORM = u'│'  # Vertical left line.
LINE_V_NORM = u'│'  # Vertical line.
LINE_V_NORM_VALUE = u'%%-%ds'  # Value pattern.
LINE_V_NORM_PADDING = u' %s ' # Padding pattern.
LINE_V_R_NORM = u'│'  # Vertical right line.
LINE_H_L_NORM = u'├'  # Horizontal left join.
LINE_H_C_NORM = u'┼'  # Horizontal center join.
LINE_H_R_NORM = u'┤'  # Horizontal right join.
LINE_H_B_NORM = u'┴'  # Horizontal bottom join.
LINE_H_BL_NORM = u'╰'  # Horizontal bottom left edge.
LINE_H_BR_NORM = u'╯'  # Horizontal bottom right edge.
# End: Normal table elements.


class Table(object):

    def __init__(self):
        self.data = []
        self.num_rows = 0
        self.num_cols = 0
        self.cols = []
        self.headers = None

    def analyze(self):
        rows = 0
        cols = []
        for row in self.data:
            rows += 1
            for num, col in enumerate(row):
                if len(cols) <= num:
                    cols.append(0)
                for part in str(col).decode('utf8').split('\n'):
                    # print '1.', repr(part)
                    cols[num] = max(cols[num], len(part) + 2)
        self.num_rows = rows
        self.num_cols = len(cols)
        self.cols = cols

    def set_header(self, data):
        self.headers = data

    def extend(self, data):
        for row in data:
            self.data.append(row)

    def draw_header(self, line_h_norm, line_h_t_norm, line_h_tl_norm,
                    line_h_tr_norm):
        # Gather lines with length of each column.
        row = [line_h_norm * col for col in self.cols]
        # Join row together.
        row = line_h_t_norm.join(row)
        # Add edges and return it.
        return line_h_tl_norm + row + line_h_tr_norm

    def draw_header_header(self):
        content = self.draw_header(
            LINE_H_HEAD,
            LINE_H_T_HEAD,
            LINE_H_TL_HEAD,
            LINE_H_TR_HEAD,
        )
        return content

    def draw_body_header(self):
        content = self.draw_header(
            LINE_H_NORM,
            LINE_H_T_NORM,
            LINE_H_TL_NORM,
            LINE_H_TR_NORM,
        )
        return content

    def draw_data(self, cols, line_v_norm_padding, line_v_norm_value,
                  line_v_norm, line_v_l_norm, line_v_r_norm):
        padding_width = len(line_v_norm_padding % '')
        template = line_v_norm_padding % line_v_norm_value
        # Gather col data and pad by length of each column.
        row = []
        for pos, width in enumerate(self.cols):
            pattern = template % (width - padding_width)
            try:
                value = pattern % unicode(cols[pos], 'utf8')
            except IndexError:
                value = ' ' * (width - padding_width)
                value = pattern % value
            row.append(value)
        # Join row together.
        row = line_v_norm.join(row)
        # Add edges and return it.
        return line_v_l_norm + row + line_v_r_norm

    def draw_join(self, line_h_norm, line_h_c_norm, line_h_l_norm,
                  line_h_r_norm):
        # Gather lines with length of each column.
        row = [line_h_norm * col for col in self.cols]
        # Join row together.
        row = line_h_c_norm.join(row)
        # Add edges and return it.
        return line_h_l_norm + row + line_h_r_norm

    def draw_header_data(self, cols):
        content = self.draw_data(
            cols,
            LINE_V_HEAD_PADDING,
            LINE_V_HEAD_VALUE,
            LINE_V_HEAD,
            LINE_V_L_HEAD,
            LINE_V_R_HEAD,
        )
        return content

    def draw_body_data(self, cols):
        content = self.draw_data(
            cols,
            LINE_V_NORM_PADDING,
            LINE_V_NORM_VALUE,
            LINE_V_NORM,
            LINE_V_L_NORM,
            LINE_V_R_NORM,
        )
        return content

    def draw_header_join(self):
        content = self.draw_join(
            LINE_H_HEAD,
            LINE_H_C_HEAD,
            LINE_H_L_HEAD,
            LINE_H_R_HEAD,
        )
        return content

    def draw_body_join(self):
        content = self.draw_join(
            LINE_H_NORM,
            LINE_H_C_NORM,
            LINE_H_L_NORM,
            LINE_H_R_NORM,
        )
        return content

    def draw_body_footer(self):
        # Gather lines with length of each column.
        row = [LINE_H_NORM * col for col in self.cols]
        # Join row together.
        row = LINE_H_B_NORM.join(row)
        # Add edges and return it.
        return LINE_H_BL_NORM + row + LINE_H_BR_NORM

    def draw(self):
        self.analyze()
        # print self.num_rows, self.num_cols, self.cols
        content = []
        if self.headers:
            row = self.headers.names
            content.append(self.draw_header_header())
            content.append(self.draw_header_data(row))
            content.append(self.draw_header_join())
        else:
            content.append(self.draw_body_header())
        for row in self.data:
            lines = []
            for pos, col in enumerate(row):
                parts = str(col).split('\n')
                for row_, part in enumerate(parts):
                    if len(lines) - 1 < row_:
                        lines.append([])
                    while len(lines[row_]) - 1 < pos:
                        lines[row_].append('')
                        # print cur, len(lines[row_]), pos
                    lines[row_][pos] = part
            # print 'lines =', lines
            for line in lines:
                content.append(self.draw_body_data(line))
            content.append(self.draw_body_join())
        if self.data:
            content.pop()
        content.append(self.draw_body_footer())
        content = '\n'.join(content)
        return content


class ClipboardInputter(asciitable.BaseInputter):

    def split(self, content):
        lines = []
        quotechars = ['"', '\'']
        if content[-1] != '\n':
            content += '\n'
        while len(content):
            quotechar = None
            # print 'content part =', repr(content), len(content)
            for pos in range(0, len(content)):
                char = content[pos]
                if char in quotechars:
                    if quotechar is None:
                        quotechar = char
                    else:
                        quotechar = None
                if not quotechar and char == '\n':
                    part = content[:pos]
                    content = content[pos + 1:]
                    lines.append(part)
                    break
            if len(content) and quotechar:
                lines.append(content)
                content = ''
        # print 'lines =', repr(lines)
        return lines

    def get_lines(self, table):
        """Get the lines from the ``table`` input.
        
        :param table: table input
        :returns: list of lines
        """
        try:
            # print '***', repr(table)
            if type(table) is not list:
                lines = self.split(table)
            else:
                lines = table
            # print '***', repr(lines)
        except TypeError:
            try:
                # See if table supports indexing, slicing, and iteration
                table[0]
                table[0:1]
                iter(table)
                lines = table
            except TypeError:
                raise TypeError('Input "table" must be a string (filename or data) or an iterable')

        return self.process_lines(lines)


class ClipboardSplitter(asciitable.DefaultSplitter):
    pass
    # def process_line(self, line):
    #     if self.delimiter == '\s':
    #         line = asciitable._replace_tab_with_space(line, self.escapechar, self.quotechar)
    #     return line  # Do not strip whitespace.


class AbstractTableCommand(sublime_plugin.TextCommand):

    def dedent_content(self, content):
        content = textwrap.dedent(content)
        return content

    def indent_content(self, content, init_indent, sub_indent=None):
        rows = []
        for num, row in enumerate(content.split('\n')):
            if num == 0 or sub_indent is None:
                indent = init_indent
            else:
                indent = sub_indent
            rows.append('%s%s' % (indent, row))
        return '\n'.join(rows)

    def tablerize_data(self, data):
        table = Table()
        table.extend(data)
        content = table.draw()
        return content

    def content_is_json(self, content):
        content = content.strip()
        startswith = content.startswith
        endswith = content.endswith
        edgy = startswith('[') and endswith(']')
        curly = startswith('{') and endswith('}')
        return edgy or curly

    def switch_quotes(self, content):
        from string import maketrans
        transtab = maketrans('"\'', '\'"')
        # print 'transtab =', repr(transtab)
        return content.encode('utf8').translate(transtab)

    def convert_json_to_tabular(self, content):
        # print 'LOOKS LIKE JSON:', repr(content)
        import json
        import re
        try:
            content = json.loads(content)
        except ValueError, excp:
            if str(excp).startswith('Expecting object'):
                content = self.switch_quotes(content)
                # print 'content =', content
                try:
                    content = json.loads(content)
                except ValueError, excp:
                    if str(excp).startswith('Expecting object'):
                        pattern = r'.*\(char (?P<char>\d+)\)$'
                        match = re.match(pattern, str(excp))
                        # print match
                        if match:
                            pos = int(match.group('char'))
                            pos -= 1
                            # JSON doesn't like trailing commas so we try to
                            # find and remove it. See if that helps...
                            while pos >= 0 and content[pos] in (' ', '\t', '\n', '\r'):
                                pos -= 1
                            if content[pos] == ',':
                                content = content[:pos] + content[pos + 1:]
                                # print 'content =', content
                                content = json.loads(content)
            else:
                raise
        result = []
        # Convert object into flat data.
        if type(content) is list:
            for item in content:
                if type(item) is list:
                    result.append([unicode(col) for col in item])
                else:
                    result.append([unicode(item)])
        elif type(content) is dict:
            for key, val in content.iteritems():
                result.append([unicode(key), unicode(val)])
        else:
            raise Exception('Expected dict or list for JSON decoding.')
        # Convert flat data into table.
        for pos, row in enumerate(result):
            result[pos] = '\t'.join(row)
        result = '\n'.join(result)
        # print 'result =', repr(result)
        return result

    def generate_table_from_content(self, content):
        if os.linesep not in content:
            if os.path.exists(content):
                content = file(content).read()
        if os.linesep not in content:
            content += os.linesep
        try:
            if self.content_is_json(content):
                content = self.convert_json_to_tabular(content)
            org_content = content.encode('utf8')
            # print repr(org_content)
            content = asciitable.read(org_content, Reader=asciitable.NoHeader, data_start=0, delimiter='\t', Inputter=ClipboardInputter, header_Splitter=ClipboardSplitter)
            if len(content.dtype.names) < 2:
                content = asciitable.read(org_content, Reader=asciitable.NoHeader, data_start=0, delimiter=':', Inputter=ClipboardInputter)
            if len(content.dtype.names) < 2:
                content = asciitable.read(org_content, Reader=asciitable.NoHeader, data_start=0, delimiter=';', Inputter=ClipboardInputter)
        except Exception, excp:
            name = type(excp).__name__
            sublime.error_message('%s: %s' % (name, excp))
            raise
        # print type(content)
        content = self.tablerize_data(content)
        return content

    def parse_table_from_content(self, content):
        content = content.splitlines()
        # print content
        data = []
        row_data = []
        for row in content:
            # print 'row =', row.encode('utf8')
            row = row.strip()
            lchar, rchar = row[0], row[-1]
            # Top header.
            if LINE_H_TL_NORM == lchar and LINE_H_TR_NORM == rchar:
                continue
            # Bottom header.
            if LINE_H_BL_NORM == lchar and LINE_H_BR_NORM == rchar:
                continue
            # Row separator.
            if LINE_H_L_NORM == lchar and LINE_H_R_NORM == rchar:
                data.append(row_data)
                row_data = []
                continue
            # Row data.
            if LINE_V_L_NORM == lchar and LINE_V_R_NORM == rchar:
                # Drop left and right lines.
                row = row[1:-1]
                # print 'row =', repr(row)
                # Split into columns.
                if row[1] == LINE_V_L_NORM:
                    row = [row]  # Don't destroy recursive tables.
                    sublime.status_message('Orgmode table detected in clipboard. Won\'t split columns.')
                else:
                    row = row.split(LINE_V_NORM)
                row = [col.strip() for col in row]
                # print row
                # Put everything into row_data.
                if not row_data:  # Generate new row_data.
                    row_data = row
                else:  # Add more to existing row_data.
                    for pos, col in enumerate(row):
                        if len(col.strip()):
                            row_data[pos] += u'\n%s' % col
                continue
            msg = 'Syntax error: Subsequent lines of orgmode tables have to start and end with boundary chars. Line found:\n%s' % row
            sublime.error_message(msg)
            raise Exception(msg)
        if row_data:  # Is there something left to put in?
            data.append(row_data)
        # print data
        return data

    def find_content_point(self, cur):
        view = self.view
        rowcol = view.rowcol
        text_point = view.text_point
        match_selector = view.match_selector
        if match_selector(cur, 'border.header'):
            row, col = rowcol(cur)
            cur = text_point(row + 1, col)
        if match_selector(cur, 'border.row.separator'):
            row, col = rowcol(cur)
            if not match_selector(text_point(row + 1, col), 'border.row.separator'):
                cur = text_point(row + 1, col)
            if not match_selector(text_point(row - 1, col), 'border.row.separator'):
                cur = text_point(row - 1, col)
        if match_selector(cur, 'border.footer'):
            row, col = rowcol(cur)
            cur = text_point(row - 1, col)
        while match_selector(cur, 'border.row.data.pre.space'):
            row, col = rowcol(cur)
            col += 1
            cur = text_point(row, col)
        while match_selector(cur, 'border.row.data.post.space'):
            row, col = rowcol(cur)
            col -= 1
            cur = text_point(row, col)
        while match_selector(cur, 'border.row.data'):
            row, col = rowcol(cur)
            if col > 0:
                col -= 1
            else:
                break
            cur = text_point(row, col)
        while match_selector(cur, 'border.row.data'):
            row, col = rowcol(cur)
            col += 1
            cur = text_point(row, col)
        if match_selector(cur, 'border'):
            return False
        if not match_selector(cur, 'orgmode.table'):
            return False
        return cur

    def find_table_boundaries(self, cur):
        view = self.view
        extract_scope = view.extract_scope
        scope_name = view.scope_name
        line = view.line
        rowcol = view.rowcol
        text_point = view.text_point
        scope = scope_name(cur)
        # print scope
        if scope.startswith('orgmode.table.simple'):
            row, col = rowcol(cur)
            length = len(line(text_point(row, 0)))
            cur = text_point(row, length)
            scope = scope_name(cur)
        if 'orgmode.table.simple' in scope:
            while 'orgmode.table.simple' in scope and 'border.header' not in scope:
                row, col = rowcol(cur)
                row -= 1
                length = len(line(text_point(row, 0)))
                cur = text_point(row, length)
                scope = scope_name(cur)
            cur = extract_scope(cur).begin()
            begin = cur
            while 'orgmode.table.simple' in scope and 'border.footer' not in scope:
                row, col = rowcol(cur)
                row += 1
                length = len(line(text_point(row, 0)))
                cur = text_point(row, 0)
                scope = scope_name(cur)
            cur = extract_scope(cur).end()
            end = cur
            sel = sublime.Region(begin, end)
            # print sel
        # print scope
        return sel


class OrgmodePasteTableFromClipboardCommand(AbstractTableCommand):

    def get_indent(self, content):
        import re
        pattern = '^([\t ]*)'
        match = re.match(pattern, content)
        if match is None:
            return ''
        else:
            return match.group(1)

    def run(self, edit):
        content = sublime.get_clipboard()
        indent = self.get_indent(content)
        has_eol = content[-1] == '\n'
        # Dedent content.
        content = self.dedent_content(content)
        # print content
        content = self.generate_table_from_content(content)
        # print repr(content)
        # Now replace selections.
        rowcol = self.view.rowcol
        for sel in self.view.sel():
            if sel.empty():
                row, col = rowcol(sel.begin())
                indent = ' ' * col
                data = self.indent_content(content, indent)
                if col:
                    data = data.lstrip()
            else:
                data = content
                row, col = rowcol(sel.begin())
                if indent:
                    # print repr(indent), col, len(indent)
                    subindent = indent
                    if col:
                        subindent += ' ' * col
                    data = self.indent_content(content, indent, subindent)
                else:
                    indent = ' ' * col
                    data = self.indent_content(content, '', indent)
            if has_eol:
                data += '\n'
            self.view.replace(edit, sel, data)


class OrgmodeCopyTableIntoClipboardCommand(AbstractTableCommand):

    def run(self, edit, format='tab'):
        sels = self.view.sel()
        cur = sels[0].begin()
        cur = self.find_content_point(cur)
        if not cur:
            sublime.status_message('Table has no content!')
            return
        # print cur
        region = self.find_table_boundaries(cur)
        # print region
        content = self.view.substr(region)
        # print content.encode('utf8')
        data = self.parse_table_from_content(content)
        # print data
        num_rows = len(data)
        if format == 'tab':
            format = 'tab separated'
            # Escape problematic columns with double quotes.
            for row in data:
                for pos, col in enumerate(row):
                    if u'\n' in col or u'\t' in col:
                        row[pos] = u'"%s"' % col
            # Join columns into tab separated string.
            data = [u'\t'.join(row) for row in data]
            # Join rows with newlines.
            data = u'\n'.join(data)
        elif format == 'json':
            format = 'JSON encoded'
            import json
            data = json.dumps(data)
        elif format == 'csv':
            format = 'CSV encoded'
            import csv
            from cStringIO import StringIO
            fh = StringIO()
            writer = csv.writer(fh)
            for row in data:
                writer.writerow(row)
            fh.seek(0)
            data = fh.read()
        else:
            msg = 'Invalid format specified. Choices are: tab, json'
            sublime.error_message(msg)
            raise Exception(msg)
        # print repr(data)
        sublime.set_clipboard(data)
        sublime.status_message('Copied table with %d rows as %s data into the clipboard.' % (num_rows, format))


class OrgmodeUpdateTableCommand(AbstractTableCommand):

    def run(self, edit):
        view = self.view
        substr = view.substr
        parse_table_from_content = self.parse_table_from_content
        tablerize_data = self.tablerize_data
        rowcol = view.rowcol
        indent_content = self.indent_content
        text_point = view.text_point
        sel_bak = []
        sels = view.sel()
        updated = 0
        for sel in sels:
            begin = rowcol(sel.begin())
            end = rowcol(sel.end())
            sel_bak.append((begin, end))
        for sel in sels:
            begin = rowcol(sel.begin())
            end = rowcol(sel.end())
            cur = sel.begin()
            cur = self.find_content_point(cur)
            if not cur:
                print 'Table without content found! Not updated.'
                continue
            sel = self.find_table_boundaries(cur)
            begin = rowcol(sel.begin())
            end = rowcol(sel.end())
            region = sel

            content = substr(region)
            org_content = content
            # print content.encode('utf8')
            indent = content.index(LINE_H_TL_NORM)
            data = parse_table_from_content(content)
            # print data
            data = [u'\t'.join(row).encode('utf8') for row in data]
            # print repr(data)

            try:
                content = asciitable.read(data, Reader=asciitable.Tab, data_start=0, delimiter='\t', Inputter=ClipboardInputter, guess=False)
                # print repr(content)
            except Exception, excp:
                name = type(excp).__name__
                sublime.error_message('%s: %s' % (name, excp))
                raise

            content = tablerize_data(content)
            # print content.encode('utf8')

            row, col = rowcol(region.begin())
            # print row, col, repr(indent)
            init_indent = ' ' * indent
            sub_indent = ' ' * (col + indent)
            # print repr(init_indent), repr(sub_indent)
            content = indent_content(content, init_indent, sub_indent)
            content += '\n'
            # print content.encode('utf8')
            if content != org_content:
                view.replace(edit, region, content)
                updated = True
        # Restore selections.
        sels.clear()
        for begin, end in sel_bak:
            sels.add(sublime.Region(text_point(*begin),text_point(*end)))
        if updated:
            sublime.status_message('Updated %d tables.' % updated)
        else:
            sublime.status_message('Nothing to update.')


class OrgmodeTableInputObserver(sublime_plugin.EventListener):

    def check(self, view):
        sels = view.sel()
        settings = view.settings()
        command_mode_enabled = False
        org_mode = bool(settings.get('command_mode', False))
        match = view.match_selector
        for sel in sels:
            found = False
            for x in range(sel.begin(), sel.end() + 1):
                if match(x, 'orgmode.table.simple border'):
                    # print sel
                    found = True
                    break
            if found:
                command_mode_enabled = True
                break
        if command_mode_enabled != org_mode:
            if command_mode_enabled:
                print 'Enabled command mode.'
            else:
                print 'Disabled command mode.'
            settings.set('command_mode', command_mode_enabled)

    def on_selection_modified(self, view):
        if view.match_selector(0, 'text.orgmode'):
            self.check(view)

    def on_activated(self, view):
        if view.match_selector(0, 'text.orgmode'):
            self.check(view)

    # Disabled - causes problems with undo history.
    # def on_modified(self, view):
    #     sel = view.sel()[0]
    #     if not view.match_selector(sel.end(), 'text.orgmode orgmode.table.simple'):
    #         return
    #     if not view.match_selector(sel.end(), 'border'):
    #         view.run_command('orgmode_update_table')


class OrgmodeTableBlockedCommand(sublime_plugin.TextCommand):

    def run(self, edit):
        pass


class OrgmodeAddColToTableCommand(AbstractTableCommand):

    def run(self, edit):
        pass


class OrgmodeAddRowToTableCommand(AbstractTableCommand):

    def run(self, edit):
        pass


class OrgmodeInspectTable(AbstractTableCommand):

    def run(self, edit):
        print 'Inspect'