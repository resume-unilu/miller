
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
	
	
clone

	git clone https://github.com/CVCEeu-dh/miller.git resume
	cd resume
	pip install -r requirements.txt
	
	pip install MySQL-python

Change mysql params

	mysql -u root -p
	
	mysql> CREATE DATABASE 'resume'	
	mysql> CREATE USER 'resume'@'localhost' IDENTIFIED BY 'password';
	mysql> GRANT ALL PRIVILEGES ON resume . * TO 'resume'@'localhost';
	FLUSH PRIVILEGES
	
Then back to resume folder
	
	python manage.py migrate
	python manage.py createsuperuser

Initialize versioning and search engine:

	python manage.py init_whoosh
	python manage.py init_git

Test if everything is working properly
	
	python manage.py runserver 0.0.0.0:8000