import os
from dotenv import load_dotenv
load_dotenv(override=True)

settings={}
settings['username']  = os.getenv('USERNAME')
settings['password']  = os.getenv('PASSWORD')
settings['post_link']  = os.getenv('LINK')
settings['geckodriver']  = os.getenv('GECKODRIVER',False)
settings['firefox_path']  = os.getenv('FIREFOX_PATH',False)
settings['headless']  = str(os.getenv('HEADLESS',False)).lower() == 'true'
settings['custom_comment']  = os.getenv('CUSTOM_COMMENT',False)
settings['min_random_delay']  = int(os.getenv('MIN_RANDOM_DELAY', 60))
settings['max_random_delay']  = int(os.getenv('MAX_RANDOM_DELAY', 120))

