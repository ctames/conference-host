Overview
==========
  This project was originally created as a way to host information about the NSF SatC Conference in DC during January '15. It is a Django web application that provides a nice interface to a database containing a wealth of information on the conference attendees, their associated NSF projects and awards, their respective institutions, and the collaborations between them.

Navigation
==========
  - **webApp**: The django application directory; the bulk of the project's work is here. Has the settings, models, views, etc. The code that's in here is the real infrastructure of the application. 
  - **forNSF**: Some extra files that were used for the NSF SatC conference that aren't key to the basic functionality of the django app. Some files in here may not work properly if used/ran from this directory; they might have to be moved into rematchr main. They're placed in forNSF merely for organization and cleanliness.
  - **logs**: A directory for logging. This directory must exist for the app to work with the current settings.
  - **dbdata**: A small selection of the SatC conference database as an example. Contains pickle files of the django model objects that make up the db.
  
File Descriptions
==========
  - **loadnsf.py**: Loads instances of the webApp's models (what's in dbdata) into the database from pickle files. 
  - **loadall.sh**: A shell script to run loadnsf for project, institution, and PI pickle files.
  - **nsfmodels.py**: A module of class definitions for NSF data that mirror some of webApp's model definitions. These object models are mainly used for loadnsf. 
  - **utils.py**: A module of various utility functions, for things like logging and such. One method in this file, key_from_email, is unusable "as is", as it requires a local "secret" module.
  - **manage.py**: The django application management script. 

Project Requirements
==========
  - django
  - django-browserid
  - django-extras

Setup
==========
  Getting the application set up locally is fairly easy, especially if you're familiar with django and using manage.py to work with the project. Just follow these steps.
  - Clone the repo and navigate to it.
  - Make sure you've installed the required libraries (browserid and extras should be available via pip).
  - Run "python manage.py syncbd". This creates the database tables.
  - Run "python manage.py runserver". This starts the local development server.
  - Open your browser and go to localhost:8000 to check out the site.
  - Run "bash loadall.sh". This will load the data in the pickle files in dbdata/pickle/ into the database. Patience is a virtue here; this can take a little bit.
  - Go back to your browser. After a refresh or restart of the server, you should see that the "Projects", "Investigators", and "Institutions" pages are now nicely populated with a bunch of links to the various project investigators and their work. 
  - All done!
  
