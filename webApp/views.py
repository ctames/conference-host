from __future__ import division

from django.shortcuts import render, render_to_response, get_object_or_404, redirect
from django.template import RequestContext
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django_extras.contrib.auth.models import SingleOwnerMixin, OwnerMixinManager
from django.forms import MultipleChoiceField, CheckboxSelectMultiple
from django.core.files import File
from django.core.files.temp import NamedTemporaryFile
from django.conf import settings
from django.contrib.auth.models import User
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib.humanize.templatetags.humanize import intcomma
from django.contrib.sites.models import get_current_site
from django.contrib.auth.models import User, AnonymousUser
from django import forms

from models import NSFInvestigator, NSFProject, ProjectPIs, CollabProjects, Words, Institutions, Posters, PosterPresenters, RapidMeeting, Breakout, BreakoutParticipant, RapidMeetingEval

from forms import DocForm, UrlForm, FileChoice
from rating import RatingForm

# from pdf2txt import main
# from processing import process
# from soupextract import extractPdf
# from profilecorpora import MyTextCorpus, Profile

from utils import LogWarning, LogMessage, uniq, format_amount, isSaTC, scope, limitActive, memoize, key_from_email
from nsfmodels import Investigators, Researcher, Project

import os, urllib2, logging, sys, pickle, operator, urllib
import itertools
import json

from django.template import  RequestContext
from django.shortcuts import render_to_response

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[-1].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def LogRequest(request, msg):
    try:
        LogMessage(get_client_ip(request) + ": " + msg)
    except:
        pass

MAX_PAGE = 100

def generate_menu(request):
    menu = """<a href="/">Index</a> &middot;
              <a href="/pis">Investigators</a> &middot; 
              <a href="/projects">Projects</a> &middot; 
              <a href="/institutions">Institutions</a> &nbsp;&nbsp;&nbsp;
              <a href="https://www.usenix.org/conference/satcpi15">Meeting Site</a>
              &nbsp;&mdash;&nbsp;
           """

    currentscope = scope(request)
    
    if currentscope == 'satc':
        menu += "<b>SaTC-Related</b>"
    else:
        menu += '<a href="/scope=satc' + urllib.quote(request.get_full_path()) + '"</a>SaTC-Related</a>'
    menu += ' &middot; '

    if currentscope == 'attending':
        menu += "<b>Registered</b>"
    else:
        menu += '<a href="/scope=attending' + urllib.quote(request.get_full_path()) + '"</a>Registered</a>'

    menu += ' &middot; '

    if currentscope == 'all':
        menu += "<b>All NSF</b>"
    else:
        menu += '<a href="/scope=all' + urllib.quote(request.get_full_path()) + '"</a>All NSF</a>'
    
    menu += ' &nbsp;&mdash;&nbsp; '

    if limitActive(request):
        menu += "<b>Active</b>"
    else:
        menu += '<a href="/active=1' + urllib.quote(request.get_full_path()) + '"</a>Active</a>'

    menu += ' &middot; '

    if limitActive(request):
        menu += '<a href="/active=0' + urllib.quote(request.get_full_path()) + '"</a>All</a>'
    else:
        menu += '<b>All</b>'

    return menu

def generate_error_menu(request):
    return generate_menu(request)

def error_response(request, msg):
    LogWarning(msg)
    return render_to_response(
        'error.html',
        {'message': msg,        
         'menu': generate_error_menu(request), } , 
        context_instance=RequestContext(request))

def login(request):
    return render_to_response(
        'login.html',
        {'message': 'Login for special powers',        
         'menu': generate_error_menu(request), } , 
        context_instance=RequestContext(request)
        )

def logout(request):
    if request.user.id:
        return error_response('Failed to logout!  User ' + request.user.email + ' is still logged in!')
    else:
        return render_to_response(
            'index.html',
            { 'menu': generate_menu(request), },
            context_instance=RequestContext(request))
    
@memoize
def index(request):
    if not request.session.get('scope', None):
        request.session['scope'] = 'satc'

    projects, _ = NSFProject.selectProjects(satc=True, endafter='2014-01-01')
    graph = generate_institution_graph(projects)
    return render_to_response(
        'index.html',
        { 'menu': generate_menu(request), 
          'graphheight': 600,
          'graphwidth': 850,
          'fontsize': 9, # doesn't work with firefox
          'json_str': graph},
        context_instance=RequestContext(request))

