###
### load_breakouts.py
###

import os
import sys
import csv
import random
import datetime
from utils import LogWarning, LogMessage
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "webApp.settings")
django.setup()

from django.db import transaction

from webApp.models import NSFInvestigator, NSFProject, ProjectPIs, CollabProjects, \
                             Organizations, Programs, Words, Institutions, \
                             RapidMeeting, Breakout, BreakoutParticipant

from pprint import pprint

from breakouts import BREAKOUTS

def lookupMatchingPI(email):
    if email:
        pis = NSFInvestigator.objects.filter(email = email)
        if len(pis) == 1:
            pi = pis[0]
        else:
            if len(pis) == 0:
                LogWarning("No matching pi for: " + email)
                assert False
                pi = None
            else:
                LogWarning("Multiple matching pis for: " + email)
                pi = pis[0]
        return pi
    return None

def loadBreakouts(breakouts, fname):
    shortnames = {}
    bleaders = {}
    for breakout in breakouts:
        (number, session, room, tag, shortname, leaders, description) = breakout
        shortnames[tag] = number
        LogMessage("shortnames: " + tag + " = " + str(number))
        bleaders[number] = leaders
        LogMessage("Adding breakout: " + str(number) + ": " + shortname)
        Breakout.objects.create(number=number,
                                title=shortname,
                                description=description,
                                location=room,
                                session=session)

    with open(fname, 'rU') as file:
        reader = csv.reader(file, dialect="excel")
        firstRow = True
        for row in reader:
            if firstRow:
                header = row
                print "Read header: " + str(header)
                firstRow = False
                continue
            
            nsfemail = row[header.index('NSF Email')]
            breakout = row[header.index('Breakout')]
            
            if not breakout:
                LogMessage("No breakout for: " + row[header.index('First Name')] + " " + row[header.index('Last Name')])
                continue
            
            if not nsfemail:
                LogWarning("No nsfemail: " + row[header.index('First Name')] + " " + row[header.index('Last Name')])
                continue # for now...should fail!
            
            if breakout == 'Excluded' or breakout == 'Keynote':
                LogMessage("Excluded: " + row[header.index('First Name')] + " " + row[header.index('Last Name')])
                continue

            pi = lookupMatchingPI(nsfemail)
            bnum = shortnames[breakout]
            bobjs = Breakout.objects.filter(number=bnum)
            assert bobjs.count() == 1
            bobj = bobjs[0]
            leader = pi.email in bleaders[bnum]
            LogMessage("Adding breakout participant " + pi.displayName() + " to " + bobj.title + " leader: " + str(leader))
            BreakoutParticipant.objects.create(breakout=bobj, pi=pi, leader=leader)
            

if __name__ == "__main__":
    Breakout.objects.all().delete()
    BreakoutParticipant.objects.all().delete()
    loadBreakouts(BREAKOUTS, sys.argv[1])
    # for arg in sys.argv[1:]:
    #    loadBreakoutGroups(arg)
