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
                             Organizations, Programs, Words, Institutions
from nsfmodels import Investigators, Researcher, Project, Institution

def update_pis(fname):
    with open(fname, 'rU') as file:
        reader = csv.reader(file, dialect="excel")
        try:
            firstRow = True
            for row in reader:
                if firstRow:
                    header = row
                    print "Read header: " + str(header)
                    firstRow = False
                    continue

                nsfemail = row[header.index('NSF Email')]
                if not '@' in nsfemail:
                    # non-pi - skip
                    continue

                try:
                    pi = NSFInvestigator.objects.get(email = nsfemail)
                except:
                    print "Missing PI: " + nsfemail
                    return # assert False

                pi.attendee = True
                pi.satc = True
                if not pi.getPrimaryInstitution():
                    print("No institution for: " + pi.fullDisplay())
                    company = row[header.index('Company')]
                    if company:
                        try:
                            institution = Institutions.objects.get(name = company)
                        except:
                            print("Adding institution: " + company + " " + cityname + ", " + statename)
                            institution = Institutions.objects.create(name = company,
                                                                      cityname = row[header.index('Work City')],
                                                                      statename = row[header.index('Work State')])
                            institution.save()
                        print "Updating institution for: " + pi.displayName() + " => " + company
                        pi.institution = institution
                        pi.save()
                        LogMessage("Updated: " + pi.displayName())
                    continue

        except csv.Error as e:
            sys.exit('file %s, line %d: %s' % (fname, reader.line_num, e))
            
if __name__ == "__main__":
    for arg in sys.argv[1:]:
        update_pis(arg)


"""


                    matches = NSFInvestigator.objects.filter(firstname=row[header.index('First Name')]).filter(lastname=row[header.index('Last Name')])
                    if len(matches) > 0:
                        LogWarning("Duplicate entry: " + row[header.index('First Name')] + " " +
                                   row[header.index('Last Name')])
                        LogWarning(" email: " + nsfemail + " / " + matches[0].email)
                        # continue
                    
                    LogMessage("Add PI: " + nsfemail + " / " + row[header.index('First Name')]
                               + " " + row[header.index('Last Name')])
                    # continue
                    piobj = NSFInvestigator.objects.create(email = nsfemail,
                                                           firstname = row[header.index('First Name')],
                                                           lastname = row[header.index('Last Name')],
                                                           satc = True,
                                                           attendee = True,
                                                           nonpi = (nsfemail == '-'))
                    
                    company = row[header.index('Company')]
                    if company:
                        try:
                            institution = Institutions.objects.get(name = company)
                        except:
                            institution = Institutions.objects.create(name = company,
                                                                      cityname = row[header.index('Work City')],
                                                                      statename = row[header.index('Work State')])
                            institution.save()
                    
                    print "Added investigator: " + piobj.fullDisplay()
                    piobj.save()
                    grants = row[header.index('NSF Grant Number')]
                    if grants:
                        grants = grants.split(',')
                        for grant in grants:
                            grant = grant.strip(' ')
                            if len(grant) == 6 and grant[0]=='9':
                                grant = '0' + grant
                            if len(grant) != 7:
                                LogWarning("Bad grant number: " + grant)
                                continue
                            try:
                                nsfproject = NSFProject.objects.get(awardID = grant)
                                ProjectPIs.objects.create(investigator = piobj,
                                                          project = nsfproject,
                                                          institution = institution,
                                                          role = 'Key')
                                LogMessage("Added grant: " + grant)
                            except:
                                if grant.startswith('18'):
                                    pass
                                else:
                                    LogWarning("No matching project: " + grant)
"""
