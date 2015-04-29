import os, string, datetime

from django.db import models
from django_extras.contrib.auth.models import SingleOwnerMixin
from django.contrib.auth.models import User
from django.dispatch import receiver
from utils import format_amount, isSaTC, scope, limitActive, showEmail, memoize, LogWarning, LogMessage

@memoize
def filter_attending(projects):
    return [project 
            for project in projects
            if any([pi.investigator.attendee for pi in project.getPIs()])]

class Institutions(models.Model):
    name = models.CharField(max_length=512)
    shortname = models.CharField(max_length=64)
    cityname = models.CharField(max_length=128)
    statename = models.CharField(max_length=64)

    def showName(self):
        if self.shortname and len(self.shortname) > 0:
            return self.shortname
        else:
            return self.name

    def displayName(self):
        return "<a href=\"/institution/" + str(self.id) + "\">" \
            + self.showName() + "</a>"
    
    def location(self):
        return string.capwords(self.cityname) + ", " + self.statename

    def fullDisplay(self):
        # we use capwords because lots of NSF records use UPPERCASE cities
        return self.displayName() + " (" + self.location() + ")"

class NSFInvestigator(models.Model):
    email = models.CharField(max_length=256)
    firstname = models.CharField(max_length=256)
    lastname = models.CharField(max_length=256)
    # This is used to enable a fixed institution for PIs when desired (needed),
    # but normally need to look up multiples from ProjectPIs
    institution = models.ForeignKey(Institutions, null=True) 
    satc = models.BooleanField(default=False)
    attendee = models.BooleanField(default=False)
    noshow = models.BooleanField(default=False)
    nonpi = models.BooleanField(default=False)
    # projects = models.ManyToManyField(NSFProject, through='ProjectPIs')
    homepage = models.URLField(null=True)

    def hasName(self):
        return (len(self.firstname) + len(self.lastname)) > 2

    @memoize
    def getPrimaryInstitution(self):
        if self.institution:
            return self.institution
        else:
            # assumes the most recent 
            primaryproject = None
            piprojects = ProjectPIs.objects.filter(investigator=self)
            for projectpi in piprojects:
                if not projectpi.project: # no project - there to set institution
                    primaryproject = projectpi
                    break
                if not primaryproject:
                    primaryproject = projectpi
                else:
                    if not projectpi.institution == primaryproject.institution:
                        # prefer active project
                        if not primaryproject.project:
                            primaryproject = projectpi
                            continue
                        if projectpi.project.isActive() and not primaryproject.project.isActive():
                            primaryproject = projectpi
                        elif projectpi.project.isActive() == primaryproject.project.isActive():
                            if projectpi.role == 'PI' and not primaryproject.role == 'PI':
                                primaryproject = projectpi
                            elif projectpi.role == primaryproject.role:
                                if projectpi.project.startDate > primaryproject.project.startDate:
                                    primaryproject = projectpi

            if primaryproject:
                return primaryproject.institution
            else:
                return None

    @memoize
    def getInstitutions(self):
        if self.institution:
            return [self.institution]
        else:
            piprojects = ProjectPIs.objects.filter(investigator=self)
            institutions = sorted(set([project.institution for project in piprojects]))
            return institutions
    
    @memoize
    def displayLinkName(self):
        return "<a href=\"/pi/" + str(self.id) + "\">" + self.displayName() + "</a>"

    @memoize
    def fullDisplay(self):
        res = self.displayLinkName()
        institution = self.getPrimaryInstitution()
        if institution:
            res += " (" + institution.displayName() + ")"
        else:
            pass # res += "NO INSTITUTION!"

        if showEmail():
            res += " " + self.email

        return res

    def displayNameInst(self):
        res = self.displayName()
        institution = self.getPrimaryInstitution()
        if institution:
            res += " (" + institution.showName() + ")" # only for latex: .replace('&','\\&') + ")"
        else:
            pass # res += "NO INSTITUTION!"
        return res

    def displayName(self):
        return self.firstname + " " + self.lastname

