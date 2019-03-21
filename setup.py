from os import path
from setuptools import find_packages, setup
from wagtailsnapshotpublisher import __VERSION__

this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='wagtail-snapshotpublisher',
    version=__VERSION__,
    packages=find_packages(),
    include_package_data=True,
    license='MIT',
    url='https://github.com/yohanlebret/wagtail-snapshotpublisher',
    description='Add Release mechanism from django-snapshotpublisher to wagtail',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='Yohan Lebret',
    author_email='yohan.lebret@gmail.com',
    classifiers=[
        'Environment :: Web Environment',
        'Framework :: Django',
        'Framework :: Django :: 2.1',
        'Framework :: Wagtail',
        'Framework :: Wagtail :: 2',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
    ],
)