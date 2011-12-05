#logger to rabbit mq,not use the python default log
from pylons import g
from donelist.lib.mq import amqp
from datetime import datetime
import cPickle as pickle
import traceback
# tz=g.display_timezone

Q = 'log_q'
def _default_dict():
    return dict(time=datetime.now(),
                host="127",
                port="default")
def log_exception(e,e_type,e_value,e_traceback):
    d = _default_dict()
    d['type'] = 'exception'
    d['traceback'] = traceback.extract_tb(e_traceback)
    d['exception_type'] = e.__class__.__name__
    s = str(e)
    d['exception_desc'] = s[:10000]
    amqp.add_item(Q, pickle.dumps(d))


def log_text(classification, text=None,level="info"):
    if text is None:
        text = classification

    if level not in ('debug', 'info', 'warning','error'):
        print "What kind of loglevel in the mq log is %s supposed to be?" % level
        level = 'error'
    d = _default_dict()
    d['type']='text'
    d['level']=level
    d['text']=text
    d['classification'] = classification
    amqp.add_item(Q,pickle.dumps(d))

                
def test_log():
    log_exception(Exception('sdf'), *sys.exc_info())
    
