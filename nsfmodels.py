###
### Object models for nsf data
### 

from utils import LogWarning

class Investigators():
    ## Mapping from email (unique string) to Researcher object.
    ## invariant: self.investigators[x].email == x
    def __init__(self): 
        self.investigators = {}

    def __len__(self):
        return len(self.all())

    def all(self):
        return [pi[1] for pi in self.investigators.items()]

    def lookupPI(self, email):
        if email in self.investigators:
            return self.investigators[email]
        else:
            return None

    def addInvestigator(self, researcher):
        if researcher.email in self.investigators:
            pass # (not doing sanity checking this time...tsk, tsk)
        else:
            self.investigators[researcher.email] = researcher

    def lookupAddInvestigator(self, firstname, lastname, email, institution): # -> Researcher
        if email in self.investigators:
            researcher = self.investigators[email]
            if researcher.firstname != firstname:
                LogWarning("Firstnames do not match for " + email + ": " + str(researcher) + " / " + firstname)
            if researcher.lastname != lastname:
                LogWarning("Lastnames do not match for " + email + ": " + str(researcher) + " / " + lastname)
            if researcher.institution != institution:
                LogWarning("Institutions do not match for " + email + ": " + str(researcher) + " / " + institution)
                researcher.institution = institution # update to new institution!
            return researcher
        else:
            researcher = Researcher(firstname, lastname, email, institution)
            self.investigators[email] = researcher
            return researcher

class Researcher():
    def __init__(self, firstname, lastname, email, institution):
        self.firstname = firstname
        self.lastname = lastname
        self.email = email
        self.institution = institution
        self.projects = []

    def addProject(self, projectID):
        self.projects.append(projectID)

    def display(self):
        return str(self) + "\n   " + ", ".join([str(project) for project in self.projects])

    def __str__(self):
        return self.firstname + " " + self.lastname + " (" + self.institution + ")" + " - " + self.email

class Institution():
    def __init__(self, name, cityname, statename):
        self.name = name
        self.cityname = cityname
        self.statename = statename

    def __str__(self):
        return self.name + " (" + self.cityname + ", " + self.statename + ")"

class Project(): # models.Model):
    def __init__(self, awardID, title, startDate, expirationDate, amount, abstract, 
                 pi, copis, 
                 institution,
                 organizations, programs):
        self.awardID = awardID
        self.title = title
        self.startDate = startDate
        self.expirationDate = expirationDate
        self.amount = amount
        self.abstract = abstract
        self.pi = pi
        self.copis = copis
        self.organizations = organizations
        self.programs = programs
        self.institution = institution
        self.collabs = [] # collaborative proposals

    def allPIs(self):
        return [self.pi] + self.copis

    def isCISE(self):
        return '05050000' in self.organizations

    def isSaTC(self):
        return '8060' in self.programs \
            or self.title.startswith("TC:") or self.title.startswith("CT-") \
            or self.title.startswith("TWC:") or self.title.startswith("EDU:")

    def __str__(self):
        return str(self.awardID) + ": " + self.title # + ' [' + ', '.join([str(collab) for collab in self.collabs]) + ']'
