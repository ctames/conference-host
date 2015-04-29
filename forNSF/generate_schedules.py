###
### generate_schedules.py
###

import os
import sys
import csv
import random
import datetime
from utils import LogWarning, LogMessage
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "webApp.settings")
django.setup()

from django.shortcuts import render
from django.db import transaction

from webApp.models import NSFInvestigator, NSFProject, ProjectPIs, CollabProjects, \
                             Organizations, Programs, Words, Institutions, \
                             RapidMeeting, PosterPresenters, BreakoutParticipant
import json
from pprint import pprint

def generate_row(time, room, event):
    return "\\row{" + time + "}{" + room + "}{" + event + "}\n"

def generate_brow(time, room, event):
    return "\\brow{" + time + "}{" + room + "}{" + event + "}\n"

def generate_prow(time, room, event):
    return "\\prow{" + time + "}{" + room + "}{" + event + "}\n"

def generate_block(msg):
    return "\\end{tabular} \\begin{addmargin}[2em]{2em}\\small\n" + msg + "\\end{addmargin} \\begin{tabular}{x{1.5in}x{1.5in}x{3.5in}}"

def latex_schedule(pi, rm, poster, breakout1, breakout2, breakout3,
                   breakoutleader, breakout1leader, breakout2leader, breakout3leader):
    LogMessage("Schedule for: " + pi.email + " . " + str(pi.id))
    msg = """
\\documentclass[11pt, letterpaper]{article}
\\input{preamble.tex}
\\begin{document}

\\begin{center}
"""
    msg += "{\\colorbox{black}{\\parbox{\\dimexpr\\textwidth-2\\fboxsep\\relax}{\\centering\\textcolor{white}{\\quad {\\large Schedule for {\\bf " + pi.displayName() + "}}}}}}\n"
    msg += """
\\end{center}

Welcome to the National Science Foundation Secure and Trustworthy
Cyberspace (SaTC) Principal Investigators' Meeting!  Your personal
schedule is below.  See the conference program or website for more
details.  You can also find a web version of your personal schedule
at: \\begin{center}\\url{http://www.rematchr.org/schedule/"""
    msg += pi.email + "}\\end{center}\n\n"
    msg += "\\bday{Monday 5 January 2015}{\n"
    msg += generate_row('8:30-9:15am', 'Regency EF', 'Welcome: Jim Kurose and Jeryl Mumpower (NSF)')
    msg += generate_row('9:15-10:30am', 'Regency EF', 'Keynote: \\ptitle{What\'s on the Horizon?}, Latanya Sweeney (Harvard University)')
    msg += generate_brow('10:30-11:00am','Regency Foyer','Break')
    msg += generate_row('11am-12:15pm','Regency EF','Panel: \\ptitle{Ethics in Security and Privacy Research} (Michael Bailey, Lujo Bauer, Stevan Savage; Rahul Telang)')
    msg += generate_brow('12:15-1:30pm','Independence Center','Lunch')

    if breakout1:
        msg += generate_prow('1:30-3:00pm', breakout1.location, 'Breakout ' + str(breakout1.number) + ": \\ptitle{" + breakout1.title + '}')
        if breakout1leader:
            print "**** BREAKOUT LEADER ****"
            msg += generate_block('Thank you for leading this breakout discussion.  You should find the room set up with a projector and screen, flip chart, and power strips.  If you need anything else for your breakout, please let the conference staff know right away.')
    else:
        msg += generate_row('1:30-3:00pm','Regency EF', 'Panel: \\title{Educating Everyone} (Diana Burley, Shriram Krishnamurthi, Zachary Peterson; Victor Piotrowski)')

    msg += generate_brow('3:00-3:30pm','Regency Foyer','Break')

    if rm:
        msg += generate_prow('3:30-5:15pm', '{\\em various locations}', 
                            'Rapid-Fire Cross Collaborations')
        for rfm in rm:
            if rfm.round == 1: time = "3:30-3:50pm"
            elif rfm.round == 2: time = "3:55-4:15pm"
            elif rfm.round == 3: time = "4:20-4:40pm"
            elif rfm.round == 4: time = "4:45-5:15pm"
            else: assert False
            msg += generate_row(time, rfm.latexLocation(), ', '.join([pi.displayNameInst() for pi in rfm.getParticipants()]))

        msg += generate_block("""
The goal of the rapid-fire cross collaborations is to instigate
discussions that would not otherwise happen and that may lead to
useful collaborations, or at least gaining insights and contacts. The
matches were generated according to several different criteria: (1)
expertise-interest compatibility (based on registration forms you
submited), (2) selfishly serving one individuals interests as well as
possible, (3) similar topics based on text analysis of NSF abstracts,
and (4) dis-similar topics based on text analysis of NSF abstract.
The matches you have may not cover all of these criteria, they are
selected to maximize some overall metrics.  After the meeting, you'll
be able to see why you were matched for each meeting round.  If you
are at a loss for how to get a conversation going, you can try to
figure out which of the four criteria were the reason you were
matched.
""")

    else:
        msg += generate_block("No rapid-fire cross collaborations scheduled.  If you would like to participate in ad-hoc rapid matching, go to headquarters in Regency EF.")

        
    if poster:
        msg += generate_prow('6:00-8:00pm', 'Independence Center', 'Present poster: \\ptitle{' + poster.title + '}')
        msg += generate_block("Easels and poster boards will be provided.  Poster locations are not assigned; you may set up your poster at any open location.")
    else:
        msg += generate_row('6:00-8:00pm', 'Independence Center', 'Poster Session and Reception')


    msg += "} \n" # end dayschedule

    msg += "\\clearpage\n"
    msg += "\\bday{Tuesday 6 January 2015}{\n"
    msg += generate_row('8:30-9:00am', 'Regency EF', 'Opening: Keith Marzullo and Michael Vogelius (NSF)')
    msg += generate_row('9:00-9:15am', 'Regency EF', 'SaTC Programmatics, Jeremy Epstein (NSF)')
    msg += generate_row('9:15-10:30am','Regency EF', 'Keynote: \\ptitle{T.S. Kuhn Revisited}, Dan Geer (In-Q-Tel)')
    msg += generate_brow('10:30-11:00am','Regency Foyer','Break')
    msg += generate_row('11am-12:15pm', 'Regency EF', 'Panel: Ideas to Innovations (Farnam Jahanian, Angelos Stavrou, Giovanni Vigna; Patrick Traynor)')

    msg += generate_brow('12:15-1:30pm', 'Independence Center', 'Lunch')

    if breakout2:
        msg += generate_prow('1:30-3:00pm', breakout2.location, 'Breakout ' + str(breakout2.number) + ": \\ptitle{" + breakout2.title + '}')
        if breakout2leader:
            print "**** BREAKOUT LEADER ****"
            msg += generate_block('Thank you for leading this breakout discussion.  You should find the room set up with a projector and screen, flip chart, and power strips.  If you need anything else for your breakout, please let the conference staff know right away.')
    else:
        msg += generate_row('1:30-3:00pm', 'Regency EF', 'Panel: \\ptitle{Security and Privacy Challenges in Health Informatics} (Xiaoqian Jiang, David Kotz, XiaoFeng Wang; Elaine Shi)')

    msg += generate_brow('3:00-3:30pm','Regency Foyer', 'Break')

    if breakout3:
        msg += generate_prow('1:30-3:00pm', breakout3.location, 'Breakout ' + str(breakout3.number) + ": \\ptitle{" + breakout3.title + '}')
        if breakout3leader:
            print "**** BREAKOUT LEADER ****"
            msg += generate_block('Thank you for leading this breakout discussion.  You should find the room set up with a projector and screen, flip chart, and power strips.  If you need anything else for your breakout, please let the conference staff know right away.')
    else:
        msg += generate_row('3:30-5:00pm','Regency EF', 'Panel: \\ptitle{Future of Privacy} (Tamara Denning, Apu Kapadia, Arvind Narayanan; Christopher Clifton)')

    msg += generate_row('5:30-7:30pm','Potomac Rooms','Birds-of-a-Feather Sessions (signup to host a BoF at the registration desk)')
    msg += "} \n" # end dayschedule
    msg += "\\par \n \\par \n"
    msg += "\\bday{Wednesday 7 January 2015}{\n"
    msg += generate_row('8:30-9:15am','Regency EF','Opening: Pramod Khargonekar and Joan Ferrini-Mundy (NSF)')
    msg += generate_row('9:15-10:30am','Regency EF','Keynote: \\ptitle{The Coming Design Wars}, Deirdre Mulligan (UC Berkeley)')

    if breakoutleader:
        msg += generate_block('As breakout leader, you or someone else representing your breakout should be prepared to present a 4-minute report on your breakout in the 11am session.  Please send slides for this as a simple PowerPoint file with no fancy template to {\\tt evans@virginia.edu} or get them to me on a USB stick before 10:30am (preferably earlier!).  Breakout leaders will present in order by breakout number, and the slides will be combined to avoid presentation transitions.')
    msg += generate_brow('10:30-11:00am','Regency Foyer','Break')
    msg += generate_row('11am-12:15pm', 'Regency EF', 'Results of Breakout Discussions')
    msg += generate_row('12:15-1:30pm', 'Independence Center', 'Lunch')
    msg += generate_row('1:30-2:45pm', 'Regency EF', 'Panel: \\ptitle{SaTC 2029?} (Carl Landwehr, Patrick McDaniel, Amit Sahai; David Evans)')
    msg += generate_row('2:45-3:00pm','Regency EF','Closing')
    msg += "} \n" # end dayschedule

    msg += "\\end{document}"
    return msg

