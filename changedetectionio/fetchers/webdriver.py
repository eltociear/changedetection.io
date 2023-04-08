from . import Fetcher
import os
import time

class fetcher(Fetcher):
    if os.getenv("WEBDRIVER_URL"):
        fetcher_description = "WebDriver Chrome/Javascript via '{}'".format(os.getenv("WEBDRIVER_URL"))
    else:
        fetcher_description = "WebDriver Chrome/Javascript"

    command_executor = ''

    # Configs for Proxy setup
    # In the ENV vars, is prefixed with "webdriver_", so it is for example "webdriver_sslProxy"
    selenium_proxy_settings_mappings = ['proxyType', 'ftpProxy', 'httpProxy', 'noProxy',
                                        'proxyAutoconfigUrl', 'sslProxy', 'autodetect',
                                        'socksProxy', 'socksVersion', 'socksUsername', 'socksPassword']
    proxy = None

    def __init__(self, proxy_override=None, command_executor=None):
        super().__init__()
        from selenium.webdriver.common.proxy import Proxy as SeleniumProxy

        # .strip('"') is going to save someone a lot of time when they accidently wrap the env value
        if command_executor:
            self.command_executor = command_executor
        else:
            self.command_executor = os.getenv("WEBDRIVER_URL", 'http://browser-chrome:4444/wd/hub').strip('"')

        # If any proxy settings are enabled, then we should setup the proxy object
        proxy_args = {}
        for k in self.selenium_proxy_settings_mappings:
            v = os.getenv('webdriver_' + k, False)
            if v:
                proxy_args[k] = v.strip('"')

        # Map back standard HTTP_ and HTTPS_PROXY to webDriver httpProxy/sslProxy
        if not proxy_args.get('webdriver_httpProxy') and self.system_http_proxy:
            proxy_args['httpProxy'] = self.system_http_proxy
        if not proxy_args.get('webdriver_sslProxy') and self.system_https_proxy:
            proxy_args['httpsProxy'] = self.system_https_proxy

        # Allows override the proxy on a per-request basis
        if proxy_override is not None:
            proxy_args['httpProxy'] = proxy_override

        if proxy_args:
            self.proxy = SeleniumProxy(raw=proxy_args)

    def run(self,
            url,
            timeout,
            request_headers,
            request_body,
            request_method,
            ignore_status_codes=False,
            current_include_filters=None,
            is_binary=False):

        from selenium import webdriver
        from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
        from selenium.common.exceptions import WebDriverException
        # request_body, request_method unused for now, until some magic in the future happens.

        # check env for WEBDRIVER_URL
        self.driver = webdriver.Remote(
            command_executor=self.command_executor,
            desired_capabilities=DesiredCapabilities.CHROME,
            proxy=self.proxy
        )

        try:
            self.driver.get(url)
        except WebDriverException as e:
            # Be sure we close the session window
            self.quit()
            raise

        self.driver.set_window_size(1280, 1024)
        self.driver.implicitly_wait(int(os.getenv("WEBDRIVER_DELAY_BEFORE_CONTENT_READY", 5)))

        if self.webdriver_js_execute_code is not None:
            self.driver.execute_script(self.webdriver_js_execute_code)
            # Selenium doesn't automatically wait for actions as good as Playwright, so wait again
            self.driver.implicitly_wait(int(os.getenv("WEBDRIVER_DELAY_BEFORE_CONTENT_READY", 5)))

        # @todo - how to check this? is it possible?
        self.status_code = 200
        # @todo somehow we should try to get this working for WebDriver
        # raise EmptyReply(url=url, status_code=r.status_code)

        # @todo - dom wait loaded?
        time.sleep(int(os.getenv("WEBDRIVER_DELAY_BEFORE_CONTENT_READY", 5)) + self.render_extract_delay)
        self.content = self.driver.page_source
        self.headers = {}

        self.screenshot = self.driver.get_screenshot_as_png()

    # Try something with requests?
    def is_ready(self):
        return True

