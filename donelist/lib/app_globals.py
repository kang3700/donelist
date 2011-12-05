from __future__ import with_statement
from pylons import config
import pytz, os, logging, sys, socket, re, subprocess, random
import signal
from datetime import timedelta, datetime
from urlparse import urlparse
from donelist.lib.stats import Stats
import json
import logging
class Globals(object):
    """Globals acts as a container for objects available throughout the
    life of the application
    """
    int_props = ['db_pool_size',
                 'db_pool_overflow_size',
                 'page_cache_time',
                 'solr_cache_time',
                 'num_mc_clients',
                 'MIN_DOWN_LINK',
                 'MIN_UP_KARMA',
                 'MIN_DOWN_KARMA',
                 'MIN_RATE_LIMIT_KARMA',
                 'MIN_RATE_LIMIT_COMMENT_KARMA',
                 'VOTE_AGE_LIMIT',
                 'REPLY_AGE_LIMIT',
                 'WIKI_KARMA',
                 'HOT_PAGE_AGE',
                 'MODWINDOW',
                 'RATELIMIT',
                 'QUOTA_THRESHOLD',
                 'num_comments',
                 'max_comments',
                 'max_comments_gold',
                 'num_default_reddits',
                 'num_query_queue_workers',
                 'max_sr_images',
                 'num_serendipity',
                 'sr_dropdown_threshold',
                 'comment_visits_period',
                  'min_membership_create_community',
                 'bcrypt_work_factor',
                 ]

    float_props = ['min_promote_bid',
                   'max_promote_bid',
                   'usage_sampling',
                   'statsd_sample_rate',
                   ]

    bool_props = ['debug', 'translator',
                  'log_start',
                  'sqlprinting',
                  'template_debug',
                  'uncompressedJS',
                  'enable_doquery',
                  'use_query_cache',
                  'write_query_queue',
                  'css_killswitch',
                  'db_create_tables',
                  'disallow_db_writes',
                  'exception_logging',
                  'disable_ratelimit',
                  'amqp_logging',
                  'read_only_mode',
                  'frontpage_dart',
                  'allow_wiki_editing',
                  'heavy_load_mode',
                  's3_media_direct',
                  'disable_captcha',
                  'disable_ads',
                  'static_pre_gzipped',
                  'static_secure_pre_gzipped',
                  ]

    tuple_props = ['stalecaches',
                   'memcaches',
                   'permacache_memcaches',
                   'rendercaches',
                   'servicecaches',
                   'cassandra_seeds',
                   'admins',
                   'sponsors',
                   'monitored_servers',
                   'automatic_reddits',
                   'agents',
                   'allowed_css_linked_domains',
                   'authorized_cnames',
                   'hardcache_categories',
                   'proxy_addr',
                   's3_media_buckets',
                   'allowed_pay_countries',
                   'case_sensitive_domains']

    #choice_props = {'cassandra_rcl': {'ONE':    CL_ONE,
    #                                  'QUORUM': CL_QUORUM},
    #                'cassandra_wcl': {'ONE':    CL_ONE,
    #                                  'QUORUM': CL_QUORUM},
    #                }
    @staticmethod
    def to_bool(x):
        return (x.lower() == 'true') if x else None

    @staticmethod
    def to_iter(v, delim = ','):
        return (x.strip() for x in v.split(delim) if x)

    def __init__(self, global_conf, app_conf, paths, **extra):
        """
        Globals acts as a container for objects available throughout
        the life of the application.

        One instance of Globals is created by Pylons during
        application initialization and is available during requests
        via the 'g' variable.

        ``global_conf``
            The same variable used throughout ``config/middleware.py``
            namely, the variables from the ``[DEFAULT]`` section of the
            configuration file.

        ``app_conf``
            The same ``kw`` dictionary used throughout
            ``config/middleware.py`` namely, the variables from the
            section in the config file for your application.

        ``extra``
            The configuration returned from ``load_config`` in 
            ``config/middleware.py`` which may be of use in the setup of
            your global variables.

        """

        global_conf.setdefault("debug", False)

        # slop over all variables to start with
        for k, v in  global_conf.iteritems():
            if not k.startswith("_") and not hasattr(self, k):
                if k in self.int_props:
                    v = int(v)
                elif k in self.float_props:
                    v = float(v)
                elif k in self.bool_props:
                    v = self.to_bool(v)
                elif k in self.tuple_props:
                    v = tuple(self.to_iter(v))
                #elif k in self.choice_props:
                #    if v not in self.choice_props[k]:
                #        raise ValueError("Unknown option for %r: %r not in %r"
                #                         % (k, v, self.choice_props[k]))
                #    v = self.choice_props[k][v]
                setattr(self, k, v)

        self.paths = paths

        self.running_as_script = global_conf.get('running_as_script', False)
        
        # turn on for language support
        #if not hasattr(self, 'lang'): self.lang = 'en'
        #self.languages, self.lang_name = \
        #                get_active_langs(default_lang= self.lang)

        #all_languages = self.lang_name.keys()
        #all_languages.sort()
        #self.all_languages = all_languages
        
        # set default time zone if one is not set
        tz = global_conf.get('timezone', 'UTC')
        self.tz = pytz.timezone(tz)
        
        # dtz = global_conf.get('display_timezone', tz)
        # self.display_tz = pytz.timezone(dtz)

    

    def setup(self, global_conf):
        '''Bind some global conf.'''
        self.setup_log(global_conf)
        self.setup_stats(global_conf)
	def reset_caches():
    	    pass 
	self.reset_caches = reset_caches

   

    def setup_log(self, global_conf):
        self.log = logging.getLogger('donelist')
        self.log.addHandler(logging.StreamHandler()) # default to stderr
        if self.debug:
            self.log.setLevel(logging.DEBUG)
        else:
            self.log.setLevel(logging.INFO)
        
        
    def setup_stats(self, global_conf):
        self.stats = Stats(global_conf.get('statsd_addr'),
                           global_conf.get('statsd_sample_rate'))
