try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

config = {
        'descriptiom': 'My Project',
	'author': 'Rahul Krishna',
	'url': 'Project page',
	'download_url': 'Download URL',
	'author_email': 'i.m.ralk@gmail.com',
	'version':'0.1',
	'install_requires': ['nose'],
	'packages': ['NAME'],
	'scripts': [],
	'name': 'Project Name'
}

setup(**config)
	