class NSFProject(models.Model):
    awardID = models.CharField(max_length=7,primary_key=True)
    title = models.CharField(max_length=256)
    startDate = models.DateField()
    expirationDate = models.DateField()
    amount = models.PositiveIntegerField()
    abstract = models.TextField()
    satc = models.BooleanField(default=False)
    institution = models.ForeignKey(Institutions, null=True)
    pis = models.ManyToManyField(NSFInvestigator, through='ProjectPIs')

    @classmethod
    def selectProjectsFromRequest(cls, request, institution=None):
        startafter = request.GET.get('startafter')
        startbefore = request.GET.get('startbefore')
        endafter = request.GET.get('endafter')
        endbefore = request.GET.get('endbefore')

        if limitActive(request) and not endafter:
            endafter = datetime.date.today().isoformat()

        minamount = request.GET.get('minamount')
        if minamount:
            try:
                minamount = int(minamount)
            except:
                LogWarning("Cannot convert minamount: " + minamount)
                minamount = None

        maxamount = request.GET.get('maxamount')
        if maxamount:
            try:
                maxamount = int(maxamount)
            except:
                LogWarning("Cannot convert maxamount: " + maxamount)
                maxamount = None

        if not institution:
            institution = request.GET.get('institution')
            if institution:
                try:
                    institutionid = int(institution) 
                    institution = Institutions.objects.get(id = institutionid)
                except:
                    LogWarning("Error with institution parameter: " + institution)
                    institution = None

        pi = request.GET.get('pi')
        satc = isSaTC(request)
        attending = (scope(request) == 'attending')
        if attending: satc = True # this is just for limiting processing, but misses non-satc
        return cls.selectProjects(satc=satc, 
                                  attending=attending,
                                  startafter=startafter, 
                                  startbefore=startbefore, 
                                  endafter=endafter, 
                                  endbefore=endbefore,
                                  pi=pi, institution=institution, 
                                  minamount=minamount, 
                                  maxamount=maxamount)

    @classmethod
    def selectProjects(cls, 
                       satc=True, attending=False,
                       startafter=None, startbefore=None, endafter=None, endbefore=None,
                       pi=None, institution=None, minamount=None, maxamount=None):
        projects = cls.objects.order_by('startDate')
        active = False
        explanation = ""

        if endafter == datetime.date.today().isoformat() and not endbefore:
            explanation = "active "
            active = True

        if satc:
            projects = projects.filter(satc=satc)
            explanation += "SaTC projects"
        else:
            explanation += "NSF projects"
            
        if institution:
            projects = projects.filter(institution=institution)
            explanation += " at " + institution.displayName()

        if minamount:
            projects = projects.filter(amount__gte=minamount);
            explanation += " over $" + format_amount(minamount)

        if maxamount:
            projects = projects.filter(amount__lte=maxamount);
            explanation += " under $" + format_amount(maxamount)

        if startafter or startbefore:
            if not startbefore:
                startbefore = '2029-12-31'
                explanation += " starting after " + startafter
            elif not startafter:
                startafter = '1900-01-01'
                explanation += " starting before " + startbefore
            else:
                explanation += " starting between " + startafter + " and " + startbefore
            projects = projects.filter(startDate__range=[startafter, startbefore])

        if endafter or endbefore:
            if not endbefore:
                endbefore = '2029-12-31'
                if not active: 
                    explanation += " ending after " + endafter
            elif not endafter:
                endafter = '1900-01-01'
                explanation += " ending before " + endbefore
            else:
                explanation += " ending between " + endafter + " and " + endbefore
            projects = projects.filter(expirationDate__range=[endafter, endbefore])
            
        projects.order_by('startDate')
 
        if attending:
            projects = filter_attending(projects)
            explanation = str(len(projects)) + " " + explanation + " with registered PI"
        else:
            explanation = str(projects.count()) + " " + explanation

        return projects, explanation

    @memoize
    def isActive(self):
        return self.expirationDate >= datetime.date.today()

    @memoize
    def getPIs(self):
        return ProjectPIs.objects.filter(project=self).order_by('investigator__lastname')

    @memoize
    def displayName(self):
        return self.awardID + ": " + self.title

    @memoize
    def displayLinkId(self):
        return "<a href=\"/project/" + self.awardID + "\">" + self.awardID + "</a>"

    @memoize
    def displayLinkName(self):
        return "<a href=\"/project/" + self.awardID + "\">" + self.displayName() + "</a>"

    # copis = self.copis = copis
    # self.organizations = organizations
    # self.programs = programs
    # self.collabs = [] # collaborative proposals

class ProjectPIs(models.Model):
    investigator = models.ForeignKey(NSFInvestigator)
    project = models.ForeignKey(NSFProject, null=True)
    role = models.CharField(max_length=10, null=True)
    institution = models.ForeignKey(Institutions, null=True)

class CollabProjects(models.Model):
    project1 = models.ForeignKey(NSFProject, related_name='project1')
    project2 = models.ForeignKey(NSFProject, related_name='project2')

class Organizations(models.Model):
    project = models.ForeignKey(NSFProject)
    organization = models.CharField(max_length=8)

class Programs(models.Model):
    project = models.ForeignKey(NSFProject)
    program = models.CharField(max_length=8)

class Words(models.Model):
    word = models.CharField(max_length=64)
    count = models.PositiveIntegerField()
    title = models.BooleanField(default=False)
    project = models.ForeignKey(NSFProject)

class Posters(models.Model):
    title = models.CharField(max_length=256)
    location = models.CharField(max_length=32, null=True)
    project = models.ForeignKey(NSFProject, null=True)

    @memoize
    def showTitle(self):
        if self.project:
            return '<a href="/project/' + self.project.awardID + '">' + self.title + '</a>'
        else:
            return self.title
            
    @memoize
    def getPresenters(self):
        presenters = [poster.presenter for poster in PosterPresenters.objects.filter(poster=self)]
        return presenters

    @memoize    
    def showPresenters(self):
        res = ''.join(['<div class="hanging">' + presenter.fullDisplay() + '</div>' for presenter in self.getPresenters()])
        return res

