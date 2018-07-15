import setuptools


setuptools.setup(name='powerplan',
                 version='0.0.1',
                 description='A library for computer-aided design of temporary power systems.',
                 long_description='A library for computer-aided design of temporary power systems.',
                 author='Russ Garrett',
                 author_email='russ@garrett.co.uk',
                 packages=['powerplan'],
                 install_requires=[
                     'networkx==2.1',
                     'pydotplus==2.0.2',
                     'pint==0.8.1',
                     'pyYAML',
                     'jinja2==2.10'
                 ],
                 python_requires=">=3.4",
                 license='GPL v3',
                 zip_safe=False)
