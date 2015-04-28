#SVEN
sven is a django app (1.6) which easily integrate text analysis with pattern with a powerful corpus management.

installing sven
---
Welcome to our (twenty)three minutes install! All you need is a terminal, virtualenv, virtualenvwrapper and a good knowledge of a Django structure. That's it. For development purpose, node and grunt-cli should be installed - cfr _troubleshooting_ part below. 
	
	cd ~/path/to
	git clone https://gitub.com/danieleguido/sven.git
	cd ~/path/to/sven
	cp sven/local_settings.sample.py sven/local_settings.py
	
modify it according to your __own__ configutation: provide your python interpreter absolute path for the **sven virtualenv**. This interpreter will be used by sven custom management command.
  
  	PYTHON_INTERPRETER = '/Users/daniele/.virtualenvs/sven/bin/python'

if you're going to use a _sqlite_ database (a light and fast alternative), you need to create a specific directory to hold the sqlite file. Then give adequate permissions access to both sqlite file and its parent directory.

	cd ~/path/to/sven
	mkvirtualenv sven
		...
	workon sven
		...

install all dependencies

	(sven) pip install -r requirements.txt

install submodules

  	(sven) git submodule init
  	(sven) git submodule update

Create missing folders and check folder permission (Ubuntu/OSx)
	
	cd ~/path/to/sven
	sudo mkdir media logs
	sudo chown -R lime:www-data media
	sudo chmod -R g+ws media
	sudo chown -R lime:www-data logs
	sudo chmod -R g+ws logs
	
then sync and test.

	(sven) python manage.py syncdb
	(sven) python manage.py test

install the javascript client dependencies:

  	(sven) npm install -g bower
  	(sven) npm install -g grunt-cli
  	(sven) cd ~/path/to/sven
  	(sven) cd client
  	(sven) npm install
  	(sven) bower install

If everything is ok you can start deploying the django server (for test purposes only!)

  python manage.py runserver

Normally a development version of sven would now be running under 
[localhost:8000](localhost:8000)

Installation issues on UBUNTU
---
Please check that python-lxml is installed.

	sudo apt-get install libxml2-dev libxslt1-dev python-dev
	sudo apt-get install python-lxml

Installation issues MacOs with MySQL
---
  
  brew install mysql
  export PATH=$PATH:/usr/local/mysql/bin
  workon sven
  (sven) pip install MySQL-Python

<!-- sven in production: some hints
---
-->
Production environment
=======
Note: sven hasn't been tested on a production environment.

  cd path/to/sven
  workon sven
  python manage.py collectstatic



Note on sven structure
---

`./client` contains all the js and stylesheet used by Sven and it is the result of scaffolding with yo angular-generator.
`./sven/management/commands/start_job.py` is the *unique* python script file responsible for the text analysis. All the other commands are testing playgrounds['%Y-%m-%d %H:%M:%S',    # '2006-10-25 14:30:59'
'%Y-%m-%d %H:%M',        # '2006-10-25 14:30'
'%Y-%m-%d',              # '2006-10-25'
'%m/%d/%Y %H:%M:%S',     # '10/25/2006 14:30:59'
'%m/%d/%Y %H:%M',        # '10/25/2006 14:30'
'%m/%d/%Y',              # '10/25/2006'
'%m/%d/%y %H:%M:%S',     # '10/25/06 14:30:59'
'%m/%d/%y %H:%M',        # '10/25/06 14:30'
'%m/%d/%y'] 
