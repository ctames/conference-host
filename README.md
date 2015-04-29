Navigation
==========
  - webApp: The django application directory. Has settings, models, views, etc.
  - forNSF: Some extra files that were used for the NSF SatC conference that weren't key to the functionality of the django app. Some files in here may not work properly if used/ran from this directory; they might have to be moved into rematchr main. They're placed in forNSF merely for organization and cleanliness.
  - logs: A directory for logging necessary for the app to work
  - dbdata: Some example files containing test data for the database. 
  
File Descriptions
==========
  - loadnsf.py: Loads instances of the webApp's models into the database from pickle files. 
  - loadall.sh: A shell script to run loadnsf for project, institution, and PI pickle files.
  - nsfmodels.py: A module of class definitions for NSF data that mirror some of webApp's model definitions. These object models are mainly used in loadnsf. 
  - utils.py: A module of various utility functions, for things like logging and such. One method in this file, key_from_email, is unusable "as is", as it requires a local "secret" module.
  - manage.py: The django application management script. 

Project Requirements
==========
  - django
  - django-browserid
  - django-extras

Setup
==========
  Getting the application set up locally is fairly easy, especially if you're familiar with django and using manage.py to work with the project. After you've made sure that you've satisfied the requirements, check to make sure that the application is working at the minimal level (css loads properly, urls working, etc.) by running "python manage.py runserver" and visiting localhost in your browser. If everything is looking nice and styled and links are working, then it's time to load the example database. Run "bash loadall.sh", which will run loadnsf.py for files in dbdata/pickle/ (this path is hardcoded in loadall.sh). loadnsf.py makes database transactions for the objects stored in these files, giving you some data to check out on the site. Revisit the site index and try out the links for projects, insitutions, and PI's. There should be a nonzero number of links to various instances of each model, and clicking on the link should bring you to a page of information about that item. If there's been no problems thus far, then the basic facilities of the site should be working fine. Delve into the webApp directory and check out the models, views, and urls to learn more about how to create your own data and use the application to your own liking.
  
