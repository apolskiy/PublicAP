import requests
from urllib.parse import urlparse
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By



class BasePage:
    def __init__(self, driver: WebDriver):
        self._driver = driver

    def open_url(self, url: str):
        self._driver.get(url)

    def _find(self, locator: tuple) -> WebElement:
        return self._driver.find_element(*locator)

    def _type(self, locator: tuple, text: str):
        self._wait_until_element_is_visible(locator)
        self._find(locator).send_keys(text)

    def _click(self, locator: tuple, time: int = 2):
        self._wait_until_element_is_visible(locator, time)
        self._find(locator).click()

    def _wait_until_url_contains(self, url: str, time: int = 2):
        WebDriverWait(self._driver, time).until(ec.url_contains(url))

    def _wait_until_element_is_visible(self, locator: tuple, time: int = 2):
        WebDriverWait(self._driver, time).until(ec.visibility_of_element_located(locator))

    def _wait_until_element_is_not_visible(self, locator: tuple, time: int = 2):
        WebDriverWait(self._driver, time).until(ec.invisibility_of_element_located(locator))

    def is_displayed(self, locator: tuple) -> bool:
        try:
            return self._find(locator).is_displayed()
        except NoSuchElementException:
            return False

    def _contains_text(self, locator: tuple, text: str):
        element_text = self._find(locator).text
        assert text in element_text, f"Expected '{text}' in '{element_text}'"

    def _switch_tab(self, tab: str):
        if tab == "child":
            window = self._driver.window_handles[1]
        elif tab == "parent":
            window = self._driver.window_handles[0]
        elif tab == "original":
            window = self._driver.current_window_handle
        else:
            raise ValueError(f"Unknown tab option: {tab}")
        self._driver.switch_to.window(window)

    def _drag_and_drop(self, locator1: tuple, locator2: tuple):
        source = self._find(locator1)
        target = self._find(locator2)
        ActionChains(self._driver).drag_and_drop(source, target).perform()

    #Aleksandr Polskiy 10/3/2025 added function to return page title
    def check_page_title(self) -> str:
        return self._driver.title

    #Aleksandr Polskiy 10/3/2025 added function to check for errors, list with errors will be returned
    #returninf list/array of errors. List of errors will be printed just in case if len  greater than 0
    def check_page_for_errors(self) -> list[str]:
        logs = self._driver.get_log('browser')
        page_errors = []
        for log in logs:
            if log['level'] == 'SEVERE' or log['level'] == 'WARNING':
                page_errors.append(str(log['message']))
            if len(page_errors)>0:
                print("Errors found:".join(page_errors))
        return page_errors

    #Aleksandr Polskiy 10/3/2025 added function to check page links, returns a list of broken links
    def check_page_links(self) -> list:
        """This function finds all links with attribute a and then extracts href values
        after that it sends requests and parses each response for the presence
        of HTTP status codes 400+, which are errors and returns the list of errors, by url"""
        links = self._driver.find_elements(By.TAG_NAME, "a")
        broken_links=[]

        #this loop extracts href values from each link and sends a get request parses response headers
        for link in links:
            href = link.get_attribute("href")
            if not href is None:  # after making sure attribute is not None, i.e. exists
                try:
                    response = requests.head(href, allow_redirects=True,
                                             timeout=5)  # Using requests for an http status check
                    if response.status_code >= 400:
                        broken_links.append(href)
                finally:
                    pass
        #print("Number of broken links found: {}".format (str(len(broken_links))))
        return broken_links

    #Aleksandr Polskiy 10/3/2025 function finds buttons by class and returns list of button text values
    def find_button_text_by_class(self, class_name: str) -> list[str]:
        buttons = self._driver.find_elements(By.CSS_SELECTOR, class_name)
        button_texts = []
        for button in buttons:
            button_texts.append(button.text)
        return button_texts

    def find_text_from_rendering(self, identifier)->str:

        answer = None

        try:
            #Find all <script> elements on the page
            scripts = self._driver.find_elements(By.TAG_NAME, "script")
            print("Found {} script elements.".format(str(len(scripts))))

            #Iterate through the script elements
            for script in scripts:
                # Get the inner HTML (content) of the script tag
                focus_text = script.get_attribute("innerHTML")

                # Check if the content contains the target function call
                if focus_text and "canvas.strokeText" in focus_text:

                #3. Extract the answer using string manipulation
                    start_keyword = identifier
                    end_keyword = "',"

                    start_index = focus_text.find(start_keyword)

                    if start_index != -1:
                        # Find the end index after the start point
                        end_index = focus_text.find(end_keyword, start_index)

                        if end_index != -1:
                            # Extract the substring
                            answer = focus_text[0:end_index]
                            break  # Exit the loop once the answer is found

        except Exception as e:
            print("An error occurred during element search or {} processing: {}".format(identifier,e))
            answer = "Error during extraction."
        finally:
            return answer

class LandingPage(BasePage):
    __url = ""
    __page_header = ""
    __page_title = ""
    #added url for challenging dom page

    def __init__(self, driver: WebDriver):
        super().__init__(driver)

    def set_url(self, url: str):
        self.__url = url

    def set_page_header(self, header: str):
        self.__page_header = header

    def set_page_title(self, title: str):
        self.__page_title = title

    def open(self):
        """This function opens page if URL is not an empty string and is not None."""
        if not self.__url is None and self.__url.strip() != "":
            if urlparse(self.__url).scheme:
                self.open_url(self.__url)
                return True
            else:
                raise ValueError("Invalid URL: missing scheme")
        return False

    def header_is_displayed(self) -> bool:
        """This function checks if the page header is displayed."""
        return self.is_displayed(self.__page_header)


    def page_title_is_correct(self) -> bool:
        return self.check_page_title() == self.__page_title