def about(request):
    return render_to_response(
        'about.html',
        { 'menu': generate_menu(request), },
        context_instance=RequestContext(request))

def buginfo(request):
    return render_to_response(
        'buginfo.html',
        { 'menu': generate_menu(request), },
        context_instance=RequestContext(request))

def getCollaborators(projects):
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
    return collaborators

def merge_edges(edges):
    index = 0
    while index < len(edges):
        (n1, n2, val) = edges[index]
        # if any later edges have same nodes, update value and remove them
        nindex = index + 1
        while nindex < len(edges):
            (nn1, nn2, nval) = edges[nindex]
            if nn1 == n1 and nn2 == n2:
                val += nval # = max(val, nval) # update to max
                del edges[nindex]
            nindex += 1
        edges[index] = (n1, n2, val)
        index += 1
    
    return edges

def make_edges(edgelist, val):
    return [(n1, n2, val)
            for n1 in edgelist
            for n2 in edgelist
            if not n1 <= n2]

def project_pis(projects):
    return sorted(uniq([ppi.investigator for ppi in itertools.chain.from_iterable([project.getPIs() for project in projects])]),key=lambda r: r.lastname + ' ' + r.firstname)

def check_super_powers(request):
    return request and user_has_superpowers(request.user)

def check_logged_in(request):
    userid = request.user
    
    if not userid:
        return error_response(request, "No user logged in.  Must be logged in to view this page.")

    email = userid.email
    try:
        pi = NSFInvestigator.objects.get(email=email)
        return pi
    except:
        msg = "No PI found for email: " + str(email) + """
<br><p>

To login, you must use the email address associated with your NSF
profile.  You should have received this in an email, but if not you
can find yourself in the <a href="/pis?scope=attending">list of
attending PIs</a>.  If you do not find yourself in that list, or you
are not able to access the email account associated with your NSF
grant, please <a href="mailto:evans@cs.virginia.edu">contact us</a>.

"""
        LogWarning(msg)
        return render_to_response(
            'error.html',
            {'message': msg,        
             'menu': generate_error_menu(request), } , 
            context_instance=RequestContext(request)
            )


def profile(request):
    pi = check_logged_in(request)
    return displayPI(request, pi)

def edit_home_page(request):
    if request.method != 'POST':
        return render_to_response(
            'error.html',
            {'message': 'POST request expected',        
             'menu': generate_error_menu(request), } , 
            context_instance=RequestContext(request)
            )

    pi = check_logged_in(request)
    url = request.POST['homepageURL']

    # if not url:
    #return render_to_response(
    #'error.html',
    #            {'message': 'Missing URL input',
    #'menu': generate_error_menu(request), } , 
    #context_instance=RequestContext(request)
    #)

    pi.homepage = url
    pi.save()
    return displayPI(request, pi)

@memoize
def generate_graph(projects, pis):
    edges = []

    for project in projects:
        cols = []
        for copi in getCollaborators([project]):
            if copi in pis:
                coindex = pis.index(copi)
                cols.append(coindex)

        # collabs = uniq([c.project2 for c in CollabProjects.objects.filter(project1 = project)])
        # for collab in collabs:
        #    collabinst = collab.institution
        #    if not collabinst in pis:
        #        pis.append(collabinst)
        #    cols.append(institutions.index(collabinst))

        val = 1
        if project.satc:
            val = 2
        edges += make_edges(cols, val)

    edges = merge_edges(edges)
    json_obj = {'nodes': [], 'links': []}

    for pi in pis:
        if type(pi) is NSFInvestigator:
            desc = {'name': pi.displayName(), 'group': 1, 'pid': pi.id }
        elif type(pi) is Institution:
            desc = {'name': pi.showName(), 'group': 1, 'instid': pi.id }
        else:
            desc = {'name': str(pi), 'group': 1}

        json_obj['nodes'].append(desc)

    for edge in edges:
        desc = {"source": edge[0], "target": edge[1], "value": edge[2]}
        json_obj['links'].append(desc)

    json_str = json.dumps(json_obj)
    return json_str

