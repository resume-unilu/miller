### Miller

collaborative writing platform, git powered.

## installation
Miller is a Python Django application. The file requirements.txt contains the list of the project dependencies, so once virtualenv and virtualenvwrapper are available the installation is as simple as:
	
	$ cd miller
	...
	$ mkvirtualenv miller
	$ pip install -r requirements.txt
	
According to your desired working environment, you may want to use mysql as database to store Miller metadata and users' information.

	$ pip install MySQL-python
	
Otherwise, sqlite lib should be included with Python.
Install db 

	$ python manage.py migrate 
	

## addons: print pdf
On RedHat 7.0:

	sudo yum install -y xorg-x11-fonts-75dpi
	sudo yum install -y xorg-x11-fonts-Type1

Download rpm, e.g.
	wget https://bitbucket.org/wkhtmltopdf/wkhtmltopdf/downloads/wkhtmltox-0.13.0-alpha-7b36694_linux-centos7-amd64.rpm


## enable docx import
Import footnotes and table of contents with pandoc (pandoc should be installed)
Import [Core properties](http://python-docx.readthedocs.io/en/latest/dev/analysis/features/coreprops.html)