from __future__ import division
from django.contrib.humanize.templatetags.humanize import intcomma

import logging

def memoize(f): # Peter Norvig's code
    table = {}
    def fmemo(*args):
        if args not in table:
            table[args] = f(*args)
        return table[args]
    fmemo.memo = table
    return fmemo

logger = logging.getLogger('django.request')

def LogWarning(s):
    # print "[Warning] " + s
    logger.warning("[Warning] " + s)

import datetime 

def LogMessage(s):
    current_time = datetime.datetime.now()
    msg = current_time.isoformat() + ": " + s
    logger.debug(msg)

def uniq(l):
    return list(set(l))

def format_amount(n):
    if n >= 1000000:
        return "{:.1f}".format(n / 1000000) + "M"
    else:
        return intcomma(n)

def scope(request):
    # post variable scope overides session
    if request.GET.get('scope'):
        scope = request.GET.get('scope')
    else:
        scope = request.session.get('scope', None) 

    if not scope:
        return 'satc'
    else:
        return scope

def limitActive(request):
    return request.session.get('active', False)

def isSaTC(request):
    return scope(request) == 'satc'

import socket

import hashlib
#from secret import SECRET
# ^ commented out as "secret" is a module not on the repo
# it's used as a "key" to create a hash for personal meeting reviews 

SECRET = "secret"
def key_from_email(email):
    magickey = hashlib.sha224(email + "/" + SECRET).hexdigest()[5:18]
    return magickey

def showEmail():
    return False # True # return socket.gethostname() == 'Ursuton'
