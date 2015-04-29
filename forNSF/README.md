This directory is for files that were used for managing the site for the NSF SatC conference but aren't necessary to
get the application working at a basic level. If you wish to make use of some of the files, be aware that in their current state
some may not work from this directory, and would have to be moved into the rematchr directory in order to work.

File Descriptions
=============
- breakouts.py: Contains a python list of information about breakout groups.
- collaborators.py:  A module that created a csv file to show the PI's and their collaborators. This was used in the matching phase
of the overall project, during which we wanted to avoid matching two PI's who had worked together already.
- fixnew.py: A script written to update the database with some new information. Not a general use program.
- generate_schedules.py: Used to create the meeting schedules for each attendee.
- load_breakouts.py: Loaded the information about breakouts into the database.
- load_matches.py: Takes a groups.csv file created by the matching process and loads that information into the database.
- login.sh: A shell script that was used for logging into the server.
- parsecsv.py: A script that was used to create an "emails2texts.pickle" file that was used in the modeling process. It takes a csv
file with information about attendees and uses the aggregated investigators and projects models to create a mapping (literally
a python dictionary) from each attendees email to pure text versions of their project abstracts.
- rating.py: A django form for PI's to rate their meetings.
- soupextract.py: Scraped pdfs from websites when our plan was to use attendees entire publications as the text information for modeling
instead of the NSF project abstracts.
- stopwords: words to exclude from counting/wordclouds/text analysis.
- testemails.py: Part of the process for the NSF conference was an email blast; this tested the provided addresses.
- updateattendees.py: Like fixnew.py, another script to update the database with some new information. Not a general use program.
- utils.py: A copy of utils.py from the rematchr directory.
- wordcounts.py: Processed text and counted words. Once used for wordclouds or other graphics.
