from setuptools import setup, find_packages

with open("./README.md", "r") as fh:
    long_description = fh.read()
setup(
    name="selective_web_reader",
    version="0.0.1",
    packages=find_packages(),
    install_requires=[
        'beautifulsoup4>=4.12.2',
    ],
    package_data={'selective_web_reader': ['config/*.json']},
    #include_package_data=True,
    author="Łael Al-Halawani",
    author_email="laelhalawani@gmail.com",
    description="SelectiveWebReader is a Python utility designed to streamline the process of fetching, processing, and extracting content from web pages based on specific URL patterns and CSS selectors.",
    classifiers=[
        "Intended Audience :: Developers",
        "Intended Audience :: Education",
        "Intended Audience :: Information Technology",
        "License :: Free for commercial use",
        "Natural Language :: English",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
    ],
    long_description=long_description,
    long_description_content_type='text/markdown',
    keywords=['scraping', 'web', 'html', 'css', 'beautifulsoup', 'requests', 'webreader', 'web_reader'],
    url="https://github.com/laelhalawani/web_reader",
)