


### install nginx (macos)
brew install nginx
nginx
/usr/local/etc/nginx/nginx.conf
nginx -s stop

UWSGI
https://docs.djangoproject.com/en/1.9/howto/deployment/wsgi/
https://docs.djangoproject.com/en/1.9/howto/deployment/wsgi/uwsgi/
http://uwsgi-docs.readthedocs.org/en/latest/tutorials/Django_and_nginx.html

test: cd sven uwsgi --http :8000 --wsgi-file uwsgi_test.py

uwsgi --http :8000 --module sven.wsgi

then modify uswgi

uwsgi --ini mysite_uwsgi.ini