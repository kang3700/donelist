from donelist.lib.templated.reddit import Reddit
from pylons import c, g
class BoringPage(Reddit):
    """parent class For rendering all sorts of uninteresting,
    sortless, navless form-centric pages.  The top navmenu is
    populated only with the text provided with pagename and the page
    title is 'reddit.com: pagename'"""

    extension_handling= False

    def __init__(self, pagename, **context):
        self.pagename = pagename
        name = 'site-name'
        if "title" not in context:
            context['title'] = "%s: %s" % (name, pagename)

        Reddit.__init__(self, **context)

    # def build_toolbars(self):
        #--- return [PageNameNav('nomenu', title = self.pagename)]


#datefmt = _force_utf8(_('%d %b %Y'))

# def get_captcha():
#     if not c.user_is_loggedin or c.user.needs_captcha():
#         return get_iden()