def generate_institution_graph(projects):
    edges = []
    institutions = []
    for project in projects:
        cols = []
        institution = project.institution
        if not institution in institutions:
            institutions.append(institution)
        collabs = uniq([c.project2 for c in CollabProjects.objects.filter(project1 = project)])
        for collab in collabs:
            collabinst = collab.institution
            if not collabinst in institutions:
                institutions.append(collabinst)
            cols.append(institutions.index(collabinst))

        val = 1
        val += int(project.amount / 1000000)
        if project.satc:
            val *= 2
        edges += make_edges(cols, val)

    edges = merge_edges(edges)
    json_obj = {'nodes': [], 'links': []}

    for institution in institutions:
        desc = {'name': institution.showName(), 'group': 1, 'instid': institution.id }
        json_obj['nodes'].append(desc)

    for edge in edges:
        desc = {"source": edge[0], "target": edge[1], "value": edge[2]}
        json_obj['links'].append(desc)

    json_str = json.dumps(json_obj)
    return json_str

def pigraph(request):
    projects, explanation = NSFProject.selectProjectsFromRequest(request, None)
    pis = project_pis(projects)

    json_str = generate_graph(tuple(projects), tuple(pis))

    return render_to_response(
            'pigraph.html',
            {'json_str': json_str,
             'explanation': explanation,
             'menu': generate_menu(request), },
            context_instance=RequestContext(request))

def pis(request, max_page=MAX_PAGE):
    satc = isSaTC(request)
    attending = (scope(request) == 'attending')

    pis = NSFInvestigator.objects
    explanation = "NSF Investigators"

    if satc:
        pis = pis.filter(satc=True)
        explanation += " involved in SaTC projects"

    if attending:
        pis = pis.filter(attendee=True)
        explanation += " attending SaTC PIs meeting"

    pis = pis.extra(select={'lower_name': 'lower(lastname)'}).order_by('lower_name', 'firstname')

    explanation = str(len(pis)) + " " + explanation

    if max_page < len(pis) < 1.85 * max_page:
        max_page = 2 * max_page # don't paginate 

    paginator = Paginator(pis, max_page)
    page = request.GET.get('page')
    if page == 'all':
        showpis = pis
    else:
        try:
            showpis = paginator.page(page)
        except PageNotAnInteger:
            showpis = paginator.page(1)
        except EmptyPage:
            showpis = paginator.page(paginator.num_pages)

    return render_to_response(
        'pis.html',
        {'pis': showpis, 
         'explanation': explanation,
         'menu': generate_menu(request),
         'paginate': len(pis) > len(showpis),
         'description': "NSF SaTC" if satc else "NSF" },
        context_instance=RequestContext(request))

def institutions(request, max_page=MAX_PAGE):
    title = 'Institutions'
    projects, explanation = NSFProject.selectProjectsFromRequest(request)
    institutions = uniq([project.institution for project in projects])
    institutions.sort(key=lambda inst: inst.name)
    explanation = str(len(institutions)) + " institutions hosting " + explanation 

    if max_page < len(institutions) < 1.85 * max_page:
        max_page = 2 * max_page # don't paginate 

    paginator = Paginator(institutions, max_page)
    page = request.GET.get('page')

    if page == 'all':
        showinstitutions = institutions
    else:
        try:
            showinstitutions = paginator.page(page)
        except PageNotAnInteger:
            showinstitutions = paginator.page(1)
        except EmptyPage:
            showinstitutions = paginator.page(paginator.num_pages)

    return render_to_response(
        'institutions.html',
        {'title': title,
         'menu': generate_menu(request),
         'explanation': explanation,
         'paginate': len(institutions) > len(showinstitutions),
         'institutions': showinstitutions },
        context_instance=RequestContext(request))

def posterpresenters(request):
    explanation = ""
    presenters = PosterPresenters.objects.order_by('presenter__lastname', 'presenter__firstname')
    explanation = str(presenters.count()) + " poster presenters" + explanation 

    return render_to_response(
        'posterpresenters.html',
        {'title': 'SaTC Poster Presenters',
         'explanation': explanation,
         'menu': generate_menu(request),
         'presenters': presenters,
         },
        context_instance=RequestContext(request))

def posters(request):
    explanation = ""
    posters = Posters.objects.all().order_by('title')
    explanation = str(posters.count()) + " posters" + explanation 

    return render_to_response(
        'posters.html',
        {'title': 'SaTC Posters',
         'explanation': explanation,
         'menu': generate_menu(request),
         'posters': posters,
         },
        context_instance=RequestContext(request))

