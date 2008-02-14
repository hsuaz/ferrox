/* fuck IE */
.thumbnail-grid { zoom: 1; }
.entry .header * { zoom: 1; }

a { font-weight: bold; text-decoration: none; color: ${c.colors['text']}; }
p { margin: 0.25em 0; line-height: 120%; }

body { background: ${c.colors['background']}; color: ${c.colors['text']}; font-family: Verdana, Helvetica, Bitstream Vera Sans, sans-serif; font-size: 10px /* blech */}

#error { background: darkred; }

/*** basic page layout ***/

#header { position: relative; padding: 0.25em; }
#user { float: right; text-align: right; }
#user form { margin-bottom: 1em; }
#user input { vertical-align: middle; }
#user #messages { position: absolute; right: 0; bottom: 0; padding: 0.25em; }
#user #messages li { margin: 0.25em 0; text-align: left; }
#user #messages li a { font-weight: normal; }
#user #messages li a img { margin-right: 3px; vertical-align: middle; }
#user #messages li.new a { font-weight: bold; font-size: 1.2em; }
#logo { height: 140px /* arbitrary banner size */; }

#navigation,
#ads { padding: 0.25em; float: left; width: 20em; }
#ads { clear: left; }
#ads li { text-align: center; }

#search form { padding-right: 5px /* 100% width textbox hack */; text-align: right; }
#search input[type='text'] { width: 100%; }

#error,
#content { position: relative; overflow: hidden /* new float clear context */; padding: 0.25em; }

#footer { padding: 0.25em; clear: both; text-align: center; border-top: 0.25em double ${c.colors['border']}; }
#shameless-whoring { position: absolute; left: 0.5em; }

/*** front page ***/
#left-column { float: left; width: 60%; }
#right-column { float: right; width: 39%; }


/*** widgets ***/

.basic-box { border: 1px solid ${c.colors['border']}; padding: 0.25em; }
.basic-box h2 { padding: 0.33em; margin-bottom: 0.25em; background: ${c.colors['border']}; color: ${c.colors['header_atop_border']}; font-weight: bold; }

/* journal/news entries */
.entry {}
.basic-box .entry { border-top: 1px solid ${c.colors['border']}; }
.entry .header { ~zoom: 1; }
.entry .header .title { float: right; margin-top: 0.25em; margin-bottom: 22px; font-size: 12px; font-weight: bold; }
.entry .header .avatar { float: left; margin-top: 14px; margin-left: 20px; border: solid ${c.colors['background']}; border-width: 2px; }
.entry .header .avatar img { vertical-align: bottom; }
.entry .header .author { clear: right; text-align: right; background: ${c.colors['border']}; color: ${c.colors['header_atop_border']}; }
.entry .header .date { text-align: right; background: ${c.colors['border']}; color: ${c.colors['header_atop_border']}; }
.entry .header .date:after { content: ''; display: block; clear: left; height: 0; background: ${c.colors['border']}; }
.entry .edit-header { padding: 0.25em; background: ${c.colors['border']}; }
.entry .edit-header .title { font-size: 12px; font-weight: bold; color: ${c.colors['header_atop_border']}; }
.entry .content { clear: both; margin: 0.25em; }

.entry.collapsed { padding: 0 0.5em; }
.entry.collapsed .header { padding: 0; }
.entry.collapsed .header .title { float: none; font-size: 1.33em; margin: 0; }
.entry.collapsed .header .title a { display: block; padding: 0.25em; }

/* thumbnail grid */
.thumbnail-grid .thumbnail { float: left; width: 120px; height: 120px; padding: 0.25em; margin: 1em; border: 1px solid ${c.colors['border']}; }
.thumbnail-grid:after { display: block; clear: both; visibility: hidden; content: 'vee was here'; height: 0; }

/* sub-link-bar */
.mini-linkbar { display: inline; margin-bottom: 0.5em; border: 1px solid ${c.colors['border']}; background: ${c.colors['border']}; ~zoom: 1; }
.mini-linkbar li { display: inline; }
.mini-linkbar li a { text-align: center; padding: 0.5em; }
.mini-linkbar li img { margin: 0 auto; vertical-align: middle; }
.mini-linkbar li:hover { background: ${c.colors['background_hover']}; }

/* basic-box linkbar, all in a row */
.micro-linkbar { background: ${c.colors['border']}; border-top: 1px dotted ${c.colors['border']}; zoom: 1; }
.micro-linkbar li { float: left; margin: 0 0.5em; }
.micro-linkbar li a { display: block; padding: 0.25em 0.5em; vertical-align: middle; line-height: 100%; }
.micro-linkbar li img { vertical-align: middle; }
.micro-linkbar li:hover { background: ${c.colors['background_hover']}; }
.micro-linkbar:after { display: block; clear: both; visibility: hidden; content: 'vee was here'; height: 0; }

