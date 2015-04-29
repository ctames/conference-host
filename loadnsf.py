import os
import sys
import pickle
import datetime
from utils import LogWarning, LogMessage
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "webApp.settings")
django.setup()

from django.db import transaction

from forNSF.wordcounts import process_text
from webApp.models import NSFInvestigator, NSFProject, ProjectPIs, CollabProjects, \
                             Organizations, Programs, Words, Institutions

from nsfmodels import Institution

def loadInvestigators(file):
    LogMessage("Loading investigators: " + file)
    pis = None
    with open(file, 'r') as f:
        pis = pickle.load(f)
    
    count = 0
    total = len(pis.all())

    transaction.set_autocommit(True)
    with transaction.atomic():
        for pi in pis.all():
            current = NSFInvestigator.objects.filter(email = pi.email)
            if current:
                # update institution
                if len(current) == 1:
                    piobj = current[0]
                    update = False
                    if not piobj.firstname == pi.firstname:
                        piobj.firstname = pi.firstname
                        update = True
                        LogWarning("Updated firstname: " + pi.email + " -> " + pi.firstname)
                    if not piobj.lastname == pi.lastname:
                        piobj.lastname = pi.lastname
                        update = True
                        LogWarning("Updated lastname: " + pi.email + " -> " + pi.lastname)

                    if update:
                        piobj.save()
                else:
                    LogError("Multiple matching investigators for email: " + pi.email)
                total -= 1
            else:
                NSFInvestigator.objects.create(email = pi.email, firstname = pi.firstname,
                                               lastname = pi.lastname)
                if count % 100 == 0:
                    LogMessage("... " + str(count) + " of " + str(total) + "...")
                count += 1

    LogMessage("Finished loading investigators: " + str(count))

def loadInstitutions(file):
    LogMessage("Loading institutions: " + file)
    pis = None
    with open(file, 'r') as f:
        institutions = pickle.load(f)
    
    count = 0
    total = len(institutions.keys())

    transaction.set_autocommit(True)
    with transaction.atomic():
        for itag, institution in institutions.items():
            match = lookupExactMatchingInstitution(institution)

            if not match:
                Institutions.objects.create(name = institution.name,
                                            cityname = institution.cityname,
                                            statename = institution.statename)
                LogMessage("New institution: " + str(institution))
                count += 1
                if count % 100 == 0:
                    LogMessage("... " + str(count) + " of " + str(total) + "...")

    LogMessage("Finished loading institutions: " + str(count))

def lookupExactMatchingInstitution(institution, quiet=False):
    assert institution
    institutions = Institutions.objects.filter(name = institution.name).filter(cityname = institution.cityname).filter(statename = institution.statename)
    if len(institutions) == 1:
        return institutions[0]
    elif len(institutions) > 1:
        LogWarning("Multiple matching institutions: " + institution.name)
        return institutions[0]
    else:
        assert not institutions
        return None

def lookupMatchingInstitution(institution, quiet=False):
    assert institution
    exact = lookupExactMatchingInstitution(institution)
    if not exact:
        LogWarning("Cannot find exact match for institution: " + str(institution))
        institutions = Institutions.objects.filter(name = institution.name)
        if len(institutions) >= 1:
            LogWarning("Found approximate match: " + str(institutions[0]))
            return institutions[0]
        else:
            return None
    else:
        return exact

def lookupMatchingPI(email):
    if email:
        pis = NSFInvestigator.objects.filter(email = email)
        if len(pis) == 1:
            pi = pis[0]
        else:
            if len(pis) == 0:
                LogWarning("No matching pi for: " + email)
                pi = None
            else:
                LogWarning("Multiple matching pis for: " + email)
                pi = pis[0]
        return pi
    return None

def lookupMatchingProject(awardID):
    project = NSFProject.objects.filter(awardID = awardID)
    if len(project) == 1:
        return project[0]
    else:
        if len(project) == 0:
            LogWarning("No matching project for: " + awardID)
        else:
            LogWarning("Multiple matching project for: " + awardID)
            return project[0]