def projects(request, max_page=MAX_PAGE):
    projects, explanation = NSFProject.selectProjectsFromRequest(request, None)
    satc = isSaTC(request)
    title = "SaTC Projects" if satc else "NSF Projects"

    if max_page < len(projects) < 1.85 * max_page:
        max_page = 2 * max_page # don't paginate 

    paginator = Paginator(projects, max_page)
    page = request.GET.get('page')

    if page == 'all':
        showprojects = projects
    else:
        try:
            showprojects = paginator.page(page)
        except PageNotAnInteger:
            showprojects = paginator.page(1)
        except EmptyPage:
            showprojects = paginator.page(paginator.num_pages)

    return render_to_response(
        'projects.html',
        {'title': title,
         'menu': generate_menu(request),
         'projects': showprojects,
         'paginate': len(projects) > len(showprojects),
         'explanation': explanation},
        context_instance=RequestContext(request))

def word(request):
    satc = isSaTC(request)
    allwords = {}
    words = Words.objects.filter(title=titles,project__satc=satc).order_by('count')
    for word in words:
        if word.word in allwords:
            allwords[word.word] = allwords[word.word] + word.count
        else:
            allwords[word.word] = word.count

    wordlist = []
    for word, count in sorted(allwords.items(), key=lambda t: t[1], reverse=True):
        wordlist.append((word, count))
        if len(wordlist) > max: break

    return render_to_response(
        'words.html',
        { 'words': wordlist, 'description': "At a Loss for",         
          'menu': generate_menu(request),
          },
        context_instance=RequestContext(request)
        )

def words(request, titles, max=200, satc=True):
    allwords = {}
    words = Words.objects.filter(title=titles,project__satc=satc).order_by('count')
    for word in words:
        if word.word in allwords:
            allwords[word.word] = allwords[word.word] + word.count
        else:
            allwords[word.word] = word.count

    wordlist = []
    for word, count in sorted(allwords.items(), key=lambda t: t[1], reverse=True):
        wordlist.append((word, count))
        if len(wordlist) > max: break

    return render_to_response(
        'words.html',
        { 'words': wordlist, 'description': "At a Loss for",         
          'menu': generate_menu(request), },
        context_instance=RequestContext(request)
        )

def piEmail(request, email):
    try:
        pi = NSFInvestigator.objects.get(email=email)
    except:
        msg = "No PI found for email: " + email
        LogWarning(msg)
        return render_to_response(
            'error.html',
            {'message': msg,        
             'menu': generate_error_menu(request), } , 
            context_instance=RequestContext(request)
        )

    return displayPI(request, pi)

def breakouts(request):
    breakouts = Breakout.objects.order_by('number')

    return render_to_response(
        'breakouts.html',
        {
            'menu': generate_menu(request),
            'breakouts': breakouts,
         },
        context_instance=RequestContext(request)
    )

def breakout(request, bid):
    LogRequest(request, "Breakout: " + str(bid))
    breakout = Breakout.objects.filter(number=bid)
    if breakout.count() < 1:
        msg = "No breakout for id: " + str(bid)
        LogWarning(msg)
        return render_to_response(
            'error.html',
            {'message': msg,        
             'menu': generate_error_menu(request), } , 
            context_instance=RequestContext(request)
        )
    assert breakout.count() == 1
    breakout = breakout[0]
    
    participantobjs = BreakoutParticipant.objects.filter(breakout=breakout)
    pis = [participant.pi for participant in participantobjs if not participant.leader]
    leaders = [participant.pi for participant in participantobjs if participant.leader]
    pis.sort(key=lambda r: r.lastname + ' ' +  r.firstname)
    leaders.sort(key=lambda r: r.lastname + ' ' +  r.firstname)

    return render_to_response(
        'breakout.html',
        {
            'menu': generate_menu(request),
            'breakout': breakout,
            'leaders': leaders,
            'pis': pis,
         },
        context_instance=RequestContext(request)
    )


def allrms(request):
    if not check_super_powers(request):
        return error_response(request, "Super powers required!")

    rm = RapidMeeting.objects.order_by('id')

    return render_to_response(
        'allrms.html',
        {
            'menu': generate_menu(request),
            'rms': rm,
         },
        context_instance=RequestContext(request)
    )

def allratings(request):
    if not check_super_powers(request):
        return error_response(request, "Super powers required!")

    rme = RapidMeetingEval.objects.order_by('id')
                
    return render_to_response(
        'allrmes.html',
        {
            'menu': generate_menu(request),
            'rmes': rme,
         },
        context_instance=RequestContext(request)
    )
    

