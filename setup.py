from setuptools import setup, find_packages
setup(
    name="selective_web_reader",
    version="0.0.2",
    packages=find_packages(),
    install_requires=[
        'beautifulsoup4>=4.12.2',
    ],
    package_data={'selective_web_reader': ['./selective_web_reader/url_config*.json']},
    #include_package_data=True, #use only with manifest not with package_data here
    author_email="Łael Al-Halawani <laelhalawani@gmail.com>",
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
    keywords=['scraping', 'web', 'html', 'css', 'beautifulsoup', 'requests', 'webreader', 'web_reader'],
    url="https://github.com/laelhalawani/web_reader",
)