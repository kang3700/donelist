class QueueMap(object):

    def __init__(self,exchange, chan,exchange_type='direct',durable=True,auto_delete=False):
        self.exchange = exchange
        self.chan = chan

        self._exchange(exchange,exchange_type=exchange_type,durable=durable, auto_delete=auto_delete)

    def _exchange(self,name,exchange_type,durable,auto_delete):
        self.chan.exchange_declare(exchange=name,
                                   type=exchange_type,
                                   durable=durable,
                                   auto_delete=auto_delete)

    def _q(self,name,durable=True,exclusive=False,auto_delete=False,self_refer=False):
        self.chan.queue_declare(queue=name,durable=durable,exclusive=exclusive,auto_delete=auto_delete)
        if self_refer:
            self._bind(name,name)

    def _bind(self,rk,q):
        self.chan.queue_bind(routing_key=rk,queue=q,exchange=self.exchange)

    def init(self):
        self.queues()
        self.bindings()

    def queues(self):
        raise NotImplementedError

    def bindings(self):
        raise NotImplementedError


class DonelistQueueMap(QueueMap):
    def queues(self):
        self._q('log_q',self_refer=True,durable=False)
        # self._bind('search_changes','solrsearch_changes')

    def bindings(self):
        pass