def schedule(request, email):
    # TODO: check logged in!
    LogRequest(request, "View schedule: " + email)
        
    try:
        pid = int(email)
        pi = NSFInvestigator.objects.get(id=pid)
    except:
        try:
            pi = NSFInvestigator.objects.get(email=email)
        except:
            msg = "No PI found for email: " + email
            LogWarning(msg)
            return render_to_response(
                'error.html',
                {'message': msg,        
                 'menu': generate_error_menu(request), } , 
                context_instance=RequestContext(request)
                )
    
    # rapid meetings 
    # this is kludgey...should have used a separate table
    rm = RapidMeeting.objects.filter(pi1=pi) | RapidMeeting.objects.filter(pi2=pi) | RapidMeeting.objects.filter(pi3=pi) | RapidMeeting.objects.filter(pi4=pi)

    rm = rm.order_by('round')
    # lots of sanity checking to do here...

    posterobj = PosterPresenters.objects.filter(presenter=pi)
    if posterobj:
        poster = posterobj[0].poster
    else:
        poster = None

    breakout1 = None
    breakout2 = None
    breakout3 = None
    breakoutleader = False
    breakout1leader = False
    breakout2leader = False
    breakout3leader = False

    breakouts = BreakoutParticipant.objects.filter(pi=pi)

    for bobj in breakouts:
        breakout = bobj.breakout
        leader = bobj.leader
        if leader:
            breakoutleader = True

        if breakout.session == 1:
            assert not breakout1
            breakout1 = breakout
            breakout1leader = leader
        elif breakout.session == 2:
            assert not breakout2
            breakout2 = breakout
            breakout2leader = leader
        elif breakout.session == 3:
            assert not breakout3
            breakout3 = breakout
            breakout3leader = leader
        else:
            LogWarning("Bad breakout session: " + breakout.title)

    return render_to_response(
        'schedule.html',
        {'pi': pi, 
         'menu': generate_menu(request),
         'rm': rm,
         'poster': poster,
         'breakout1': breakout1,
         'breakout2': breakout2,
         'breakout3': breakout3,
         'breakoutleader': breakoutleader,
         'breakout1leader': breakout1leader,
         'breakout2leader': breakout2leader,
         'breakout3leader': breakout3leader,
         },
        context_instance=RequestContext(request)
    )

def user_has_superpowers(userid):
    try:
        return userid.email == 'evans@cs.virginia.edu'
    except:
        return False

def getPI(id):
    return NSFInvestigator.objects.get(id=id)

def displayReason(reason):
    if reason == 'dissimilar-topics':
        displayreason = 'Dissimilar research topics (from NSF abstracts)'
    elif reason == 'similar-topics':
        displayreason = 'Similar research topics (from NSF abstracts)'
    elif reason == 'e-i':
        displayreason = 'Compatible expertise and interests (from registration forms)'
    elif reason == 'serve-my-interest':
        displayreason = 'Serve one participants interests well (from registration forms)'
    elif reason == 'bug':
        displayreason = '<span class="bug">Bug in implementation</span> <span class="editlink"><a href="/buginfo">[More Info]</a></span>'
    else:
        displayreason = 'Bug in Dave\'s code'
    return displayreason

