import re

enable_syntax_highlighting = True
try:
    import pygments
    import pygments.lexers
    import pygments.formatters
    
except ImportError:
    enable_syntax_highlighting = False


class BBcodeException:
    def __init__(self,text):
        self.text = text
        self.errors = []
        
    def __str__(self):
        return "BBcodeException: %s" % self.text

class BBcodeParser:

    def __init__(self, sanitizer=None):
        self.tag_handlers = {}
        self.param_sanitizer = re.compile(r'[^a-zA-Z0-9\"\'\ \-\_\;\&]')
        if sanitizer:
            self.output_sanitizer = sanitizer
        else:
            self.output_sanitizer = lambda x: BBcodeParser.default_output_sanitizer(x)

    @classmethod
    def default_output_sanitizer(cls, text):
        return text\
            .replace('&', '&amp;')\
            .replace('<', '&lt;')\
            .replace('>', '&gt;')\
            .replace('"', '&quot;')\
            .replace("\n", '<br>')\
            .replace("\r", '')
        
    def parse(self, text, offset=0):
        if offset == 0:
            self.errors = []
        output = ''
        left_tag_stack = []
        right_tag_stack = []
        remaining = text
        inhibit_bin = ''
        while '[' in remaining:
            out, remaining = remaining.split('[',1)
            output += self.output_sanitizer(out)
            offset += len(out) + 1
            params = ''
            tag = ''

            try:
                tag, remaining = remaining.split(']',1)
            except ValueError:
                self.errors.append(('found [ without corresponding ]', offset))
                output += '['
                continue
                #if dumb:
                #    output += '['
                #    continue
                #else:
                #    raise BBcodeException('found [ without corresponding ]')
            
            if '=' in tag:
                tag, params = tag.split('=',1)
                if self.tag_handlers[tag].sanitize_params:
                    params = self.param_sanitizer.sub('',params)
                    params.replace('&','&amp;')
                    params.replace('"','&quot;')

            #if '[' in tag and not dumb:
            #    raise BBcodeException('unexpected [')
            if '[' in tag:
                raise self.errors.append(('unexpected [', offset))

            close_tag = False
            if tag[0:1] == '/':
                tag = tag[1:]
                close_tag = True

            if not self.tag_handlers.has_key(tag):
                #if dumb:
                #    output += '[/' if close_tag else '['
                #    output += tag
                #    output += ("=%s]"%params) if params else ']'
                #    continue
                #else:
                #    raise BBcodeException("tag [%s] is unknown" % tag)
                output += '[/' if close_tag else '['
                output += tag
                output += ("=%s]"%params) if params else ']'
                raise self.errors.append(("tag [%s] is unknown" % tag, offset))
                continue
                
            if close_tag:
                while left_tag_stack and left_tag_stack[-1][0] != tag:
                    unordered_tag = left_tag_stack.pop()
                    output += self.tag_handlers[unordered_tag[0]].end(unordered_tag[0])
                    if self.tag_handlers[unordered_tag[0]].last_error:
                        self.errors.append((self.tag_handlers[unordered_tag[0]].last_error, offset))
                        self.tag_handlers[unordered_tag[0]].last_error = None
                    if not self.tag_handlers[unordered_tag[0]].dont_restart:
                        right_tag_stack.append(unordered_tag)
                if not left_tag_stack:
                    #if dumb:
                    #    output += "[/%s]" % tag
                    #elif self.tag_handlers[unordered_tag[0]].dont_restart:
                    #    raise BBcodeException("extraneous tag closure: [/%s] (possible nesting issue)"%tag)
                    #else:
                    #    raise BBcodeException("extraneous tag closure: [/%s]"%tag)
                    output += "[/%s]" % tag
                    if self.tag_handlers[unordered_tag[0]].dont_restart:
                        self.errors.append(("extraneous tag closure: [/%s] (possible nesting issue)"%tag, offset))
                    else:
                        self.errors.append(("extraneous tag closure: [/%s]"%tag, offset))

                left_tag_stack.pop()
                output += self.tag_handlers[tag].end(tag)
                if self.tag_handlers[tag].last_error:
                    self.errors.append((self.tag_handlers[tag].last_error, offset))
                    self.tag_handlers[tag].last_error = None
                right_tag_stack.reverse()
                for unordered_tag in right_tag_stack:
                    output += self.tag_handlers[unordered_tag[0]].start(unordered_tag[0], unordered_tag[1])
                    if self.tag_handlers[unordered_tag[0]].last_error:
                        self.errors.append((self.tag_handlers[unordered_tag[0]].last_error, offset))
                        self.tag_handlers[unordered_tag[0]].last_error = None
                    left_tag_stack.append(unordered_tag)
                right_tag_stack = []
                
            else:
                #if self.tag_handlers[tag].verify_close and not dumb:
                #    if "[/%s]" % tag not in remaining:
                #        raise BBcodeException("unclosed [%s] tag" % tag)
                if self.tag_handlers[tag].verify_close:
                    if "[/%s]" % tag not in remaining:
                        self.errors.append(("unclosed [%s] tag" % tag, offset))
                    
                if not self.tag_handlers[tag].no_close:
                    left_tag_stack.append((tag,params))
                output += self.tag_handlers[tag].start(tag, params)
                if self.tag_handlers[tag].last_error:
                    self.errors.append((self.tag_handlers[tag].last_error, offset))
                    self.tag_handlers[tag].last_error = None

                if self.tag_handlers[tag].inhibit_parse:
                    end_tag = remaining.find("[/%s]"%tag)
                    
                    inside = ''
                    if end_tag == -1:
                        #if self.tag_handlers[tag].verify_close and not dumb:
                        #    raise BBcodeException("unclosed [%s] tag (inhibiting tag)" % tag)
                        #else:
                        #    inside = remaining
                        #    remaining = ''
                        if self.tag_handlers[tag].verify_close:
                            self.errors.append(("unclosed [%s] tag (inhibiting tag)" % tag, offset))
                        inside = remaining
                        remaining = ''
                    else:
                        inside = remaining[0:end_tag]
                        remaining = remaining[end_tag:]

                    output += self.tag_handlers[tag].process_text(inside,lambda x: self.parse(x,offset=offset))
                    if self.tag_handlers[tag].last_error:
                        self.errors.append((self.tag_handlers[tag].last_error, offset))
                        self.tag_handlers[tag].last_error = None
                    offset += len(inside)
        
        output += self.output_sanitizer(remaining)
        left_tag_stack.reverse()
        for unclosed_tag in left_tag_stack:
            output += self.tag_handlers[unclosed_tag[0]].end(unclosed_tag[0])
            if self.tag_handlers[unclosed_tag[0]].last_error:
                self.errors.append((self.tag_handlers[unclosed_tag[0]].last_error, offset))
                self.tag_handlers[unclosed_tag[0]].last_error = None
                
        return output

