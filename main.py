import os
import itertools
from random import random
from time import sleep
from typing import Iterator, List

from explicit import waiter, XPATH
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from settings import settings

class Bot:
    def __init__(self, username, password, post_link,
                geckodriver=False,firefox_path=False,
                headless=False,custom_comment=False,
                min_random_delay=60,max_random_delay=120):
        """
        Starts a new bot instance.

        :param username: account name used on Instagram.
        :param password: password to login.
        :param post_link: link to post on Instagram.
        :param geckodriver: path to geckodriver executable.
        :param headless: boolean for headless param for Firefox Options.
        :param custom_element: a text to append to comment alongside mentions.
        :param min_random_delay: minium integer seconds for random delay between each comments.
        :param max_random_delay: maximum integer seconds for random delay between each comments.  
        """
        self.username = username
        self.password = password
        self.post_link = post_link
        self.geckodriver = geckodriver
        self.firefox_path = firefox_path
        self.headless = headless
        self.custom_comment = custom_comment
        self.min_random_delay = min_random_delay
        self.max_random_delay = max_random_delay

        self.options = Options()
        self.options.headless = bool(self.headless)
        if self.geckodriver and self.firefox_path:
            self.driver  = webdriver.Firefox(options=self.options, 
            firefox_binary=self.firefox_path, executable_path=self.geckodriver)
        else:
            self.driver  = webdriver.Firefox(options=self.options)

    def start(self):
        """Starts the bot"""
        print('Login...')
        self.login()
        print('Loading followers...')
        self.load_accounts()
        print(len(self.accounts_list))
        
        sleep(6)
        self.open_post(self.post_link)
        sleep(8)
        last_state = 0
        state_path = f'{self.post_link}_state.txt'
        if os.path.exists(state_path):
            last_state = int(open(state_path,'r').readlines()[-1].strip())
        print('last index: ', last_state)
        self.accounts_list = self.accounts_list[last_state+1:]
        for a,b in zip(self.accounts_list[::2], self.accounts_list[1::2]):
            print(f'Commenting...')
            comment_input = self.driver.find_element_by_css_selector("textarea")
            comment_input.click()
            sleep(2)
            comment_input = self.driver.find_element_by_css_selector("textarea")
            if self.custom_comment:
                comment_input.send_keys(f'{self.custom_comment} @{a} @{b}')
            else:
                comment_input.send_keys(f'@{a} @{b}')
            sleep(6)
            self.driver.find_element_by_css_selector("button[type=submit]").click()
            last_state_file = open(state_path,'w')
            last_state += 2
            last_state_file.write(f'{last_state}\n')
            last_state_file.close()
            sleep(int(random() * (self.max_random_delay - self.min_random_delay)) + self.min_random_delay)
        sleep(20)
        print('bye!')
        self.driver.close()

    def open_post(self, post_link: str) -> None:
        """Open post link"""
        print('Opening post...')
        self.driver.get(f'https://www.instagram.com/p/{post_link}/')

    def _load_accounts_file(self) -> List[str]:
        """Load all accounts from file."""
        return list(map(lambda x: x.strip(), open('accounts.txt','r').readlines()))

    def _load_followers(self, account) -> List[str]:
        """Scrap and convert into list all followers from account name."""

        tmp_list = []
        try:
            for count, follower in enumerate(self._scrape_followers(account=account), 1):
                    tmp_list.append(follower)
        except:
            pass
        return tmp_list

    def upsert_accounts(self, account):
        """
        Load accounts with followers from passed account and 
        create/update the accounts.txt file.
        :param account: account name.
        """

        self.accounts_list = list(set(self.accounts_list + self._load_followers(account)))
        with open('accounts.txt','a') as f:
            tmp = list(map(lambda x: x+'\n', self.accounts_list))
            f.writelines(tmp)

    def load_accounts(self) -> None:
        """Load accounts with followers list from current logged account""" 
        if  not os.path.exists('accounts.txt'):
            self.upsert_accounts(self.username)
        else:
            self.accounts_list = self._load_accounts_file()

    def login(self) -> None:
        """Login the user"""
        self.driver.implicitly_wait(5)
        self.driver.get('http://instagram.com')
        self.driver.find_element_by_css_selector("input[name='username']").send_keys(self.username)
        self.driver.find_element_by_css_selector("input[name='password']").send_keys(self.password)
        self.driver.find_element_by_xpath("//button[@type='submit']").click()
        sleep(6)

    # I found here https://www.codegrepper.com/code-examples/whatever/scraping+instagram+followers+list+python
    def _scrape_followers(self, account) -> Iterator[str]:
        # Load account page
        self.driver.get("https://www.instagram.com/{0}/".format(account))

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
    if settings['username'] is None:
        print('USERNAME is empty')
        exit(0)
    elif settings['password'] is None:
        print('PASSWORD is empty')
        exit(0)
    elif settings['post_link'] is None:
        print('LINK is empty')
        exit(0)
    
    bot = Bot(username=settings['username'],password=settings['password'], post_link=settings['post_link'],
              geckodriver=settings['geckodriver'],firefox_path=settings['firefox_path'],
                headless=settings['headless'],custom_comment=settings['custom_comment'],
                min_random_delay=settings['min_random_delay'],max_random_delay=settings['max_random_delay'])
    # bot.start()