def submitrating(request, rmid, email=None):
    try: 
        rfmeeting = RapidMeeting.objects.get(id=rmid)
    except:
        msg = "Invalid meeting id: " + str(rmid)
        LogWarning(msg)
        return render_to_response(
            'error.html',
            {'message': msg, 
             'menu': generate_error_menu(request),
             } , 
            context_instance=RequestContext(request)
        )

    try:
        pid = int(email)
        pi = NSFInvestigator.objects.get(id=pid)
    except:
        try:
            pi = NSFInvestigator.objects.get(email=email)
        except:
            msg = "No PI found for email: " + email
            LogWarning(msg)
            return render_to_response(
                'error.html',
                {'message': msg,        
                 'menu': generate_error_menu(request), } , 
                context_instance=RequestContext(request)
                )

    if request.method != 'POST':
        return error_response(request, 'POST request expected')

    rpi1 = None
    rpi1present = False
    rpi2 = None
    rpi2present = False
    rpi3 = None
    rpi3present = False

    if 'participants' in request.POST:
        participants = request.POST.getlist('participants')
        ## yuck!  not for consumption by cs101 students...
        if len(participants) >= 1:
            try:
                rpi1 = getPI(participants[0])
            except:
                return error_response(request, 'No PI found for: ' + participants[0])
            rpi1present = True
        if len(participants) >= 2:
            rpi2 = getPI(participants[1])
            rpi2present = True
        if len(participants) >= 3:
            rpi3 = getPI(participants[2])
            rpi3present = True


    if 'guessreason' in request.POST:
        guessreason = request.POST['guessreason']
    else:
        guessreason = None

    if 'matchquality' in request.POST:
        try:
            matchquality = int(request.POST['matchquality'])
        except:
            msg = "Cannot convert quality to value: " + request.POST['matchquality']
            LogWarning(msg)
            return render_to_response(
                'error.html',
                {'message': msg,        
                 'menu': generate_error_menu(request), } , 
                context_instance=RequestContext(request)
                )
    else:
        matchquality = None

    if 'comments' in request.POST:
        comments = request.POST['comments']
    else:
        comments = None

    msg = ""
    oldrme = RapidMeetingEval.objects.filter(rm=rfmeeting, pi=pi)
    if oldrme.count() > 0:
        LogWarning("Duplicate rating recieved.  This rating will replace previous rating: " + rfmeeting.displayMeetingReason() + " / pi: " + pi.displayName())
        
    rme = RapidMeetingEval.objects.create(rm=rfmeeting,
                                          pi=pi,
                                          rpi1=rpi1, rpi1present=rpi1present,
                                          rpi2=rpi2, rpi2present=rpi2present,
                                          rpi3=rpi3, rpi3present=rpi3present,
                                          guessreason=guessreason,
                                          matchquality=matchquality,
                                          comments=comments)
    rme.save()

    if rfmeeting.round < 4:
        nextround = rfmeeting.round + 1
        nextmeeting = RapidMeeting.objects.filter(round=nextround, pi1=pi) \
            | RapidMeeting.objects.filter(round=nextround, pi2=pi) \
            | RapidMeeting.objects.filter(round=nextround, pi3=pi) \
            | RapidMeeting.objects.filter(round=nextround, pi4=pi) 
        if nextmeeting.count() == 1:
            return ratemeeting(request, nextmeeting[0].id, pi.email)
        else:
            msg = "No meeting found for round " + str(nextround)
            LogWarning(msg)
            return render_to_response(
                'error.html',
                {'message': msg, 
                 'menu': generate_error_menu(request),
                 } , 
                context_instance=RequestContext(request))
    else:
        rmos = RapidMeeting.objects.filter(pi1=pi) | RapidMeeting.objects.filter(pi2=pi) | RapidMeeting.objects.filter(pi3=pi) | RapidMeeting.objects.filter(pi4=pi)
        rmos = rmos.order_by('round')

        report = ""

        for rfm in rmos:
            report += "<p><b>Meeting " + str(rfm.round) + "</b><blockquote>"
            ##
            # report += str(rfm.id) + " for " + str(pi.id) + "</br>"
            report += ', '.join([pid.displayLinkName() for pid in rfm.getParticipants()]) + "<br>"

            realreason = rfm.reason
            if realreason == 'similar-topics' or realreason == 'dissimilar-topics':
                realreason = 'bug'

            rmes = RapidMeetingEval.objects.filter(pi = pi, rm=rfm) 

            if rmes.count() == 0:
                rme = None
                report += "<span class=\"warning\">Error: no evaluation for: " + str(rfm.id) + " by " + str(pi.id) + ".</span><br>"
            elif rmes.count() > 1:
                report += "<span class=\"warning\">Warning: multiple ratings found for this meeting.  Using last rating.</span><br>"
                rme = rmes.latest('id')
                # assert rme.id == rfm.id
            else:
                rme = rmes[0]

            if rme:
                assert rme.rm == RapidMeeting.objects.get(id=rfm.id)
                assert rme.rm == rfm

                if not rme.guessreason:
                    report += "No guessed reason recorded"
                else:
                    if rme.guessreason == 'bug':
                        report += "Guessed reason: Bug in implementation"
                    else: 
                        report += "Guessed reason: " + displayReason(rme.guessreason)
                    
            report += "<br>Actual reason: " + displayReason(realreason) 
            if not realreason == 'bug': report += " (Score: " + str(rfm.score) + ")"
            report += "</br></blockquote></p>"

        return render_to_response(
            'finishedratings.html',
            {
             'menu': generate_error_menu(request),
             'pi': pi,
             'report': report,
             } , 
            context_instance=RequestContext(request)
            )

