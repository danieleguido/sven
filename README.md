#SVEN
sven is a django app which easily integrate text analysis with pattern with a powerful corpus management.

installing sven
---
Welcome to our three minutes install! All you need is a terminal, virtualenv, virtualenvwrapper and a good knowledge of a Django structure. That's it. For development purpose, node and grunt-cli should be installed - cfr _troubleshooting_ part below. 
	
	cd ~/path/to
	git clone https://gitub.com/danieleguido/sven.git
	cd ~/path/to/sven
	cp sven/locale_settings.sample.py sven/locale_settings.py
	
modify it according to your __own__ configutation.
if you're going to use a _sqlite_ database (a light and fast alternative), you need to create a specific directory to hold the sqlite file. Then give adequate permissions access to both sqlite file and its parent directory.

	cd ~/path/to/sven
	mkvirtualenv sven
		...
	workon sven
		...
	(sven) python manage.py syncdb
	(sven) python manage.py test

sven in production: some hints
---

todo

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


Structure
---

`./src` contains all the js and stylesheet used by Sven.
