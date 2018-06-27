import setuptools


setuptools.setup(name='powerplan',
                 version='0.0.1',
                 description='',
                 long_description='',
                 author='Russ Garrett',
                 author_email='russ@garrett.co.uk',
                 packages=['powerplan', 'powerplan.command'],
                 install_requires=['networkx==2.1', 'pydotplus', 'click', 'pint'],
                 python_requires=">=3.4",
                 license='MIT License',
                 entry_points={
                    'console_scripts': {
                        'powerplan=powerplan.command.powerplan:run'
                    }
                 },
                 zip_safe=False)