def ratemeeting(request, rmid, email=None):
    try: 
        rfmeeting = RapidMeeting.objects.get(id=rmid)
    except:
        msg = "Invalid meeting id: " + str(rmid)
        LogWarning(msg)
        return render_to_response(
            'error.html',
            {'message': msg, 
             'menu': generate_error_menu(request),
             } , 
            context_instance=RequestContext(request)
        )

    try:
        pid = int(email)
        pi = NSFInvestigator.objects.get(id=pid)
    except:
        try:
            pi = NSFInvestigator.objects.get(email=email)
        except:
            msg = "No PI found for email: " + email
            LogWarning(msg)
            return render_to_response(
                'error.html',
                {'message': msg,        
                 'menu': generate_error_menu(request), } , 
                context_instance=RequestContext(request)
                )

    participants = rfmeeting.getParticipants()

    try:
        participants.remove(pi)
    except ValueError:
        msg = "Invalid request: can only rate meetings in which you were a participant!"
        msg += "\n<br><p>Meeting: " + rfmeeting.displayMeeting() + " </p>"
        LogWarning(msg)
        return render_to_response(
            'error.html',
            {'message': msg, 
             'menu': generate_error_menu(request),
             } , 
            context_instance=RequestContext(request)
        )

    ratingform = RatingForm()    
    ratingform.fields['participants'].choices = [(str(pname.id), 
                                                  pname.displayNameInst() if not pname.noshow 
                                                  else pname.displayNameInst() + ' [Did not attend meeting]') 
                                                 for pname in participants]
    ratingform.initial['participants'] = [str(pname.id) for pname in participants if not pname.noshow]

    return render_to_response(
        'ratedates.html',
        {'pi': pi, 
         'rfid': rfmeeting.id,
         'round': rfmeeting.round,
         'menu': generate_menu(request),
         'form': ratingform,
         },
        context_instance=RequestContext(request)
    )

def after(request, email=None):
    ## todo: support token login

    allgood = False
    tok = request.GET.get('tok')
    if not email:
        return error_response(request, "No email provided.")
    if not tok:
        return error_response(request, "No authentication token provided.")

    if tok == key_from_email(email):
        # all good!
        allgood = True
        request.user = User(email=email,username=email)
    else:
        # return error_response(request, "Expected token: " + str(key_from_email(email)) + " got token " + str(tok) + " for email: " + str(email))
        return error_response(request, "Bad token provided! (This server is unhackable.  Please don't try!)")

    if not allgood and not request.user.is_authenticated(): 
        if email:
            LogRequest(request, "Rate meetings for: " + email)
            msg = "To see this page, you must login as " + email + """.  Authentication is done using Mozilla's <a href="https://www.mozilla.org/en-US/persona/">Persona</a> single sign-on service with your NSF email address."""
        else:
            msg = """To see this page, you must be logged in.  Authentication is done using Mozilla's <a href="https://www.mozilla.org/en-US/persona/">Persona</a> single sign-on service with your NSF email address."""

        return render_to_response(
            'login.html',
            {'message': msg,        
             'menu': generate_error_menu(request), } , 
            context_instance=RequestContext(request)
            )

    userid = request.user

    if not userid.email == email and not user_has_superpowers(request.user):
        return render_to_response(
            'error.html',
            {'message': "Authentication error: email mismatch.",        
             'menu': generate_error_menu(request), } , 
            context_instance=RequestContext(request)
            )
    try:
        pid = int(email)
        pi = NSFInvestigator.objects.get(id=pid)
    except:
        try:
            pi = NSFInvestigator.objects.get(email=email)
        except:
            msg = "No PI found for email: " + email
            LogWarning(msg)
            return render_to_response(
                'error.html',
                {'message': msg,        
                 'menu': generate_error_menu(request), } , 
                context_instance=RequestContext(request)
                )
    
    rm = RapidMeeting.objects.filter(pi1=pi) | RapidMeeting.objects.filter(pi2=pi) \
         | RapidMeeting.objects.filter(pi3=pi) | RapidMeeting.objects.filter(pi4=pi)
    rm = rm.order_by('round')

    if rm.count() == 0:
        return error_response(request, "No meetings to rate for " + pi.displayName())
    else:
        return ratemeeting(request, rm[0].id, pi.email)

