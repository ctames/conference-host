###
### This is a one-time use program to update the database with the 
### information about the attendees.
###

import csv
import os
import sys
import pickle
import datetime
from utils import LogWarning, LogMessage
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "webApp.settings")
django.setup()

from django.db import transaction

from wordcounts import process_text
from webApp.models import NSFInvestigator, NSFProject, ProjectPIs, CollabProjects, \
                             Organizations, Programs, Words, Institutions, RapidMeeting, BreakoutParticipant, Posters, PosterPresenters, Breakout, RapidMeetingEval

def delete_project(award):
    try:
        bad = NSFProject.objects.get(awardID=award)
        bad.delete()
    except:
        LogWarning("Cannot find project to delete: " + award)

def fix_data():
    # delete_project('9322647')
    # delete_project('0000000')        
    # ppis = ProjectPIs.objects.filter(project=NSFProject.objects.get(awardID='1017660')).filter(investigator=NSFInvestigator.objects.get(id=141450))
    # assert ppis.count() == 2
    # ppis[0].delete()
    pass

def addPI(email, firstname, lastname, institution, cityname=None, statename=None):
    pi = NSFInvestigator.objects.filter(email = email)
    if pi.count() > 0:
        [eachpi.delete() for eachpi in pi]
        LogWarning("Duplicate add: " + email)
    else:
        inst = Institutions.objects.filter(name=institution)
        if inst.count() == 0:
            instobj = Institutions.objects.create(name=institution,
                                                  cityname=cityname,
                                                  statename=statename)
            instobj.save()
        else:
            instobj = inst[0]

        pi = NSFInvestigator.objects.create(email = email, firstname = firstname,
                                            lastname = lastname,
                                            institution = instobj,
                                            satc = True,
                                            attendee = True)
        print "Added PI: " + pi.fullDisplay()
        return pi

def add_institution(name, cityname, statename):
    try:
        inst = Institutions.objects.get(name=name)
        print "Institution already exists: " + inst.displayFull()
    except:
        print "Adding institution: " + name
        instobj = Institutions.objects.create(name=name,
                                              cityname=cityname,
                                              statename=statename)
        instobj.save()

def set_institution(email, institution):
    pi = NSFInvestigator.objects.get(email=email)
    institution = Institutions.objects.get(name=institution)
    pi.institution = institution
    pi.save()

def set_noshow(email):
    pi = NSFInvestigator.objects.get(email=email)
    pi.noshow = True
    pi.save()

def set_institution_id(id, institution):
    pi = NSFInvestigator.objects.get(id=id)
    institution = Institutions.objects.get(name=institution)
    pi.institution = institution
    pi.save()

def switch_rm(pid, round, oldgroup, newgroup):
    pi = NSFInvestigator.objects.get(id=pid)
    rmold = RapidMeeting.objects.get(id=oldgroup)
    rmnew = RapidMeeting.objects.get(id=newgroup)
    print "Switching " + pi.fullDisplay() + " from " + str(rmold.id) + " to " + str(rmnew.id)
    assert rmold.round == rmnew.round == round

    if rmold.pi1 == pi:
        rmold.pi1 = rmold.pi2
        rmold.pi2 = rmold.pi3
        rmold.pi3 = rmold.pi4
        rmold.pi4 = None
        rmold.save()
    elif rmold.pi2 == pi:
        rmold.pi2 = rmold.pi3
        rmold.pi3 = rmold.pi4
        rmold.pi4 = None
        rmold.save()
    elif rmold.pi3 == pi:
        rmold.pi3 = rmold.pi4
        rmold.pi4 = None
        rmold.save()
    elif rmold.pi4 == pi:
        rmold.pi4 = None
        rmold.save()
    else:
        print "Not found in old group!"
        # assert False

    # add to rmnew
    if not rmnew.pi1:
        rmnew.pi1 = pi
    elif not rmnew.pi2:
        rmnew.pi2 = pi
    elif not rmnew.pi3:
        rmnew.pi3 = pi
    elif not rmnew.pi4:
        rmnew.pi4 = pi
    else:
        assert False

    rmnew.save()

