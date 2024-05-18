from typing import Optional
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlparse
from http.client import IncompleteRead
import bs4
import json
import time
from pathlib import Path
import logging as log
from .swr_config import DEFAULT_URL_CONFIG_FILE_PATH
from .swr_config import UNCONFIGURED_URLS_OUTPUT_FILE
from .swr_config import ERRORED_URLS_OUTPUT_FILE


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

    def __init__(self, url_configs_file:str = None, unconfigured_urls_notification_file:str=None, errored_urls_notification_file:str=None) -> None:
        """
        Initializes WebReader with a URL configurations file.

        Args:
            url_configs_file (str, optional): Path to the URL configurations file. Defaults to DEFAULT_URL_CONFIG_FILE_PATH.
            unconfigured_urls_notification_file (str, optional): Path to the file to write unconfigured URLs to. Defaults to UNCONFIGURED_URLS_OUTPUT_FILE.
        
        A class to load and process web content based on URL configurations.

        Attributes:
            url_configs_file (str): Path to the URL configurations file.
            unconfigured_urls_output_file (str): Path to the file to write unconfigured URLs to.
            url_configs (dict): Loaded URL configurations mapping URL patterns to include and remove selectors.
            html_string (str): Processed HTML content as a string.

        Methods:
            load_website(url: str): Loads and processes a website's HTML content based on URL configurations.
            get_html(): Returns the processed HTML content.
            download_image(image_url: str, save_as: str, save_dir: str, file_name: str, make_dir: bool): Downloads and saves an image from a given URL.



        """
        self.url_configs_file = DEFAULT_URL_CONFIG_FILE_PATH if url_configs_file is None else url_configs_file
        self.unconfigured_urls_output_file = UNCONFIGURED_URLS_OUTPUT_FILE if unconfigured_urls_notification_file is None else unconfigured_urls_notification_file
        self.errored_urls_output_file = ERRORED_URLS_OUTPUT_FILE if errored_urls_notification_file is None else errored_urls_notification_file
        self.url_configs = {}
        if Path(self.url_configs_file).exists() and Path(self.url_configs_file).is_file():
            self._load_url_configs_file(self.url_configs_file)
        else:
            error_msg = f"URL configurations file not found at {self.url_configs_file}, please ensure the file exists and is accessible or provide a path to a different file."
            raise FileNotFoundError(error_msg)
        self.html_string:str = None
        self.url:str = None

    @staticmethod
    def _create_config(url_pattern:str, include_selectors:list, remove_selectors:list) -> dict:
        """
        Creates a URL configuration dictionary for a given URL pattern.

        Args:
            url_pattern (str): The URL pattern to match.
            include_selectors (list): List of CSS selectors to include in the extraction.
            remove_selectors (list): List of CSS selectors to remove from the extraction.

        Returns:
            dict: A URL configuration dictionary containing the URL pattern, include selectors, and remove selectors.
        """
        return {
            "url_pattern" : [url_pattern],
            "include_selectors" : include_selectors,
            "remove_selectors" : remove_selectors
        }
    
    def switch_to_local(self, configs_dir:str, overwrite:bool = False) -> None:
        """
        Switches to use local configuration and output files instead of the package's global files, useful for separate configurations for different projects.
        If the file doesn't exists, creates it and saves the current configurations, unconfigured URLs, and errored URLs to the new files.
        If the files exit it can overwrite them with the overwrite set to True.
        Finally it sets the new files to be used by the class.

        Args:
            configs_dir (str): The directory to save the new configuration files.
            save_as (str): The path to save the URL configurations file.
            overwrite (bool, optional): Whether to overwrite the file if it already exists. Default is False.
        """
        if not Path(configs_dir).exists():
            Path(configs_dir).mkdir(parents=True, exist_ok=True)
        new_url_configs_file = Path(configs_dir) / Path(self.url_configs_file).name
        new_unconfigured_urls_output_file = Path(configs_dir) / Path(self.unconfigured_urls_output_file).name
        new_errored_urls_output_file = Path(configs_dir) / Path(self.errored_urls_output_file).name
        if not new_url_configs_file.exists() or overwrite:
            if Path(self.url_configs_file).exists():
                url_configs = []
                with open(self.url_configs_file, 'r', encoding='utf-8') as f:
                    url_configs = json.load(f)
                with open(new_url_configs_file, 'w', encoding='utf-8') as f:
                    json.dump(url_configs, f, indent=4)
            else:
                with open(new_url_configs_file, 'w', encoding='utf-8') as f:
                    json.dump([], f, indent=4)
        if not new_unconfigured_urls_output_file.exists() or overwrite:
            if Path(self.unconfigured_urls_output_file).exists():
                unconfigured_urls = []
                with open(self.unconfigured_urls_output_file, 'r', encoding='utf-8') as f:
                    unconfigured_urls = json.load(f)
                with open(new_unconfigured_urls_output_file, 'w', encoding='utf-8') as f:
                    json.dump(unconfigured_urls, f, indent=4)
            else:
                with open(new_unconfigured_urls_output_file, 'w', encoding='utf-8') as f:
                    json.dump([], f, indent=4)
        if not new_errored_urls_output_file.exists() or overwrite:
            if Path(self.errored_urls_output_file).exists():
                errored_urls = []
                with open(self.errored_urls_output_file, 'r', encoding='utf-8') as f:
                    errored_urls = json.load(f)
                with open(new_errored_urls_output_file, 'w', encoding='utf-8') as f:
                    json.dump(errored_urls, f, indent=4)
            else:
                with open(new_errored_urls_output_file, 'w', encoding='utf-8') as f:
                    json.dump([], f, indent=4)
        self.url_configs_file = new_url_configs_file.as_posix()
        self.url_configs = {}
        self._load_url_configs_file(self.url_configs_file)
        self.unconfigured_urls_output_file = new_unconfigured_urls_output_file.as_posix()
        self.errored_urls_output_file = new_errored_urls_output_file.as_posix()
        log.info(f"Switched to local configuration files: {self.url_configs_file}, {self.unconfigured_urls_output_file}, {self.errored_urls_output_file}")
    

    def add_new_config(self, url_pattern:str, include_selectors:list=["h1", "p"], remove_selectors:list=["button", "form", "style", "script", "iframe"], update_file:bool=True) -> None:
        """
        Adds a URL configuration to the url_configs dictionary and optionally updates the URL configurations file.

        Args:
            url_pattern (str): The URL pattern to match.
            include_selectors (list): List of CSS selectors to include in the extraction.
            remove_selectors (list): List of CSS selectors to remove from the extraction.
            update_file (bool, optional): Whether to update the URL configurations file. Default is True.
        """
        config = self._create_config(url_pattern, include_selectors, remove_selectors)
        self._add_new_config(config, update_entry=False)
        if update_file:
            self._update_url_configs_file()
    
    def modify_or_add_config(self, url_pattern:str, include_selectors:list=["h1", "p"], remove_selectors:list=["button", "form", "style", "script", "iframe"], update_file:bool=True) -> None:
        """
        Adds a URL configuration to the url_configs dictionary and optionally updates the URL configurations file.

        Args:
            url_pattern (str): The URL pattern to match.
            include_selectors (list): List of CSS selectors to include in the extraction.
            remove_selectors (list): List of CSS selectors to remove from the extraction.
            update_file (bool, optional): Whether to update the URL configurations file. Default is True.
        """
        config = self._create_config(url_pattern, include_selectors, remove_selectors)
        self._add_new_config(config, update_entry=True)
        if update_file:
            self._update_url_configs_file()

    def _update_url_configs_file(self) -> None:
        """
        Updates the URL configurations file with the current url_configs dictionary.
        """
        with open(self.url_configs_file, 'w', encoding='utf-8') as f:
            json.dump(self.url_configs, f, indent=4)

    def _add_config(self, url_config:dict) -> None:
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
    
    def _add_new_config(self, url_config:dict, update_entry:bool=False) -> None:
        """
        Adds a URL configuration to the url_configs dictionary.
        
        Args:
            url_config (dict): A single URL configuration containing URL patterns, include, and remove selectors.
        """
        url_patterns = url_config["url_pattern"]
        matched:bool = False
        for url_pattern in url_patterns:
            if url_pattern in self.url_configs.keys():
                matched = True
        if not matched or update_entry:   
            self.url_configs[url_pattern] = {
                "include_selectors" : url_config["include_selectors"],
                "remove_selectors" : url_config["remove_selectors"]
            }
        
    def _load_url_configs_file(self, url_configs_file: str):
        """
        Loads URL configurations from a file and populates the url_configs attribute.

        Args:
            url_configs_file (str): Path to the URL configurations file.
        """
        log.debug(f"Loading URL configurations from: {url_configs_file}")
        if not Path(url_configs_file).exists():
            log.error(f"Configuration file {url_configs_file} does not exist.")
            return

        with open(url_configs_file, 'r', encoding='utf-8') as f:
            configs = json.load(f)
            log.debug(f"Loaded configurations: {configs}")

        for config in configs:
            self._add_config(config)
        log.debug(f"Final URL configurations: {self.url_configs}")

    
    def _get_selectors(self, url:str, include_default:bool = False) -> Optional[dict]:
        """
        Retrieves include and remove selectors for a given URL.

        Args:
            url (str): The URL to match against the url_configs patterns.
            include (bool, optional): Whether to skip the default settings if no match is found. Default is False. If set to True, the method will return None if no match is found.

        Returns:
            dict: A dictionary containing include and remove selectors if a match is found, None otherwise.
        """
        for url_pattern in self.url_configs.keys():
            if url_pattern in url:
                return self.url_configs[url_pattern]
        urls = []
        #check

        try:
            with open(self.unconfigured_urls_output_file, 'r', encoding='utf-8') as f:
                urls = json.load(f)
        except FileNotFoundError:
            pass

        if url not in [u['url'] for u in urls]:
            urls.append({'url': url})
            with open(self.unconfigured_urls_output_file, 'w', encoding='utf-8') as f:
                json.dump(urls, f, indent=4)
            log.warn(f"URL {url} added to {self.unconfigured_urls_output_file} for future reference.")
        else:
            log.warn(f"URL {url} already present in {self.unconfigured_urls_output_file}, since you're seeing this message you've read this URL before. Please add a configuration for it using add_new_config method for better results.")
        
        if "_default_" in self.url_configs.keys() and include_default:
            return self.url_configs["_default_"]
        else:
            return None

    


    def _load_html(self, url: str, timeout: float = 10, max_retries: int = 3, wait_inbetween: int = float) -> Optional[str]:
        """
        Attempts to load HTML content from a URL, with specified timeout and retries. In case of errors, it logs the error and adds the URL to the errored_urls.json file.

        Args:
            url (str): URL from which to load HTML content.
            timeout (int): Maximum time in seconds to wait for a response from the server.
            max_retries (int): Maximum number of retry attempts after the initial request fails.
            wait_inbetween (int): Wait time in seconds between retry attempts.

        Returns:
            str: The loaded HTML content as a string, or None if an error occurs.
        """
        attempt = 0
        errors = []
        while attempt <= max_retries:
            try:
                req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                with urlopen(req, timeout=timeout) as response:
                    html = response.read().decode('utf-8')
                    return html
            except IncompleteRead as e:
                log.error(f"IncompleteRead error on attempt {attempt+1} for {url}: {str(e)}")
                errors.append(str(e))
            except (HTTPError, URLError) as e:
                log.error(f"Network error on attempt {attempt+1} for {url}: {str(e)}")
                errors.append(str(e))
            except Exception as e:
                log.error(f"Unhandled error on attempt {attempt+1} for {url}: {str(e)}")
                errors.append(str(e))

            time.sleep(wait_inbetween)
            attempt += 1
        log.error(f"Failed to load HTML after {max_retries} retries for {url}")
        #add line to errored_urls.json if the line is not present
        errored_urls = []
        try:
            with open(self.errored_urls_output_file, 'r', encoding='utf-8') as f:
                errored_urls = json.load(f)
        except FileNotFoundError:
            pass

        if url not in [u['url'] for u in errored_urls]:
            errored_urls.append({'url': url, 'errors': errors})
            with open(self.errored_urls_output_file, 'w', encoding='utf-8') as f:
                json.dump(errored_urls, f, indent=4)
            log.warn(f"URL {url} errored added to {self.errored_urls_output_file} for future reference.")
        else:
            log.warn(f"URL {url} already present in {self.errored_urls_output_file}, since you're seeing this message you've read this URL before. Please add a configuration for it using add_new_config method for better results.")
        return None

      
    
    def _skim_relevant(self, html:str, selectors:dict) -> str:
        """
        Extracts relevant content from HTML based on include and remove selectors.
        First it selects the include selectors and creates a new html out of them then, it removes the remove selectors from the new html.

        Args:
            html (str): The HTML content to process.
            selectors (dict): A dictionary containing include and remove selectors.

        Returns:
            str: A string containing the extracted HTML elements.
        """
        include_selectors = selectors["include_selectors"]
        remove_selectors = selectors["remove_selectors"]
        soup = bs4.BeautifulSoup(html, 'html.parser')
        selected_elements = [str(tag) for selector in include_selectors for tag in soup.select(selector)]
        log.debug(f"Selected elements: {selected_elements}")
        selected_html = ''.join(selected_elements)
        log.debug(f"Selected HTML (before removing unwanted selectors): {selected_html}")
        for selector in remove_selectors:
            selected_soup = bs4.BeautifulSoup(selected_html, 'html.parser')
            for tag in selected_soup.select(selector):
                tag.extract()
        return selected_soup.prettify()
    
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
    
    def _set_url(self, url:str) -> None:
        """
        Sets the URL attribute to the specified URL.

        Args:
            url (str): The URL to set.
        """
        self.url = url

    def load_website(self, url:str, timeout:float=20, max_retries:int=5, wait_inbetween:float=2, download_unconfigured:bool=False) -> Optional[str]:
        """
        Loads, processes, and stores the HTML content from a specified URL.

        Args:
            url (str): The URL of the website to load.
            timeout (float, optional): Maximum time in seconds to wait for a response from the server. Default is 20.
            max_retries (int, optional): Maximum number of retry attempts after the initial request fails. Default is 5.
            wait_inbetween (float, optional): Wait time in seconds between retry attempts. Default is 2.
            download_unconfigured (bool, optional): Whether to download the HTML content for unconfigured URLs. Default is False. 
                If set to True, the method will first look for __default__ configuration in the URL configurations file and if not found, 
                it will download the full HTML content without any processing.

        Returns:
            str: The processed HTML content as a string, or None if an error occurs.
        """
        self._set_url(url)
        selectors = self._get_selectors(url, include_default=download_unconfigured)
        log.debug(f"Selectors for {url}: {selectors}")
        if selectors:
            try:
                html = self._load_html(url, timeout=timeout, max_retries=max_retries, wait_inbetween=wait_inbetween)
                html = self._make_links_absolute(html=html, url=url)
                log.debug(f"HTML loaded from {url}: \n{html}")
                selected_elements = self._skim_relevant(html=html, selectors=selectors)
                html = "".join([str(element) for element in selected_elements])
                log.debug(f"Skimmed html from {url}: \n{html}...")
                self.html_string = html
                return html
            except Exception as e:
                log.error(f"Error encountered while processing {url}: {str(e)}")
                raise e
        else:
            log.error(f"No configuration found for {url} in {self.url_configs_file}. Please add a configuration for this URL using add_new_config method or set download_unconfigured to True to download the full HTML content.")
            raise ValueError(f"No configuration found for {url} in {self.url_configs_file}. Please add a configuration for this URL using add_new_config method or set download_unconfigured to True to download the full HTML content.")
        
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
                    with open(save_path, 'wb', encoding='utf-8') as f:
                        f.write(image_data)
                    log.info(f"{url} saved to {save_path}")
                    return str(save_path)
                else:
                    raise RuntimeError(f"Image failed to download, returned code {response.status}")
        except HTTPError as e:
            log.error(f"HTTP Error encountered: {e.code} - {e.reason}")
        except URLError as e:
            log.error(f"URL Error encountered: {e.reason}")
        return ""

    def save_html(self, file_path:str = None) -> None:
        """
        Saves the processed HTML content to a file.

        Args:
            file_path (str, optional): The path to save the HTML content. If not provided derived from the URL.
        """
        if self.html_string is None:
            log.error("No HTML content to save. Please load a website first.")
            raise ValueError("No HTML content to save. Please load a website first.")
        if file_path is None:
            file_path = Path(urlparse(self.url).path).name + ".html"
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(self.html_string)
        log.info(f"HTML content saved to {file_path}")
        return file_path
    
    def download_website(self, url:str, save_dir:str = None, file_name:str = None, make_dir:bool = True, with_images:bool = False) -> str:
        """
        Downloads and saves a website's HTML content and optionally images.

        Args:
            url (str): The URL of the website to download.
            save_dir (str, optional): The directory to save the HTML file. Default is the current directory.
            file_name (str, optional): The name of the HTML file. Derived from the URL if not provided.
            make_dir (bool, optional): Whether to create the save directory if it does not exist. Default is True.
            with_images (bool, optional): Whether to download images from the website. Default is False.

        Returns:
            str: The path to the saved HTML file.
        """
        html = self.load_website(url)
        if with_images:
            soup = bs4.BeautifulSoup(html, 'html.parser')
            image_urls = [img['src'] for img in soup.find_all('img', src=True)]
            for image_url in image_urls:
                new_image_path = self.download_image(image_url, save_dir=save_dir, make_dir=make_dir)
                html = html.replace(image_url, new_image_path)
        return self.save_html(file_path=file_name)