def pi(request, userid):
    LogRequest(request, "pi: " + str(userid))
    try:
        pi = NSFInvestigator.objects.get(id=userid)
    except:
        msg = "No PI found for id: " + str(userid)
        LogWarning(msg)
        return render_to_response(
            'error.html',
            {'message': msg, 
             'menu': generate_error_menu(request),
             } , 
            context_instance=RequestContext(request)
        )

    return displayPI(request, pi)

def set_scope(request, scope, url):
    assert scope == 'satc' or scope == 'all' or scope == 'attending'
    request.session['scope'] = scope 

    # this is really silly...I'm sure there is a better way, but can't figure out how
    return render_to_response(
        'redirect.html',
        { 'redirect': "http://" + get_current_site(request).domain + "/" + url },
        context_instance=RequestContext(request))

def set_active(request, active, url):
    assert active == '0' or active == '1'
    request.session['active'] = bool(active == '1')

    # this is really silly...I'm sure there is a better way, but can't figure out how
    return render_to_response(
        'redirect.html',
        { 'redirect': "http://" + get_current_site(request).domain + "/" + url },
        context_instance=RequestContext(request))

def displayPI(request, pi):
    piprojects = ProjectPIs.objects.filter(investigator=pi)
    projects = sorted(uniq([p.project for p in piprojects if p.project]), key=lambda proj: proj.startDate)
    totalawarded = format_amount(sum([project.amount for project in projects]))

    collaborators = getCollaborators(projects)
    try:
        collaborators.remove(pi)
    except:
        LogWarning("Not a self-collaborator: " + pi.fullDisplay())

    institutions = pi.getInstitutions()

    return render_to_response(
        'pi.html',
        {'pi': pi, 
         'menu': generate_menu(request),
         'totalawarded': totalawarded,
         'institutions': institutions,
         'projects': projects, 
         'collaborators': collaborators},
        context_instance=RequestContext(request)
    )

def institution(request, institutionid):
    satc = isSaTC(request)
    try:
        institution = Institutions.objects.get(id = institutionid)
    except:
        msg = "No institution for id: " + str(institutionid) 
        LogWarning(msg)
        return render_to_response('error.html',
                                  {'message': msg,
                                   'menu': generate_error_menu(request),
                                   },
                                  context_instance=RequestContext(request))

    projects, explanation = NSFProject.selectProjectsFromRequest(request, institution=institution)

    totalawarded = format_amount(sum([project.amount for project in projects]))

    pis = project_pis(projects)
    if scope(request) == 'attending': pis = [pi for pi in pis if pi.attendee]
    pis.sort(key=lambda r: r.lastname + ' ' +  r.firstname)

    # include all projects with (relevant) PIs
    # use projects only for scoped projects
    piprojects, _ = NSFProject.selectProjects(satc=False, institution=institution)
    graph = generate_graph(tuple(piprojects), tuple(project_pis(projects)))

    return render_to_response(
        'institution.html',
        {'institution': institution,
         'menu': generate_menu(request),
         'satc': satc,
         'pis': pis,
         'projects': projects,
         'json_str': graph,
         'explanation': explanation,
         'totalawarded': totalawarded },
        context_instance=RequestContext(request))

def project(request, abstractid):
    LogRequest(request, "project: " + str(abstractid))
    try:
        project = NSFProject.objects.get(awardID = abstractid)
    except:
        msg = "No project found for award ID: " + str(abstractid) 
        LogWarning(msg)
        return render_to_response('error.html',
                                  {'message': msg,
                                   'menu': generate_error_menu(request),
                                   },
                                  context_instance=RequestContext(request))
                                 
    pis = project.getPIs() 

    collabs = uniq([c.project2 for c in CollabProjects.objects.filter(project1 = project)])
    collabpis = uniq([(p.investigator, collab)
                      for collab in collabs
                      for p in ProjectPIs.objects.filter(project=collab)])
    collabpis.sort(key=lambda r: r[0].lastname)

    amount = format_amount(project.amount)

    return render_to_response(
        'project.html',
        {'project': project, 
         'menu': generate_menu(request),
         'amount': amount,
         'pis': pis, 'collabs': collabs, 'collabpis': collabpis},
        context_instance=RequestContext(request)
    )
