import logging
from pylons import g
LOG_FILE="/home/wizard/ubuntu-one/donelist/log.log"
from donelist.lib.mq import log as log2
from donelist.lib.mq import amqp
from donelist.lib.base import *
import cPickle as pickle
from donelist.lib.wrapped import Templated
from donelist.lib.templated.boringpage import BoringPage

import sys
log = logging.getLogger(__name__)
log.addHandler(logging.FileHandler(LOG_FILE))
log.setLevel(logging.INFO)

class Password(Templated):
    """Form encountered when 'recover password' is clicked in the LoginFormWide."""
    def __init__(self, success=False):
        Templated.__init__(self, success = success)

class FormsController(BaseController):
   
    
        
    def index(self):
        @g.stats.amqp_processor("log_q")
        def handle(msg):
            for msgs in msg:
                print "msg%s" % pickle.loads(msgs.body)
        
        # log2.log_text('formscontroller')
        # amqp.handle_items("log_q",handle,verbose = False)

        # Return a rendered template
        #   return render('/some/template.mako')
        # or, Return a response
        return 'Hello World' 
    def GET_password(self):
        log.info("in_password")
        """The 'what is my password' page"""
        return BoringPage("password", content=Password()).render()  #_ i18n




  




