###
### This is a one-time use program to update the database with the 
### information about the attendees.
###

# Import smtplib for the actual sending function
import smtplib
import time

# Import the email modules we'll need
from email.mime.text import MIMEText

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
from pdfManage.models import NSFInvestigator, NSFProject, ProjectPIs, CollabProjects, \
                             Organizations, Programs, Words, Institutions, Posters, PosterPresenters
from nsfmodels import Investigators, Researcher, Project, Institution

def email_poster(row, header):
    sys.exit("Don't email unless you really mean it!")
    presenters = []
    presenter = row[header.index('Poster Presenter')]
    presenter2 = row[header.index('Poster Presenter 2')]
    presenter3 = row[header.index('Poster Presenter 3')]
    title = row[header.index('Poster name')]

    try:
       pi = NSFInvestigator.objects.get(email = presenter)
       presenters.append(pi)
       # LogMessage("Poster presenter: " + pi.fullDisplay())
    except:
       LogWarning("No matching PI: " + presenter)

    pi2 = None
    if len(presenter2) > 1:
       try:
           pi2 = NSFInvestigator.objects.get(email = presenter2)
           presenters.append(pi2)
           # LogMessage("Poster presenter: " + pi2.fullDisplay())
       except:
           LogWarning("No matching PI for presenter 2: " + presenter2)

    pi3 = None
    if len(presenter3) > 1:
       try:
           pi3 = NSFInvestigator.objects.get(email = presenter3)
           presenters.append(pi3)
           # LogMessage("Poster presenter: " + pi3.fullDisplay())
       except:
           LogWarning("No matching PI for presenter 3: " + presenter3)

    project = None
    try:
        project = NSFProject.objects.get(awardID=row[header.index('NSF Grant Number')])
    except:
        LogWarning("No matching project: " + row[header.index('NSF Grant Number')])

    msg = "Dear "
    msg += ', '.join([pi.firstname + " " + pi.lastname for pi in presenters])
    msg += ":\n"
    msg += """
Thank you for requesting to present a poster at the NSF SaTC PIs Meeting.  

Your poster:

"""
    msg += "     " + title + "\n"
    msg += """
has been accepted for presentation.

The poster session will be held Monday, January 5 in the evening.

You should bring a printed poster to the session.  We will provide 
an easel and 3' x 4' poster board.  Feel free to also bring any
printed materials you would like to distribute.

Thank you for your contribution to the meeting, and I look forward to 
seeing you at the meeting.

Best,

--- Dave
========================================
David Evans
http://www.cs.virginia.edu/evans
Organizer, NSF SaTC PIs Meeting

"""

    print msg

    sender = 'SaTC PIs Meeting<evansde@gmail.com>'
    recipients = [pi.email for pi in presenters]
    # recipients = ['evansde@gmail.com', 'evans@virginia.edu']

    msg = MIMEText(msg)
    msg['Subject'] = 'SaTC PIs Meeting Poster: ' + title
    msg['From'] = sender
    msg['To'] = ', '.join(recipients)
    msg['Cc'] = 'evans@virginia.edu'
    msg['Reply-To'] = 'evans@virginia.edu'

    s = smtplib.SMTP('smtp.gmail.com',587)
    s.set_debuglevel(1)
    s.ehlo()    
    s.starttls()
    s.login("evansde@gmail.com", "qpjsmodegdkkzptg")
    s.sendmail(sender, recipients, msg.as_string())
    s.quit()
    
    print "Sent message: " + msg.as_string()
    print "sleeping..."
    time.sleep(5 + len(msg['To']))
    # sys.exit("Done!")


    if False:
        poster = None
        try:
            poster = Posters.objects.get(title=title)
            poster.project=project
            poster.save()
            LogWarning("Poster already exists: " + title + " -> updated")
            return
        except:
            poster = Posters.objects.create(title=title, project=project)
            

        print "Poster: " + title
        for pi in presenters:
            PosterPresenters.objects.create(poster=poster, presenter=pi)
            print "   " + pi.lastname,
        print

def process_poster(row, header):
    presenters = []
    presenter = row[header.index('Poster Presenter')]
    presenter2 = row[header.index('Poster Presenter 2')]
    presenter3 = row[header.index('Poster Presenter 3')]
    title = row[header.index('Poster name')]

    try:
       pi = NSFInvestigator.objects.get(email = presenter)
       presenters.append(pi)
       # LogMessage("Poster presenter: " + pi.fullDisplay())
    except:
       LogWarning("No matching PI: " + presenter + " for " + title)

    pi2 = None
    if len(presenter2) > 1:
       try:
           pi2 = NSFInvestigator.objects.get(email = presenter2)
           presenters.append(pi2)
           # LogMessage("Poster presenter: " + pi2.fullDisplay())
       except:
           LogWarning("No matching PI for presenter 2: " + presenter2)

    pi3 = None
    if len(presenter3) > 1:
       try:
           pi3 = NSFInvestigator.objects.get(email = presenter3)
           presenters.append(pi3)
           # LogMessage("Poster presenter: " + pi3.fullDisplay())
       except:
           LogWarning("No matching PI for presenter 3: " + presenter3)

    project = None
    try:
        project = NSFProject.objects.get(awardID=row[header.index('NSF Grant Number')])
    except:
        LogWarning("No matching project: " + row[header.index('NSF Grant Number')] + " for " + title)

    poster = None
    try:
        poster = Posters.objects.get(title=title)
        poster.project=project
        poster.save()
        PosterPresenters.objects.delete(poster=poster)
        LogWarning("Poster already exists: " + title + " -> updated")
    except:
        poster = Posters.objects.create(title=title, project=project)
                
    #    print "Poster: " + title
    for pi in presenters:
        PosterPresenters.objects.create(poster=poster, presenter=pi)
        # print "   " + pi.lastname,
        # print
        
def process_posters(fname):
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
                
                # print "----------------------------------------------------------------------"
                process_poster(row, header)
                # break

        except csv.Error as e:
            sys.exit('file %s, line %d: %s' % (fname, reader.line_num, e))
            
if __name__ == "__main__":
    for arg in sys.argv[1:]:
        Posters.objects.all().delete()
        PosterPresenters.objects.all().delete()
        process_posters(arg)
        

