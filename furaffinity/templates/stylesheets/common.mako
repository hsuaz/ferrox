/*** layout things that should never change ***/

#skip-to-content { display: none; }

/*** forms ***/

input[type='submit'], input[type='reset'], input[type='button'],
input[type='radio'], input[type='checkbox'] { cursor: pointer; }

/*** widgets ***/

/* admin controls */
.admin:before { content: '» '; color: #e87400; }
.admin:after  { content: ' «'; color: #e87400; }

/* inline link list */
ul.inline { margin: 0.25em 0; }
ul.inline li { display: inline; }
ul.inline li:before { content: '• '; }
ul.inline li:first-child:before { content: ''; }
ul.inline li.selected a { outline: 2px solid #919bad; -moz-outline-radius: 4px; }

/* usernames */
.userlink { position: relative; /* XXX breaks IE somehow */ }
.userlink a { font-weight: bold; }
.userlink a img { border: none; vertical-align: bottom; }
.userlink .popup { visibility: hidden; position: absolute; left: 0; z-index: 10; color: black; background: white; background: rgba(255, 255, 255, 0.9); border: 1px solid black; width: 15em; padding: 0.5em; }
.userlink .popup .avatar { float: right; height: 50px; }
.userlink .popup .name { font-weight: bold; }
.userlink .popup .role { font-size: 0.8em; font-style: italic; margin-bottom: 0.5em; }
.userlink .popup .rel { font-size: 0.8em; }
.userlink .popup .links { font-size: 0.8em; margin-top: 0.5em; }
.userlink .popup .online { color: white; background-color: rgb(0, 128, 0); background-color: rgba(0, 128, 0, 0.5); font-size: 0.75em; font-weight: bold; text-align: center; padding: 0.17em; margin: 0.5em -0.66em -0.66em -0.66em; }
.userlink .popup .offline { color: white; background-color: rgb(128, 0, 0); background-color: rgba(128, 0, 0, 0.5); font-size: 0.75em; font-weight: bold; text-align: center; padding: 0.17em; margin: 0.5em -0.66em -0.66em -0.66em; }
.userlink:hover .popup { visibility: visible; }

/* standard dl-based form */
dl.standard-form dt { float: left; position: relative; z-index: 2; width: 9.75em; padding: 0.25em 0 0 0.25em; line-height: 150%; font-style: italic; }
dl.standard-form dt:after { content: ':'; }
dl.standard-form dt img { vertical-align: middle; }
dl.standard-form:after,
dl.standard-form dd:after { content: 'v'; display: block; clear: left; visibility: hidden; height: 1px; margin-top: -1px; }
dl.standard-form dd { position: relative; z-index: 1; padding: 0.25em 0 0.25em 10em; margin: 0; }
/* IE has a horrible float model */
/* See http://www.howtocreate.co.uk/wrongWithIE/?chapter=Float+Model */
dl.standard-form dd { ~padding-left: 0.25em; }

/* remove before release */
#PLACEHOLDER { border: 3px double #c04040; color: #c04040; font-weight: bold; font-size: 1.67em; padding: 0.5em; text-align: center; }