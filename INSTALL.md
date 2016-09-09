
	sudo apt update
	sudo apt upgrade

	sudo locale-gen en_US en_US.UTF-8
	sudo dpkg-reconfigure locales 

Check /etc/environments then set
	
	LC_ALL=en_US.UTF-8
	LANG=en_US.UTF-8

	sudo apt install python-pip

	pip install virtualenv --user
	pip install virtualenvwrapper --user

Add 
source /home/your-user/.local/bin/virtualenvwrapper.sh

	
	sudo apt install mysql-server mysql-client
	sudo mysql_secure_installation
	
VALIDATE PASSWORD PLUGIN 2=Strong then disable everything.
	
	sudo apt-get install libmysqlclient-dev
	
	
clone (current user home folder, so that our project home dir will be `~/miller`)
	
	cd
	git clone https://github.com/CVCEeu-dh/miller.git miller
	cd ~/miller
	mkvirtualenv miller
	pip install -r requirements.txt
	
	pip install MySQL-python

For mysql, create an user and its own database with all privileges granted:

	mysql -u root -p
	
	mysql> CREATE DATABASE 'miller'	
	mysql> CREATE USER 'miller'@'localhost' IDENTIFIED BY 'password';
	mysql> GRANT ALL PRIVILEGES ON resume . * TO 'resume'@'localhost';
	FLUSH PRIVILEGES
	
Then back to project home folder and launch
	
	cd ~/miller
	python manage.py migrate
	python manage.py createsuperuser

Initialize versioning and search engine:

	python manage.py init_whoosh
	python manage.py init_git

Initialize with default tags
	
	python manage.py loaddata miller.tag.json

Test if everything is working properly
	
	python manage.py runserver 0.0.0.0:8000
	
	
## Production environment (uWSGI + nginx)
This setup mostly follows [uwsgi documentation for Django and nginx](http://uwsgi-docs.readthedocs.io/en/latest/tutorials/Django_and_nginx.html).
Create and chown the dir where log files and static file will be stored. We're going to use /var/www for simplicity sake
	
	mkdir /var/www/miller
	sudo chown youruser:staff -R /var/www/miller 

Check your STATIC_ROOT in your miller/local_settings.py file, then run the collectstatic command:
	
	python manage.py collectstatic

Install (and start) nginx
	
	sudo apt-get install nginx
	sudo /etc/init.d/nginx start
	
Test that the server is running. Copy then rename the `miller.nginx.conf.example` file to `miller.nginx.conf`.
Edit according to your paths and system organisation, then symlink to /etc/nginx/sites-enabled so nginx can see it:

	sudo ln -s ~/miller/miller.nginx.conf /etc/nginx/sites-enabled/

Do almost the same for `miller.uwsgi.ini.example` to `miller.uwsgi.ini` and change vars according to your needs.

Start uwsgi (with virtualenv activated) and check that everything works smoothly:
	
	uwsgi --ini miller.uwsgi.ini 
	
Then you can deactivate the virtualenv and install uwsgi system-wide, with vassals and everything with sudo:

	deactivate
	sudo pip install uwsgi
	sudo mkdir /etc/uwsgi
	sudo mkdir /etc/uwsgi/vassals

	# Create a symlink for the `~/miller/miller.uwsgi.ini` file:

	sudo ln -s ~/miller/miller.uwsgi.ini /etc/uwsgi/vassals/
	
	# run the emperor
	uwsgi --emperor /etc/uwsgi/vassals
	
If and only if there are no errors, daemonize the emperor:

	sudo uwsgi --emperor /etc/uwsgi/vassals --daemonize /var/log/uwsgi-emperor.log
	
	

	
