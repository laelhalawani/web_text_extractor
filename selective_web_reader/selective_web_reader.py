from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlparse
import bs4
import json
from pathlib import Path


DEFAULT_URL_CONFIG_FILE_PATH = "./url_configs.json"
"""
Configuration File Format for Content Extraction:

- `url_pattern`: A list of URL strings or patterns for matching web pages. 
  Each element should be a string that represents a part of a URL or an exact URL to match. 
  Use "_default_" to apply settings universally to URLs not matched by other patterns.
  Example: ["https://example.com/page", "_default_"].

- `include_selectors`: List of CSS selector strings that identify HTML elements whose content should be included.
  CSS selectors target elements based on attributes like id, class, and others, specifying precisely what to extract.
  Example: ["div.article-content", "main > p.intro"].

- `remove_selectors`: List of CSS selector strings for identifying HTML elements to be excluded from the extracted content.
  Useful for removing non-essential elements such as ads, scripts, and navigation bars from the extraction.
  Example: ["div.advertisement", "nav.navigation", "script"].

This configuration allows detailed specification of content to include and exclude based on the structure of targeted web pages.
"""

class SelectiveWebReader:
    """
    A class to load and process web content based on URL configurations.

    Attributes:
        url_configs_file (str): Path to the URL configurations file.
        url_configs (dict): Loaded URL configurations mapping URL patterns to include and remove selectors.
        html_string (str): Processed HTML content as a string.

    Methods:
        load_website(url: str): Loads and processes a website's HTML content based on URL configurations.
        get_html(): Returns the processed HTML content.
        download_image(image_url: str, save_as: str, save_dir: str, file_name: str, make_dir: bool): Downloads and saves an image from a given URL.
    """

    def __init__(self, url_configs_file:str = None) -> None:
        """
        Initializes WebReader with a URL configurations file.

        Args:
            url_configs_file (str, optional): Path to the URL configurations file. Defaults to DEFAULT_URL_CONFIG_FILE_PATH.
        
        A class to load and process web content based on URL configurations.

        Attributes:
            url_configs_file (str): Path to the URL configurations file.
            url_configs (dict): Loaded URL configurations mapping URL patterns to include and remove selectors.
            html_string (str): Processed HTML content as a string.

        Methods:
            load_website(url: str): Loads and processes a website's HTML content based on URL configurations.
            get_html(): Returns the processed HTML content.
            download_image(image_url: str, save_as: str, save_dir: str, file_name: str, make_dir: bool): Downloads and saves an image from a given URL.

        """
        self.url_configs_file = DEFAULT_URL_CONFIG_FILE_PATH if url_configs_file is None else url_configs_file
        self.url_configs = {}
        if Path(self.url_configs_file).exists() and Path(self.url_configs_file).is_file():
            self._load_url_configs_file(self.url_configs_file)
        else:
            error_msg = f"URL configurations file not found at {self.url_configs_file}, please ensure the file exists and is accessible or provide a path to a different file."
            raise FileNotFoundError(error_msg)
        self.html_string:str = ""

    @staticmethod
    def _create_config(url_parent:str, include_selectors:list, remove_selectors:list) -> dict:
        """
        Creates a URL configuration dictionary for a given URL pattern.

        Args:
            url_parent (str): The URL pattern to match.
            include_selectors (list): List of CSS selectors to include in the extraction.
            remove_selectors (list): List of CSS selectors to remove from the extraction.

        Returns:
            dict: A URL configuration dictionary containing the URL pattern, include selectors, and remove selectors.
        """
        return {
            "url_pattern" : [url_parent],
            "include_selectors" : include_selectors,
            "remove_selectors" : remove_selectors
        }
    
    def add_new_config(self, url_parent:str, include_selectors:list=["h1", "p"], remove_selectors:list=["button", "form", "style", "script", "iframe"], update_file:bool=True) -> None:
        """
        Adds a URL configuration to the url_configs dictionary and optionally updates the URL configurations file.

        Args:
            url_parent (str): The URL pattern to match.
            include_selectors (list): List of CSS selectors to include in the extraction.
            remove_selectors (list): List of CSS selectors to remove from the extraction.
            update_file (bool, optional): Whether to update the URL configurations file. Default is True.
        """
        config = self._create_config(url_parent, include_selectors, remove_selectors)
        self._add_config(config)
        if update_file:
            self._update_url_configs_file()

    def _update_url_configs_file(self) -> None:
        """
        Updates the URL configurations file with the current url_configs dictionary.
        """
        with open(self.url_configs_file, 'w') as f:
            json.dump(self.url_configs, f, indent=4)

    def _add_config(self, url_config:dict):
        """
        Adds a URL configuration to the url_configs dictionary.

        Args:
            url_config (dict): A single URL configuration containing URL patterns, include, and remove selectors.
        """
        url_patterns = url_config["url_pattern"]
        for url_pattern in url_patterns:
            if not url_pattern in self.url_configs.keys():
                self.url_configs[url_pattern] = {
                    "include_selectors" : url_config["include_selectors"],
                    "remove_selectors" : url_config["remove_selectors"]
                }
    
    def _load_url_configs_file(self, url_configs_file:str):
        """
        Loads URL configurations from a file and populates the url_configs attribute.

        Args:
            url_configs_file (str): Path to the URL configurations file.
        """
        with open(url_configs_file, 'r') as f:
            configs = json.load(f)
        for config in configs:
            self._add_config(config)
    
    def _get_selectors(self, url:str):
        """
        Retrieves include and remove selectors for a given URL.

        Args:
            url (str): The URL to match against the url_configs patterns.

        Returns:
            dict: A dictionary containing include and remove selectors if a match is found, None otherwise.
        """
        for url_pattern in self.url_configs.keys():
            if url_pattern in url:
                return self.url_configs[url_pattern]
            elif "_default_" in self.url_configs.keys():
                print(f"No match found for {url}, using default settings for now:\n{self.url_configs['_default_']}\nIt is recommended to add a configuration for this URL using add_new_config method.")
                return self.url_configs["_default_"]
    
    def _load_html(self, url:str) -> str:
        """
        Loads the HTML content from a given URL.

        Args:
            url (str): The URL from which to load HTML content.

        Returns:
            str: The loaded HTML content.
        """
        req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        html = urlopen(req).read().decode("utf8")
        self.html_string = html
        return html
    
    def _skim_relevant(self, html:str, selectors:dict) -> str:
        """
        Extracts relevant content from HTML based on include and remove selectors.

        Args:
            html (str): The HTML content to process.
            selectors (dict): A dictionary containing include and remove selectors.

        Returns:
            str: A string containing the extracted HTML elements.
        """
        include_selectors = selectors["include_selectors"]
        remove_selectors = selectors["remove_selectors"]
        soup = bs4.BeautifulSoup(html, 'html.parser')
        for selector in remove_selectors:
            for tag in soup.select(selector):
                tag.extract()
        selected_elements = [str(tag) for selector in include_selectors for tag in soup.select(selector)]
        return ''.join(selected_elements)
    
    def _make_links_absolute(self, html:str, url:str) -> str:
        """
        Converts relative links in the HTML to absolute links.

        Args:
            html (str): The HTML content to process.
            url (str): The base URL to resolve relative links against.

        Returns:
            str: The processed HTML with absolute links.
        """
        soup = bs4.BeautifulSoup(html, 'html.parser')
        for link in soup.find_all('a', href=True):
            link['href'] = urljoin(url, link['href'])
        return str(soup)

    def load_website(self, url:str) -> str:
        """
        Loads, processes, and stores the HTML content from a specified URL.

        Args:
            url (str): The URL of the website to load.

        Returns:
            str: The processedHTML content based on URL configurations.
        """
        html = self._load_html(url)
        html = self._make_links_absolute(html=html, url=url)
        selectors = self._get_selectors(url)
        if selectors:
            selected_elements = self._skim_relevant(html=html, selectors=selectors)
            html = "".join([str(element) for element in selected_elements])
        self.html_string = html
        return html

    def get_html(self) -> str:
        """
        Retrieves the processed HTML content.

        Returns:
            str: The processed HTML content as a string.
        """
        return self.html_string

    @staticmethod
    def download_image(image_url:str, save_as:str=None, save_dir:str = None, file_name:str=None, make_dir:bool = True) -> str:
        """
        Downloads an image from the specified URL and saves it to a local file.

        Args:
            image_url (str): The URL of the image to download.
            save_as (str, optional): The full path to save the image file. If provided, overrides save_dir and file_name.
            save_dir (str, optional): The directory to save the image file. Used if save_as is not provided.
            file_name (str, optional): The name of the image file. Derived from the URL if not provided.
            make_dir (bool, optional): Whether to create the save directory if it does not exist. Default is True.

        Returns:
            str: The path to the saved image file.

        Raises:
            RuntimeError: If the image download fails.
            HTTPError, URLError: For URL and HTTP errors.
        """
        url = urlparse(image_url).path
        save_path = ''
        if save_as is not None:
            save_path = save_as
        else:
            file_name = file_name if file_name is not None else Path(url).name
            if save_dir is not None:
                save_path = Path(save_dir) / file_name
            else:
                save_path = Path('.') / file_name
        if make_dir:
            save_path.parent.mkdir(parents=True, exist_ok=True)

        req = Request(image_url, headers={'User-Agent': 'Mozilla/5.0'})

        try:
            with urlopen(req) as response:
                if response.status == 200:
                    image_data = response.read()
                    with open(save_path, 'wb') as f:
                        f.write(image_data)
                    print(f"{url} saved to {save_path}")
                    return str(save_path)
                else:
                    raise RuntimeError(f"Image failed to download, returned code {response.status}")
        except HTTPError as e:
            print(f"HTTP Error encountered: {e.code} - {e.reason}")
        except URLError as e:
            print(f"URL Error encountered: {e.reason}")
        return ""

    def save_html(self, save_as:str) -> None:
        """
        Saves the processed HTML content to a file.

        Args:
            save_as (str): The full path to save the HTML content.
        """
        if self.html_string:
            with open(save_as, 'w') as f:
                f.write(self.html_string)
            print(f"HTML content saved to {save_as}")
        else:
            print("No HTML content to save, please load a website first.")
            raise RuntimeError("No HTML content to save, please load a website first.")