class TagBase:
    no_close = False
    dont_restart = False
    verify_close = False
    sanitize_params = True
    inhibit_parse = False

    def __init__(self):
        self.last_error = None
        pass

    def start(self, name, params):
        if params:
            return "[%s=%s]" % (name, params)
        else:
            return "[%s]" % name

    def end(self, name):
        if self.no_close:
            return ''
        else:
            return "[/%s]" % name
            
    def process_text(self, text, parser_callback):
        # This function is only needed if you use inhibit_parse
        return ''

class Blank(TagBase):
    def start(self, name, params):
        return ''

    def end(self, name):
        return ''
            
class Bold(TagBase):
    def start(self, name, params):
        return '<strong>'

    def end(self, name):
        return '</strong>'

class Italic(TagBase):
    def start(self, name, params):
        return '<em>'

    def end(self, name):
        return '</em>'

class Underline(TagBase):
    def start(self, name, params):
        return '<u>'

    def end(self, name):
        return '</u>'

class Strike(TagBase):
    def start(self, name, params):
        return '<strike>'

    def end(self, name):
        return '</strike>'

class Quote(TagBase):
    dont_restart = True
    verify_close = True
    def start(self, name, params):
        if params:
            return "<div class=\"blockquote\"><em>Posted by: %s</em><br />" % params
        else:
            return '<div class=\"blockquote\">'

    def end(self, name):
        return '</div>'