def addWords(project, nsfproject):
    wcounts = process_text(project.abstract)
    with transaction.atomic():
        for (word, count) in wcounts.items():
            Words.objects.create(project = nsfproject, word = word, count = count, title = False)

    with transaction.atomic():
        for (word, count) in wcounts.items():
            Words.objects.create(project = nsfproject, word = word, count = count, title = True)

def loadProjects(file):
    projects = None
    with open(file, 'r') as f:
        projects = pickle.load(f)

    count = 0
    total = len(projects)
    LogMessage("Loading projects: " + str(total))

    transaction.set_autocommit(True)
    with transaction.atomic():
        for project in projects:
            oldproject = NSFProject.objects.filter(awardID = project.awardID)
            if oldproject:
                LogWarning("Project duplicate: " + project.awardID)
                oldobj = oldproject[0]
                oldobj.delete()
            else:
                LogWarning("New project: " + project.awardID)

            startdate = datetime.datetime.strptime(project.startDate, "%m/%d/%Y").date()
            expiredate = datetime.datetime.strptime(project.expirationDate, "%m/%d/%Y").date()
            pi = None
            piemail = project.pi
            pi = lookupMatchingPI(piemail)
            copis = []
            copiemails = project.copis
            for copiemail in copiemails:
                copi = lookupMatchingPI(copiemail)
                if copi: 
                    copis.append(copi)
             
            iname = project.institution
            segments = iname.split('%')
            
            while len(segments) > 3:
                LogMessage("Shortening bad institution: " + iname)
                segments[1] = segments[0] + "%" + segments[1]
                segments = segments[1:]
                
            if not len(segments) == 3:
                LogWarning("Bad Institution: " + iname)
                institution = None
            else:
                institution = lookupMatchingInstitution(Institution(segments[0], segments[1], segments[2]))
                # LogMessage("Found matching institution: " + institution.name)

            # LogMessage("Add project: " + project.title)
            nsfproject = NSFProject.objects.create(awardID = project.awardID,
                                                   title = project.title,
                                                   startDate = startdate,
                                                   expirationDate = expiredate,
                                                   amount = int(project.amount),
                                                   satc = project.isSaTC(),
                                                   institution = institution,
                                                   abstract = project.abstract)

            for organization in project.organizations:
                Organizations.objects.create(project = nsfproject, organization = organization)

            for program in project.programs:
                Programs.objects.create(project = nsfproject, program = program)

            if pi:
                if project.isSaTC():
                    pi.satc = True
                    pi.save()

                pimember = ProjectPIs.objects.create(
                    investigator = pi,
                    project = nsfproject,
                    institution = institution,
                    role = 'PI')

            for copi in copis:
                if project.isSaTC():
                    copi.satc = True

                ProjectPIs.objects.create(investigator = copi,
                                          project = nsfproject,
                                          institution = institution,
                                          role = 'CoPI')
                
            # LogMessage("Adding project: " + str(project.awardID))
            assert lookupMatchingProject(project.awardID)
            addWords(project, nsfproject)
            count += 1
            if count % 100 == 0:
                LogMessage("... " + str(count) + " of " + str(total) + "...")

    LogMessage("Adding collaborative projects...")

    # Add collaborative projects once project table is complete
    with transaction.atomic():
        for project in projects:
            pobj = lookupMatchingProject(project.awardID)
            if not pobj:
                LogWarning("No matching project! " + str(project.awardID))
                continue
            collabs = project.collabs
            for collab in collabs:
                cobj = lookupMatchingProject(collab)
                CollabProjects.objects.create(project1 = pobj, project2 = cobj)

    # check collab symmetry

def loadFile(f):
    if 'projects' in f:
        loadProjects(f)
    elif 'institutions' in f:
        loadInstitutions(f)
    else:
        loadInvestigators(f)

if __name__ == "__main__":
    for arg in sys.argv[1:]:
        loadFile(arg)