class PosterPresenters(models.Model):
    poster = models.ForeignKey(Posters)
    presenter = models.ForeignKey(NSFInvestigator)

class Breakout(models.Model):
    number = models.PositiveIntegerField()
    title = models.CharField(max_length=64)
    description = models.TextField()
    location = models.CharField(max_length=32)
    session = models.PositiveIntegerField()

    def sessionTime(self):
        if self.session == 1:
            return "Monday, 1:30-3:00pm"
        elif self.session == 2:
            return "Tuesday, 1:30-3:00pm"
        elif self.session == 3:
            return "Tuesday, 3:30-5:00pm"
        else:
            LogWarning("Bad session time: " + str(self.session))
            return "[Session Error]"

class BreakoutParticipant(models.Model):
    breakout = models.ForeignKey(Breakout)
    pi = models.ForeignKey(NSFInvestigator)
    leader = models.BooleanField(default=False)

class RapidMeeting(models.Model):
    pi1 = models.ForeignKey(NSFInvestigator, related_name='pi1')
    pi2 = models.ForeignKey(NSFInvestigator, related_name='pi2')
    pi3 = models.ForeignKey(NSFInvestigator, null=True, related_name='pi3')
    pi4 = models.ForeignKey(NSFInvestigator, null=True, related_name='pi4')
    round = models.PositiveIntegerField()
    room = models.CharField(max_length=32) 
    location = models.PositiveIntegerField()
    reason = models.CharField(max_length=256)
    score = models.FloatField()

    def getParticipants(self):
        participants = [self.pi1, self.pi2]
        if self.pi3: 
            participants.append(self.pi3)
        if self.pi4: 
            assert self.pi3
            participants.append(self.pi4)
        return participants

    def displayLocation(self):
        if self.room == "Washington Room":
            self.room = "Washington"
        return "<b>#" + str(self.location) + "</b> in <b>" + self.room  + "</b>"

    def latexLocation(self):
        if self.room == "Washington Room":
            self.room = "Washington"
        return "{\\bf \\#" + str(self.location) + "} in {\\bf " + self.room  + "}"
 
    def displayMeeting(self):
        msg = "<tr class=\"personalized\"><td align=center><b>"
        if self.round == 1:
           msg += "3:30pm"
        elif self.round == 2:
           msg += "3:55pm"
        elif self.round == 3:
           msg += "4:20pm"
        elif self.round == 4:
           msg += "4:45pm"
        msg += "</td><td>" + self.displayLocation() + "</td><td>" + ', '.join([pi.displayLinkName() for pi in self.getParticipants()]) + "</td></tr>"
        return msg

    def displayMeetingReason(self):
        msg = "<b>Round " + str(self.round) + "</b> (" + ', '.join([pi.displayLinkName() for pi in self.getParticipants()]) + ")<br>"
        if self.reason == 'dissimilar-topics':
            displayreason = 'Dissimilar research topics (from NSF abstracts)'
        elif self.reason == 'similar-topics':
            displayreason = 'Similar research topics (from NSF abstracts)'
        elif self.reason == 'e-i':
            displayreason = 'Compatible expertise and interests (from registration forms)'
        elif self.reason == 'serve-my-interest':
            displayreason = 'Serve one participants interests well (from registration forms)'
        else:
            displayreason = 'Bug in Dave\'s code'

        msg += "Reason for match: <em>" + displayreason + "</em><br>"
        msg += "Algorithmic score: " + str(self.score) + "<br>"
        return msg

class RapidMeetingEval(models.Model):
    rm = models.ForeignKey(RapidMeeting)
    pi = models.ForeignKey(NSFInvestigator, related_name='pi')

    rpi1 = models.ForeignKey(NSFInvestigator, related_name='rpi1', null=True)
    rpi1present = models.BooleanField(default=False)
    rpi2 = models.ForeignKey(NSFInvestigator, related_name='rpi2', null=True)
    rpi2present = models.BooleanField(default=False)
    rpi3 = models.ForeignKey(NSFInvestigator, related_name='rpi3', null=True)
    rpi3present = models.BooleanField(default=False)

    guessreason = models.CharField(max_length=256, null=True)
    matchquality = models.PositiveIntegerField(null=True)
    comments = models.TextField(null=True)

def upload_to(instance, filename):
    return '%s/%s' % (instance.user.username, filename)

class Document(SingleOwnerMixin, models.Model):
    docfile = models.FileField(upload_to=upload_to)
    user = models.ForeignKey(User)

class TempPdf(SingleOwnerMixin, models.Model):
    url = models.URLField()

@receiver(models.signals.post_delete, sender=Document)
def auto_delete_file_on_delete(sender, instance, **kwargs):
    if instance.docfile:
        if os.path.isfile(instance.docfile.path):
            if instance.docfile.path[-4:] == '.pdf':
                txtPath = instance.docfile.path[:-3] + 'txt'
                if os.path.isfile(txtPath):
                    os.remove(txtPath)
            os.remove(instance.docfile.path)
            
