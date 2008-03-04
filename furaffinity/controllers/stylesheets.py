from furaffinity.lib.base import *
import furaffinity.lib.paginate as paginate
from furaffinity.model import form

import logging

log = logging.getLogger(__name__)

class StylesheetsController(BaseController):

    duality_light_back = '#d4dce8'
    duality_light_mid = '#919bad'
    duality_light_fore = '#4b4b4b'

    duality_dark_back = '#2e3b41'
    duality_dark_mid = '#6a7283'
    duality_dark_fore = '#cfcfcf'

    colorschemes = {
        'light': {
            'background': duality_light_back,
            'background_alt': '#c8d2e2',
            'background_hover': '#eef1f5',
            'text': duality_light_fore,
            'link': '#5775ad',
            'link_visited': '#8257ad',
            'link_active': '#57ad57',
            'link_hover': '#ad5757',
            'header': 'black',
            'header2': duality_light_mid,
            'header_atop_border': 'white',
            'border': duality_light_mid,
            'border_strong': 'black',
        },
        'dark': {
            'background': duality_dark_back,
            'background_alt': '#303b3f',
            'background_hover': '#252d30',
            'text': duality_dark_fore,
            'link': '#5775ad',
            'link_visited': '#8257ad',
            'link_active': '#57ad57',
            'link_hover': '#ad5757',
            'header': 'white',
            'header2': duality_dark_mid,
            'header_atop_border': 'white',
            'border': duality_dark_mid,
            'border_strong': duality_dark_fore,
        },
    }

    def index(self, sheet, color=None):
        """Returns the selected stylesheet filled with the selected colors."""

        response.headers['Content-type'] = 'text/css;charset=utf8'
        c.colors = self.colorschemes.get(color, self.colorschemes['dark'])
        return render('stylesheets/%s.mako' % sheet)

    # TODO make a sub for the float-clear stuff
