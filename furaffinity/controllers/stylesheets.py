import logging

import formencode

from furaffinity.lib.base import *
import furaffinity.lib.paginate as paginate

from furaffinity.model import form

log = logging.getLogger(__name__)

class StylesheetsController(BaseController):

    duality_dark = '#2e3b41'
    duality_med = '#6a7283'
    duality_light = '#cfcfcf'

    colorschemes = {
        'light': {
            'background': '#d4dce8',
            'text': '#4b4b4b',

            'DARK_REPLACEME': '#d4dce8',
            'MED_REPLACEME': '#919bad',
            'LIGHT_REPLACEME': '#4b4b4b',
        },
        'dark': {
            'background': duality_dark,
            'text': duality_light,

            'DARK_REPLACEME': duality_dark,
            'MED_REPLACEME': duality_med,
            'LIGHT_REPLACEME': duality_light,
        },
    }

    def index(self, sheet):
        response.headers['Content-type'] = 'text/css;charset=utf8'
        c.colors = self.colorschemes['light']
        return render('stylesheets/%s.mako' % sheet)
    # TODO make a sub for the float-clear stuff
