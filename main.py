import os
import itertools
from random import random
from time import sleep
from typing import Iterator, List

from dotenv import load_dotenv
from explicit import waiter, XPATH
from selenium import webdriver
from selenium.webdriver.firefox.options import Options

load_dotenv(override=True)

USERNAME = os.getenv('USERNAME')
PASSWORD = os.getenv('PASSWORD')
LINK = os.getenv('LINK')
GECKODRIVER = os.getenv('GECKODRIVER', False)
FIREFOX_PATH = os.getenv('FIREFOX_PATH', False)

class Bot:
    def __init__(self, username, password):
        self.username = username
        self.password = password

    def start(self):
        print('starting')
        self.options = Options()
        self.options.headless = True
        if GECKODRIVER and FIREFOX_PATH:
            self.driver  = webdriver.Firefox(options=self.options, 
            firefox_binary=FIREFOX_PATH, executable_path=GECKODRIVER)
        else:
            self.driver  = webdriver.Firefox(options=self.options)

        self.driver.implicitly_wait(5)
        
        self.driver.get('http://instagram.com')
        print('Login...')
        self.login()
        print('Loading followers...')
        self.followers_list  = self.load_followers()
        print(len(self.followers_list))
        
        sleep(6)
        self.goto(LINK)
        
        sleep(20)
        print('bye!')
        self.driver.close()

    def goto(self, post_link: str) -> None:
        print('Opening post...')
        self.driver.get(f'https://www.instagram.com/p/{post_link}/')
        sleep(8)

        for a,b in zip(self.followers_list[::2], self.followers_list[1::2]):
            print(f'Commeting...')
            comment_input = self.driver.find_element_by_css_selector("textarea")
            comment_input.click()
            sleep(2)
            comment_input = self.driver.find_element_by_css_selector("textarea")
            comment_input.send_keys(f'@{a} @{b}')
            sleep(1)
            self.driver.find_element_by_css_selector("button[type=submit]").click()
            sleep(int(random() * (120 - 60)) + 60)

    def load_followers(self) -> List[str]:
        if  not os.path.exists('followers.txt'):
            with open('followers.txt', 'wt') as file:
                try:
                    for count, follower in enumerate(self.scrape_followers(), 1):
                        print("\t{:>3}: {}".format(count, follower))
                        file.write(follower+'\n')
                except:
                    pass
        return open('followers.txt','rt').readlines()

    def login(self) -> None:
        self.driver.find_element_by_css_selector("input[name='username']").send_keys(USERNAME)
        self.driver.find_element_by_css_selector("input[name='password']").send_keys(PASSWORD)
        self.driver.find_element_by_xpath("//button[@type='submit']").click()
        sleep(6)

    # I found here https://www.codegrepper.com/code-examples/whatever/scraping+instagram+followers+list+python
    def scrape_followers(self) -> Iterator[str]:
        # Load account page
        self.driver.get("https://www.instagram.com/{0}/".format(self.username))

        # Click the 'Follower(s)' link
        # driver.find_element_by_partial_link_text("follower").click
        sleep(6)
        self.driver.find_element_by_css_selector("li.Y8-fY:nth-child(2) > a:nth-child(1)").click()

        # Wait for the followers modal to load
        waiter.find_element(self.driver, "//div[@role='dialog']", by=XPATH)
        allfoll = int(self.driver.find_element_by_xpath("//li[2]/a/span").text)
        # At this point a Followers modal pops open. If you immediately scroll to the bottom,
        # you hit a stopping point and a "See All Suggestions" link. If you fiddle with the
        # model by scrolling up and down, you can force it to load additional followers for
        # that person.

        # Now the modal will begin loading followers every time you scroll to the bottom.
        # Keep scrolling in a loop until you've hit the desired number of followers.
        # In this instance, I'm using a generator to return followers one-by-one
        follower_css = "ul div li:nth-child({}) a.notranslate"  # Taking advange of CSS's nth-child functionality
        for group in itertools.count(start=1, step=12):
            for follower_index in range(group, group + 12):
                if follower_index > allfoll:
                    raise StopIteration
                yield waiter.find_element(self.driver, follower_css.format(follower_index)).text

            # Instagram loads followers 12 at a time. Find the last follower element
            # and scroll it into view, forcing instagram to load another 12
            # Even though we just found this elem in the previous for loop, there can
            # potentially be large amount of time between that call and this one,
            # and the element might have gone stale. Lets just re-acquire it to avoid
            # tha
            last_follower = waiter.find_element(self.driver, follower_css.format(group+11))
            self.driver.execute_script("arguments[0].scrollIntoView();", last_follower)


if __name__ == "__main__":
    
    bot = Bot(USERNAME,PASSWORD)
    bot.start()