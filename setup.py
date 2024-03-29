import setuptools

setuptools.setup(
    name="powerplan",
    version="0.0.1",
    description="A library for computer-aided design of temporary power systems.",
    long_description="A library for computer-aided design of temporary power systems.",
    author="Russ Garrett",
    author_email="russ@garrett.co.uk",
    packages=["powerplan"],
    package_data={"powerplan": ["templates/*"]},
    install_requires=["networkx>=2.6", "pydotplus>=2.0.2", "pint==0.19.2", "pyYAML", "jinja2>=3.0.0"],
    python_requires=">=3.6",
    license="GPL v3",
    zip_safe=False,
)
