""" setup """
from os import path
from setuptools import find_packages, setup
from wagtailsnapshotpublisher import __VERSION__

THIS_DIRECTORY = path.abspath(path.dirname(__file__))
with open(path.join(THIS_DIRECTORY, 'README.md'), encoding='utf-8') as f:
    LONG_DESCRIPTION = f.read()

# install_dependencies = [
#     'jsonschema == 3.0.1',
# ]

setup(
    name='wagtail-snapshotpublisher',
    version=__VERSION__,
    packages=find_packages(),
    include_package_data=True,
    # install_requires=install_dependencies,
    license='MIT',
    url='https://github.com/nhsuk/wagtail-snapshotpublisher',
    description='Add Release mechanism from django-snapshotpublisher to wagtail',
    long_description=LONG_DESCRIPTION,
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
