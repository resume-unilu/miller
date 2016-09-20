# Installation
Those below are the installation instruction for running Miller on ubuntu 16.04 server.

## Check dependencies

	sudo apt update
	sudo apt upgrade

	sudo locale-gen en_US en_US.UTF-8
	sudo dpkg-reconfigure locales 

Check /etc/environments then set
	
	LC_ALL=en_US.UTF-8
	LANG=en_US.UTF-8

Once `locale` is well set, we can install `virtualenv` and `virtualenvwrapper`

	sudo apt install python-pip

	pip install virtualenv --user
	pip install virtualenvwrapper --user

Add optionally `virtualenvwrapper.sh` to your bash file, or simply:

	source /home/your-user/.local/bin/virtualenvwrapper.sh

### mysql installation
Feel free to skip this session if you decided to use another database or mysl has been set in your system.

	sudo apt install mysql-server mysql-client
	sudo mysql_secure_installation
	
Then set the correct config for your system.
If there is no libmysql installed, we should
	
	sudo apt-get install libmysqlclient-dev
	
## Clone and setup Miller!
clone (current user home folder, so that our project home dir will be `~/miller`)
	
	cd
	git clone https://github.com/CVCEeu-dh/miller.git miller
	cd ~/miller
	mkvirtualenv miller
	pip install -r requirements.txt
	
	# only if you decided so.
	pip install MySQL-python

For mysql, create an user and create a database where he/she has all privileges granted:

	mysql -u root -p
	
	mysql> CREATE DATABASE miller;	
	mysql> CREATE USER 'miller'@'localhost' IDENTIFIED BY 'password';
	mysql> GRANT ALL PRIVILEGES ON resume . * TO 'resume'@'localhost';
	FLUSH PRIVILEGES
	
Back to project home folder, copy `miller/local_settings.py.example` file to `miller/local_settings.py` and fill the installation specific configuration params. The variables set in the `local_settings` file will override those present in `settings.py`. ! Remember to change  the `SECRET_KEY` (e.g. try a django-secret-key-generator service) and the info about the database to be used).

Finally, launch some django commands:
	
	cd ~/miller
	python manage.py migrate
	python manage.py createsuperuser

We should also initialize versioning and search engine - Miller makes use of WHOOSH:

	python manage.py init_whoosh
	python manage.py init_git

Initialize with default tags:
	
	python manage.py loaddata miller.tag.json

Test if everything is working properly:
	
	python manage.py runserver 0.0.0.0:8000
	
	
## Setup a production environment (uWSGI + nginx)
This setup mostly follows [uwsgi documentation for Django and nginx](http://uwsgi-docs.readthedocs.io/en/latest/tutorials/Django_and_nginx.html).
Create and chown the dir where log files and static files will be stored. We're going to use `/var/www` for simplicity sake
	
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
	sudo /etc/init.d/nginx restart
	
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
	
	
## setup git to expose versioned content
Follow the doc https://git-scm.com/book/en/v2/Git-on-the-Server-Setting-Up-the-Server

	$ sudo adduser git
	$ su git
	$ cd
	$ mkdir .ssh && chmod 700 .ssh
	$ touch .ssh/authorized_keys && chmod 600 .ssh/authorized_keys
	
And create a bare repository as suggested, e.g inside `/opt/git/my-miller-contents.git`

Go to 
	
	cd 
Remember to add 
	
	eval "$(ssh-agent -s)"
	ssh-add ~/.ssh/id_rsa_custom

	
