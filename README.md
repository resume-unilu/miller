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
	