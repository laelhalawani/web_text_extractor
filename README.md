 # SelectiveWebReader

SelectiveWebReader is a Python utility designed to streamline the process of fetching, processing, and extracting content from web pages based on specific URL patterns and CSS selectors. It allows users to define which parts of a webpage to include or exclude, making it ideal for web scraping, data mining, and content extraction tasks.

## Features

- **URL Pattern Matching**: Customize content extraction based on URL patterns.
- **Content Selection**: Use CSS selectors to specify which parts of a webpage to extract.
- **Content Exclusion**: Define elements to be removed from the extraction.
- **Image Download**: Utility function to download and save images from the web.
- **HTML Content Processing**: Processes HTML content to make links absolute, and extracts relevant content based on configurations.
- **Easy adding new configurations**: Add new configurations using the add_new_config method, provide url and css selectors to include and exclude

## Installation

clone the repo, navigate to the directory and run the following command:

```bash
pip install .
```

## Usage

Import the SelectiveWebReader class from the package:
```python
from selective_web_reader import SelectiveWebReader
```

Create a new instance of the SelectiveWebReader class:
```python
swr = SelectiveWebReader()
```

Optionally, add new configurations using the `add_new_config` method, you can make it persistent by setting `update_file` argument to True, the default is False. The configurations are saved in a json file called `configurations.json` in the current directory.
```python
swr.add_new_config(url_pattern='example.com/', include_selectors=['p', 'h1', '.content'], exclude_selectors=['.sidebar', 'script', 'button', '#footer'])
```

Load a URL and extract content based on the configurations, if no configuration is found it will use the default and 
create or update an `unconfigured_urls.txt` in your project directory for future reference.
```python
swr.load_url('https://example.com')
```

Optionally get the extracted content as a string:
```python
html_content = swr.get_html()
```

Optionally save the extracted content to a file:
```python
swr.save_html('output.html')
```

## How it works

The SelectiveWebReader class is the main interface for the utility. It allows users to define configurations for URL patterns and CSS selectors, and provides methods for fetching and processing web content.
When a URL is passed the selectors are located and first the include selectors are extracted and then the exclude selectors are removed from the extracted content.
You can get the output as a html string with `get_html()` method or save it to a file with `save_html()` method.