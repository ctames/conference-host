###
### Outputs a csv file of all SaTC PIs and their collaborators
###

import os
import sys
import pickle
import datetime
from utils import LogWarning, LogMessage, uniq
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "webApp.settings")
django.setup()

from django.db import transaction

from wordcounts import process_text
from webApp.models import NSFInvestigator, NSFProject, ProjectPIs, CollabProjects, \
                             Organizations, Programs, Words, Institutions
from nsfmodels import Investigators, Researcher, Project, Institution

def generateCollaborators(institution):
    pis = NSFInvestigator.objects.filter(satc=True).extra(select={'lower_name': 'lower(lastname)'}).order_by('lower_name', 'firstname').filter(attendee=True)

    for pi in pis:
        line = pi.email + ", "

        piprojects = ProjectPIs.objects.filter(investigator=pi)
        projects = sorted(uniq([p.project for p in piprojects if p.project]), 
                          key=lambda proj: proj.startDate)

        collaborators = sorted(uniq(
                [p.investigator
                 for proj in projects
                 for p in ProjectPIs.objects.filter(project=proj)]
                +
                [p.investigator
                 for proj in projects
                 for collab in [c.project2 for c in CollabProjects.objects.filter(project1 = proj)]
                 for p in ProjectPIs.objects.filter(project=collab)]),
                               key = lambda pi: pi.lastname)

        if institution:
            institutions = pi.getInstitutions()
            for institution in institutions:
                pis = uniq([ppi.investigator for ppi in ProjectPIs.objects.filter(institution=institution)])
                pis = [icollab for icollab in pis if pi.attendee]
                if pi in pis:
                    pis.remove(pi)
                else:
                    pass # LogWarning("Not a self institution collaborator! " + pi.fullDisplay())

                collaborators += pis
                
        if pi in collaborators:
            collaborators.remove(pi)
        else:
            pass # print "Not self-collaborator: " + pi.email

        line += ', '.join([collaborator.email for collaborator in collaborators if collaborator.attendee])
        print line

if __name__ == "__main__":
    generateCollaborators(institution=True)
