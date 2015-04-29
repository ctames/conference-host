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

def test_addr(s):
    try:
        pi = NSFInvestigator.objects.get(email=s)
        return True
    except:
        return False

def test_emails(fname):
    with open(fname, 'r') as file:
        for email in file:
            email = email[:-1]

            if test_addr(email):
                print email
            else:
                print "-"
            
if __name__ == "__main__":
    for arg in sys.argv[1:]:
        test_emails(arg)


