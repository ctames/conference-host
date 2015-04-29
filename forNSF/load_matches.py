###
### load_matches.py
###

### Read in a groups.csv file produced by rematchr and put matches in database.

### WARNING: this clears all the previous matches.

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
                             RapidMeeting

import json
from pprint import pprint


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

MAXLOCATION=150

def findNearestOpenLocation(spaces, start):
    # print("Finding nearest open to " + str(start) + "..." + str(MAXLOCATION))
    for offset in range(0, MAXLOCATION / 2):
        # print("Try offset: " + str(offset))
        if spaces[(start + offset) % MAXLOCATION] == -1:
            # print("Found open location: " + str((start + offset) % MAXLOCATION))
            return (start + offset) % MAXLOCATION
        if spaces[(start - offset) % MAXLOCATION] == -1:
            # print("Found open - location: " + str((start - offset) % MAXLOCATION))
            return (start - offset) % MAXLOCATION
    
    LogWarning("No open locations!")
    assert False

def locationRoom(location):
    assert location < MAXLOCATION
    location += 1 # start from 1
    if location < 40:
        return 'Washington Room'
    elif location < 50:
        return 'Potomac 1'
    elif location < 60:
        return 'Potomac 2'
    elif location < 70:
        return 'Potomac 3'
    elif location < 80:
        return 'Potomac 4'
    elif location < 90:
        return 'Potomac 5'
    elif location < 100:
        return 'Potomac 6'
    else:
        assert location <= MAXLOCATION
        return 'Regency EF'

def selectLocation(spaces, meeting, round, pi1, pi2, pi3, pi4):
    # assumes rounds are processed in order
    print "Finding location for: " + str(meeting)
    round = round - 1 # offset by 1
    if round == 0:
        location = findNearestOpenLocation(spaces[round], random.randint(0, MAXLOCATION - 1))
        spaces[round][location] = meeting
    else:
        closest = None
        distance = None
        for pi in [pi1, pi2, pi3, pi4]:
            if pi:
                lastround = RapidMeeting.objects.filter(pi1=pi) | RapidMeeting.objects.filter(pi2=pi) | RapidMeeting.objects.filter(pi3=pi) | RapidMeeting.objects.filter(pi4=pi)
                lastround = lastround.filter(round=round) # note: round is -1
                if lastround.count() == 1:
                    lastlocation = lastround[0].location
                    nearest = findNearestOpenLocation(spaces[round], lastlocation)
                    if (not closest) or (abs(lastlocation - nearest) < distance) or (abs(lastlocation - nearest) == distance and random.randint(0, 1) == 0):
                        closest = nearest
                        distance = abs(lastlocation - nearest)
                        print("Found better location: " + str(closest) + " (distance " + str(distance) + " for " + pi.displayName() + ")")
                else:
                    if lastround.count() == 0:
                        LogWarning("No previous round for " + pi.displayName())
                    else:
                        LogWarning("Multiple previous rounds for " + pi.displayName())

        assert closest
        location = closest

    return location

def loadMatches(fname):
    RapidMeeting.objects.all().delete()
    print("Loading matches: " + fname)
    # we have 149 total spaces:
    # Washington Room -- 39 Spaces -- Sessions 1 - 39
    # Potomac 1 -- 10 Spaces -- Sessions 40 - 49
    # Potomac 2 -- 10 Spaces -- Sessions 50 - 59
    # Potomac 3 -- 10 Spaces -- Sessions 60 - 69
    # Potomac 4 -- 10 Spaces -- Sessions 70 - 79
    # Potomac 5 -- 10 Spaces -- Sessions 80 - 89
    # Potomac 6 -- 10 Spaces -- Sessions 90 - 99
    # Regency EF -- 50 Spaces -- Sessions 100 - 150

    spaces = [[-1] * 150 for space in range(0,4)]

    with open(fname, 'rU') as file:
        reader = csv.reader(file, dialect="excel")
        for row in reader:
            print "Group " + row[0] + ": " + row[1] + " - " + row[2] + ", " + row[3] + ", " + row[4] 
            meeting = int(row[0])
            round = int(row[1])
            pi1 = lookupMatchingPI(row[2])
            assert pi1
            pi2 = lookupMatchingPI(row[3])
            pi3 = lookupMatchingPI(row[4])
            if pi3:
                assert pi2

            pi4 = lookupMatchingPI(row[5])
            if pi4:
                assert pi3

            reason = row[6]
            score = float(row[7])
            
            location = selectLocation(spaces, meeting, round, pi1, pi2, pi3, pi4)
            print("Meeting " + str(meeting) + " in location " + str(location))
            RapidMeeting.objects.create(pi1=pi1,
                                        pi2=pi2,
                                        pi3=pi3,
                                        pi4=pi4,
                                        round=round,
                                        room=locationRoom(location),
                                        location=location,
                                        reason=reason,
                                        score=score)

if __name__ == "__main__":
    for arg in sys.argv[1:]:
        loadMatches(arg)