def schedule(pi):
    rm = RapidMeeting.objects.filter(pi1=pi) | RapidMeeting.objects.filter(pi2=pi) | RapidMeeting.objects.filter(pi3=pi) | RapidMeeting.objects.filter(pi4=pi)

    rm = rm.order_by('round')
    # LogMessage("rapid meeting 1: " + ' / '.join([m.displayMeeting() for m in rm]))
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

    return latex_schedule(pi, rm, poster, breakout1, breakout2, breakout3, breakoutleader,
                          breakout1leader, breakout2leader, breakout3leader)

def generate_schedule(no, attendee):
    msg = schedule(attendee)
    fname = 'schedules/schedule-' + "%03d" % no + "-" + str(attendee.id) + '.tex'
    print "Writing schedule for " + attendee.displayName() + " to " + fname + "..."
    with open(fname, "w") as file:
        file.write(msg)

def generate_schedules():
    attendees = NSFInvestigator.objects.filter(attendee=True).order_by('lastname','firstname')
    count = 1
    for attendee in attendees:
        if not attendee.email:
            LogMessage("Bad pi: " + str(attendee.id))
            continue
        generate_schedule(count, attendee)
        count += 1
#        if count > 100: 
#            break # one for now


if __name__ == "__main__":
    generate_schedules()
