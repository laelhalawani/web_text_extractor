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