def remove_from_matching(pid):
    pi = NSFInvestigator.objects.get(id=pid)

    for rm in RapidMeeting.objects.filter(pi1=pi):
        assert rm.pi1 == pi
        rm.pi1 = rm.pi2
        rm.pi2 = rm.pi3
        rm.pi3 = rm.pi4
        rm.pi4 = None
        rm.save()

    for rm in RapidMeeting.objects.filter(pi2=pi):
        assert rm.pi2 == pi
        rm.pi2 = rm.pi3
        rm.pi3 = rm.pi4
        rm.pi4 = None
        rm.save()

    for rm in RapidMeeting.objects.filter(pi3=pi):
        assert rm.pi3 == pi
        rm.pi3 = rm.pi4
        rm.pi4 = None
        rm.save()

    for rm in RapidMeeting.objects.filter(pi4=pi):
        assert rm.pi4 == pi
        rm.pi4 = None
        rm.save()
    
def add_to_breakout(pid, bid):
    pi = NSFInvestigator.objects.get(id=pid)
    breakout = Breakout.objects.get(number=bid)
    BreakoutParticipant.objects.create(pi=pi, breakout=breakout, leader=False)

def remove_from_breakouts(pid):
    pi = NSFInvestigator.objects.get(id=pid)
    breakouts = BreakoutParticipant.objects.filter(pi=pi)
    assert breakouts.count() <= 1
    for breakout in breakouts:
        breakout.delete()

if __name__ == "__main__":
    # add_institution('Cornell Tech', 'New York City', 'New York')
    # set_institution('ajuels@gmail.com', 'Cornell Tech')
    # set_institution('jlach@virginia.edu', 'University of Virginia Main Campus')
    # remove_from_matching(163615)
    # remove_from_matching(96123)
    # remove_from_breakouts(96123)
    # remove_from_matching(110855)
    # poster = Posters.objects.get(title='A Model Explaining Security Behavior of Employees in Cyberspace')
    # PosterPresenters.objects.create(poster=poster, presenter=NSFInvestigator.objects.get(id=159444))

    # set_institution_id(154444, 'University of Colorado at Colorado Springs')
    # remove_from_matching(117379) # feamster
    # remove_from_breakouts(117379)
    # add_to_breakout(117379, 13)

    # switch_rm(74563, 1, 5546, 5610)
    # switch_rm(115291, 2, 5671, 5679)
    # switch_rm(157732, 3, 5835, 5845)
    # remove_from_matching(131146) # chris kim
    #! remove_from_matching(121267)
    #! remove_from_breakouts(121267)

    #> delete poster Caging Libraries To Control Software Faults
    #> delete poster Privacy-preserving Data Collection on IEEE 802.11s-based Smart Grid AMI Networks
    #> fix poster: remove Terry Benzel from LASER poster, change project to 1446407
    
    poster = Posters.objects.get(title='Learning from Authoritative Security Experiment Results (LASER)')
    ppi = PosterPresenters.objects.get(poster=poster, presenter=NSFInvestigator.objects.get(id=107154))
    ppi.delete()
    poster.project = NSFProject.objects.get(awardID=1446407)
    poster.save()

    # print "Deleting all evalution!"
    # RapidMeetingEval.objects.all().delete()
    
    ## noshows
#    set_noshow('gahn@asu.edu')
#    set_noshow('kemal@cs.siu.edu')
#    set_noshow('robin.j.bachman@census.gov')
#    set_noshow('bertino@cs.purdue.edu')
#    set_noshow('dabbish@cmu.edu')
#    set_noshow('huaiyu_dai@ncsu.edu')
#    set_noshow('rdantu@unt.edu')
#    set_noshow('ghafoor@purdue.edu')
#    set_noshow('sghosh@cse.usf.edu')
#    set_noshow('hafiz@umd.umich.edu')
#    set_noshow('tien@iastate.edu')
#    set_noshow('reddy@ece.tamu.edu')
#    set_noshow('browe@rti.org')
#    set_noshow('shao@cs.yale.edu')
#    set_noshow('ankurs@eng.umd.edu')

    #remove_from_matching(121267)
    # remove_from_breakouts(121267)
    # set_institution_id(94176, 'SUNY at Stony Brook')
    # institution = Institutions.objects.get(name='SUNY at Stony Brook')
    # institution.shortname = 'Stony Brook University'
    # institution.save()
    # set_institution_id(117379, 'Princeton University')

