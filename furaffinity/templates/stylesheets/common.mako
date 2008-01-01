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