class URL(TagBase):
    sanitize_params = False
    
    def __init__(self, sanitizer_callback=None):
        TagBase.__init__(self)
        if not sanitizer_callback:
            self.sanitizer_callback = lambda x: BBCodeParser.default_output_sanitizer(x)
        else:
            self.sanitizer_callback = sanitizer_callback
            
    def start(self, name, params):
        if params[0:10] == 'javascript':
            params = params[11:]
        
        if not params:
            self.last_error = 'no url provided for [url]'
            return '<a>'
        
        return "<a href=\"%s\">" % self.sanitizer_callback(params)

    def end(self, name):
        return '</a>'

class Cut(TagBase):
    inhibit_parse = True
    verify_close = True
    
    def __init__(self, show=True):
        self.show = show
        self.link = None
        TagBase.__init__(self)
        
    def start(self, name, params):
        if not self.show:
            if self.link:
                if params:
                    return """[[[ <a href="%s">%s</a> ]]]""" % (self.link, params)
                else:
                    return """[[[ <a href="%s">Read more</a> ]]]""" % self.link
            else:
                if params:
                    return "[[[ %s ]]]"%params
                else:
                    return '[[[ Read more ]]]'
        else:
            return ''
            
    def end(self, name):
        return ''
        
    def process_text(self, text, parser_callback):
        if self.show:
            return parser_callback(text)
        else:
            return ''

class Code(TagBase):
    inhibit_parse = True
    verify_close = True
    
    def __init__(self):
        self.params = ''
        TagBase.__init__(self)
    
    def start(self, name, params):
        self.params = params
        return "Code (%s):<br /><div style=\"border: 1px black solid; width: 80%%; font-family: monospace\">"%params
        
    def end(self, name):
        return '</div>'
        
    def process_text(self, text, parser_callback):
        if self.params and enable_syntax_highlighting:
            try:
                lexer = pygments.lexers.get_lexer_by_name(self.params)
            except pygments.util.ClassNotFound:
                pass
            else:
                formatter = pygments.formatters.get_formatter_by_name('html', noclasses=True)
                return pygments.highlight(text, lexer, formatter)
        
        return "<pre>%s</pre>"%text\
            .replace('&','&amp;')\
            .replace('<','&lt;')\
            .replace('>','&gt;')\
            .replace('"','&quot;')

if __name__ == '__main__':
    b = BBcodeParser()
    b.tag_handlers['b'] = Bold()
    b.tag_handlers['i'] = Italic()
    b.tag_handlers['u'] = Underline()
    b.tag_handlers['s'] = Strike()
    b.tag_handlers['quote'] = Quote()
    b.tag_handlers['url'] = URL()
    b.tag_handlers['cut'] = Cut()
    b.tag_handlers['code'] = Code()

    text = "[b]Head[/b]\n[cut][s]test[/s][/cut]\npart"
    print '-'*40
    print text
    print '-'*40
    print b.parse(text)
    print '-'*40
    b.tag_handlers['cut'].show = False
    print b.parse(text)
    print '-'*40
    
    text = "[code=php]\n<?php\necho 'hello [b]world[/b]';\n?>[/code]"
    print '-'*40
    print text
    print '-'*40
    print b.parse(text)
    print '-'*40
    
    text = "[code]\n<?php\necho 'hello [b]world[/b]';\n?>[/code]"
    print '-'*40
    print text
    print '-'*40
    print b.parse(text)
    print '-'*40
    
    print b.parse('[b]bold[/b] [u]underline[/u] [i]italic[/i] [s]strike[/s]')
    print b.errors
    print b.parse('[quote]Quote[/quote] [quote=source]Quote w/ Source[/quote]')
    print b.errors
    print b.parse('[url=http://www.google.com/]Link[/url]')
    print b.errors
    print b.parse('hit[b]he[i]r[/b]e[/i]')
    print b.errors
    print b.parse('[b][quote][/b]')
    print b.errors
