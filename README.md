#SVEN
sven is a django app (1.6) which easily integrate text analysis with pattern with a powerful corpus management.

installing sven
---
git clone, activate submodules, activate a virtualenv, mkvirtualenv
copy localsettingssample and modify it according to your own configuration

Run in your terminal:

  cd path/to/sven
  workon sven
  python manage.py collectstatic
  python manage.py syncdb
  python manage.py test

If everything is ok you can start deploying the django server (for test purposes only!)

  python manage.py runserver

Normally a development version of sven should be running under 
[localhost:8000]
  

troubleshooting
---
__(OSX)__ how to compile local .po file for localization 

	brew update
	brew install gettext
	brew link getttext --force

	django-admin.py makemessages --locale=fr


where 

add the following folder from font-awesome if settings.OFFLINE is enabled.

fonts
	
css

requirements
---

Django==1.6.2
Pattern==2.6
wsgiref==0.1.2



git submodule init
git submodule update