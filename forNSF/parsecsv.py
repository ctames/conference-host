import pickle
import csv
import nsfmodels
import sys

csvfile = sys.argv[1]
investigators = []
projects = []

with open("investigators.pickle") as file:
	investigators = pickle.load(file)
	
with open("projects.pickle") as file:
	projects = pickle.load(file)

emails_grants = []
with open(csvfile, 'rU') as file:
	filereader = csv.reader(file, dialect=csv.excel_tab)
	for row in filereader:
		if len(row) > 0:
			if len(row[0].split(',')) > 9:
				print row[0].split(',')
				print ""
				emails_grants.append((row[0].split(',')[5], row[0].split(',')[8]))

people = {}	
for pair in emails_grants:
	email  = pair[0]
	people[email] = []
	for investigator_obj in investigators:
		pi = investigator_obj.lookupPI(email)
		if pi is not None:
			people[email] += pi.projects
	grants = pair[1]
	awards = grants.split()
	for award in awards:
		if award not in people[email]:
			people[email].append(award)

			
people_texts = {}
totalawards = 0
numberfound = 0
emptyemails = []
for email in people.keys():
	if '@' not in email:
		people.pop(email)
	else:
		print email
		print people[email]
		
		people_texts[email] = []
		for id in people[email]:
			totalawards += 1
			for project in projects:
				if id.strip('\"') == project.awardID:
					people_texts[email].append(project.abstract)
					numberfound += 1
					break
		if len(people_texts[email]) == 0:
			print email + "'s texts are empty"
			emptyemails.append(email)
		print ""
						
print "total awards: " + str(totalawards)
print "number found: " + str(numberfound)
print "empty lists : " + str(len(emptyemails))
for person in emptyemails:
	print email
	
with open("../modeling/emails2texts.pickle", "wb") as file:
	pickle.dump(people_texts, file)
