from bbcode import *

parser = BBcodeParser()
parser.tag_handlers['b'] = Bold()
parser.tag_handlers['i'] = Italic()
parser.tag_handlers['u'] = Underline()
parser.tag_handlers['s'] = Strike()
parser.tag_handlers['quote'] = Quote()
parser.tag_handlers['url'] = URL()
parser.tag_handlers['code'] = Code()

parser_long = BBcodeParser() # for use with [cut] tags
parser_long.tag_handlers.update(parser.tag_handlers)
parser_long.tag_handlers['cut'] = Cut()

parser_short = BBcodeParser() # for use with [cut] tags
parser_short.tag_handlers.update(parser.tag_handlers)
parser_short.tag_handlers['cut'] = Cut(False)
