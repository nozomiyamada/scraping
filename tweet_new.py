from time import sleep
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from bs4 import BeautifulSoup
import pandas as pd
import tkinter as tk
import tkinter.ttk as ttk
from tkinter import filedialog
import re, json, os, sys, glob, requests, datetime, calendar

##### GUI #####

def main():
    root = tk.Tk()
    #root.geometry('750x500+300+100')
    root.title("tweet scraper")

    # Select Language
    label_lang = tk.Label(root, text='language'); label_lang.grid(row=0, column=0, columnspan=4, sticky=tk.W)
    lang_value = tk.StringVar(); lang_value.set('th')
    lang1 = tk.Radiobutton(root, text='th', variable=lang_value, value='th')
    lang1.grid(row=1, column=0)
    lang2 = tk.Radiobutton(root, text='en', variable=lang_value, value='en')
    lang2.grid(row=1, column=1)
    lang3 = tk.Radiobutton(root, text='jp', variable=lang_value, value='jp')
    lang3.grid(row=1, column=2)
    lang3 = tk.Radiobutton(root, text='none', variable=lang_value, value='none')
    lang3.grid(row=1, column=3)
    
    # query
    label_q = tk.Label(root, text='query'); label_q.grid(row=2, column=0, columnspan=4, sticky=tk.W)
    query = tk.StringVar()
    form_q = tk.Entry(root, justify='center', textvariable=query)
    form_q.grid(row=3, column=0, columnspan=4, sticky=tk.W)

    # function to convert into 2 digit string e.g. 1 -> 01
    def to2d(month:int):  
        month = str(month)
        return month if len(month) == 2 else '0'+ month

    # year from
    year_today = datetime.datetime.today().year
    month_today = datetime.datetime.today().month
    day_today = datetime.datetime.today().day
    
    label_from = tk.Label(root, text='from'); label_from.grid(row=4, column=0, columnspan=4, sticky=tk.W)
    year_from = ttk.Combobox(root)
    year_from['values'] = [f'{year_today}-{to2d(m)}-01' for m in range(month_today, 0, -1)] + [f'{y}-{to2d(m)}-01' for y in range(year_today-1, 2005, -1) for m in range(12, 0, -1)]
    year_from.grid(row=5, column=0, columnspan=4, sticky=tk.W)
    
    # year to
    label_to = tk.Label(root, text='to'); label_to.grid(row=6, column=0, columnspan=4, sticky=tk.W)
    year_to = ttk.Combobox(root)
    year_to['values'] = [f'{year_today}-{to2d(month_today)}-{day_today}'] + [f'{year_today}-{to2d(m)}-{calendar.monthrange(year_today, m)[-1]}' for m in range(month_today-1, 0, -1)] \
                        + [f'{y}-{to2d(m)}-{calendar.monthrange(y, m)[-1]}' for y in range(year_today-1, 2005, -1) for m in range(12, 0, -1)]
    year_to.grid(row=7, column=0, columnspan=4, sticky=tk.W)

    # every
    label_every = tk.Label(root, text='every n minutes'); label_every.grid(row=8, column=0, columnspan=4, sticky=tk.W)
    every_value = tk.IntVar(); every_value.set(0)
    every1 = tk.Radiobutton(root, text='none', variable=every_value, value=0)
    every1.grid(row=9, column=0)
    every2 = tk.Radiobutton(root, text='60 min', variable=every_value, value=1)
    every2.grid(row=9, column=1)
    every3 = tk.Radiobutton(root, text='30 min', variable=every_value, value=2)
    every3.grid(row=9, column=2)
    every3 = tk.Radiobutton(root, text='10 min', variable=every_value, value=3)
    every3.grid(row=9, column=3)

    # output file type
    label_filetype = tk.Label(root, text='save file type'); label_filetype.grid(row=10, column=0, columnspan=4, sticky=tk.W)
    filetype_value = tk.BooleanVar(); filetype_value.set(True)
    def btn_click_json():
        form_save.delete(0, tk.END)
        form_save.insert(0, 'a.json')
    def btn_click_csv():
        form_save.delete(0, tk.END)
        form_save.insert(0, 'a.csv')
    filetype1 = tk.Radiobutton(root, text='JSON', variable=filetype_value, value=True, command=btn_click_json)
    filetype1.grid(row=11, column=0, columnspan=2)
    filetype2 = tk.Radiobutton(root, text='CSV', variable=filetype_value, value=False, command=btn_click_csv)
    filetype2.grid(row=11, column=2, columnspan=2)
    
    # file name
    label_save = tk.Label(root, text='file path'); label_save.grid(row=12, column=0, columnspan=4, sticky=tk.W)
    filepath = tk.StringVar()
    form_save = tk.Entry(root, textvariable=filepath)
    form_save.insert(0, 'a.json')
    form_save.grid(row=13, column=0, columnspan=4, sticky=tk.W+tk.E)

    def to_none(text:str):
        return None if text == '' else text
    
    def start():
        inst = ScrapeTweet(filepath = form_save.get(),
            query = to_none(form_q.get()),
            times_per_hour = every_value.get(),
            scroll_time = 30,
            lang = lang_value.get(),
            month_from = to_none(year_from.get()),
            month_to = to_none(year_to.get()),
            is_json = filetype_value.get())
        inst.scrape_tweet_noloop(start_date=1)

    button = tk.Button(root, text='START SCRAPING', command=start)
    button.grid(row=14, column=1, columnspan=2)

    fff = tk.StringVar()
    L = tk.Label(root, textvariable=fff); L.grid(row=15)
    root.mainloop()

##### functions for scraping #####

def convert_int(num_str):
    """
    convert string to int in reply, retweet, like
    '56 ' > 56
    '' > 0
    """
    if num_str == '':
        return 0
    else:
        return int(num_str.strip())

def scrape_from_html(html:str):
    """
    scrape all tweets from html of one page
    """
    soup = BeautifulSoup(html, 'html.parser')

    # get the list of tweet contents, <li class='js-stream-item stream-item stream-item'>
    contents = soup.find_all('article')
    tweet_list = []

    # iterate content in list
    for content in contents:
        date = content.time.get('datetime')[:-5]
        displayname = content.find_all("a")[1].span.text
        username = content.find_all("a")[1].get('href')[1:]
        tweetid = content.find_all('a')[2].get('href').split('/')[-1]
        
        # tweet is in 1-2-2-2th div
        # if reply, tweet is in 1-2-2-3th div
        tweet, hashtags = '', []
        div_tweet = content.div.find_all('div',recursive=False)[1].find_all('div',recursive=False)[1].find_all('div',recursive=False)[1]
        
        if div_tweet.text.startswith('Replying to'):
            reply_to = div_tweet.text.split('Replying to')[-1].strip()
            div_tweet = content.div.find_all('div',recursive=False)[1].find_all('div',recursive=False)[1].find_all('div',recursive=False)[2]
        else:
            reply_to = None

        for child in div_tweet.findChildren(recursive=False):
            if child.name == 'span':
                text = child.text
                if text.startswith('#'):
                    hashtags.append(text[1:])
                    tweet += text
                elif child.img != None: # for emoji
                    tweet += child.img.get('alt')
                else:
                    tweet += text
            elif child.name == 'a':
                tweet += child.text
        lang = div_tweet.get('lang')
        
        # reply is in 1-2-2-3or4th div : role='group'
        div_reply = content.find('div', role='group')
        reply = div_reply.find_all('div',recursive=False)[0].div.get('aria-label').split('Repl')[0]
        retweet = div_reply.find_all('div',recursive=False)[1].div.get('aria-label').split('Retweet')[0]
        like = div_reply.find_all('div',recursive=False)[2].div.get('aria-label').split('Like')[0]

        dic = {
            'date':date,
            'displayname':displayname,
            'username':username,
            'reply_to':reply_to,
            'tweet':tweet.strip(),
            'hashtag':hashtags,
            'language':lang,
            'reply':convert_int(reply),
            'retweet':convert_int(retweet),
            'like':convert_int(like),
            'url':f'https://twitter.com/tweet/status/{tweetid}',
        }
        tweet_list.append(dic)
    
    return sorted(tweet_list, key=lambda x:x['url'], reverse=True)

##### class #####

class ScrapeTweet:
    def __init__(self, filepath, query=None, times_per_hour=6, 
    scroll_time=30, lang=None, month_from=None, month_to=None, is_json=True):
        self.filepath = filepath  # '/Users/Nozomi/files/tweet/'
        self.times_per_hour = times_per_hour  # none, 1, 2, 6
        self.scroll_time = scroll_time  # how many times to scroll in one page 
        self.month_from = month_from  # request parameter since
        self.month_to = month_to  # request parameter until
        self.is_json = True  # True: JSON, False: CSV
        if query != None:
            self.url = f'https://twitter.com/search?q={query}%20'
        else:
            self.url = f'https://twitter.com/search?q='
        if lang != None:
            self.url += f'lang%3A{lang}%20'

    def scrape_tweet_noloop(self, start_date=1):
        #options = Options()
        #options.add_argument('-headless')
        #driver = webdriver.Firefox(firefox_options=options)
        driver = webdriver.Chrome()
        if self.month_from != None:
            self.url += f'since%3A{self.month_from}%20'
        if self.month_to != None:
            self.url += f'until%3A{self.month_to}%20'
        driver.get(self.url)

        # scroll k times
        scrollheight_list = []
        while True:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")  # scroll to the bottom
            scrollheight_list.append(driver.execute_script("return document.body.scrollHeight;"))
            sleep(1)
            if len(scrollheight_list) >= 4:
                if len(set(scrollheight_list[-4:])) == 1:
                    break
            else:
                scrollheight_list = scrollheight_list[-4:]

        # scraping
        html = driver.page_source.encode('utf-8')
        result = scrape_from_html(html)
        if self.is_json:
            with open(self.filepath, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=4, ensure_ascii=False)
        else:
            pd.DataFrame(result).to_csv(self.filepath, encoding='utf-8', index=None)

        #driver.close()

    def scrape_tweet_day(self, month, start_date=1):
        """
        month: month2013_10 = ['2013-10-1', '2013-10-2',...]
        """
        files = sorted(glob.glob(self.path + month[0].rsplit('-',1)[0] + '/*.tsv'))
        print(sorted([x.rsplit('/')[-1] for x in files]))
        #options = Options()
        #options.add_argument('-headless')
        #driver = webdriver.Firefox(firefox_options=options)
        driver = webdriver.Firefox()

        for day_idx in tqdm.tqdm(range(start_date-1, len(month)-1), desc='day'):
            day_since = month[day_idx] 
            day_until = month[day_idx+1]  # if the time is 23:50, override 'day_to' below

            filename = f'{self.path}{month[0].rsplit("-",1)[0]}/{day_since}.tsv'
            if filename in files: # if exists, append
                # open file once for making tweet ID list
                with open(filename, 'r', encoding='utf-8') as f:
                    tweet_id_exist = [line[1] for line in csv.reader(f, delimiter='\t')]
                write_file = open(filename, 'a', encoding='utf-8')
            else:
                write_file = open(filename, 'w', encoding='utf-8')
                tweet_id_exist = []
            writer = csv.writer(write_file, delimiter='\t', lineterminator='\n')

            url = self.url + f'%20since%3A{day_since}_0:00_ICT%20until%3A{day_until}_0:00_ICT'
            driver.get(url)

            # scroll k times
            scrollheight = []
            for _ in range(self.scroll_time):
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")  # scroll to the bottom
                scrollheight.append(driver.execute_script("return document.body.scrollHeight;"))
                sleep(1)
                if len(scrollheight) >= 3 and len(set(scrollheight[-3:])) == 1:
                    break

                # scraping
                id_compile = re.compile('tweet js-stream-tweet .*')
                tweet_compile = re.compile('TweetTextSize .*')
                html = driver.page_source.encode('utf-8')
                soup = BeautifulSoup(html, "html.parser")  # get html
                id_html = soup.find_all('div', class_=id_compile)  # get user id and tweet id
                tweet_html = soup.find_all('p', class_=tweet_compile)  # get tweet and hash tag
                """ hash tags
                if tweet_html[k].find('a') is not None:
                    hashtags = tweet_html[k].find_all('a')
                    hashtag = [unquote(tag.get('href').split('/hashtag/')[-1].strip('?src=hash')) for tag in hashtags]
                else:
                    hashtag = 'None'
                """

                # check banned tweet
                id_html_checked = [a for a in id_html if ('because it violates' not in a.text and 'has been withheld' not in a.text and 'This Tweet is unavailable' not in a.text)]
                for k in range(len(id_html_checked)):
                    user_id = id_html_checked[k].get('data-permalink-path').split('/status/')[0].strip('/')
                    tweet_id = id_html_checked[k].get('data-permalink-path').split('/status/')[-1]
                    tweet = tweet_html[k].text
                    line = [user_id, tweet_id, tweet]
                    if tweet_id not in tweet_id_exist:
                        writer.writerow(line)

            write_file.close()
        driver.close()

    def scrape_from_now(self, filename):
        """
        month: month2013_10 = ['2013-10-1', '2013-10-2',...]
        """
        #options = Options()
        #options.add_argument('-headless')
        #driver = webdriver.Firefox(firefox_options=options)
        driver = webdriver.Firefox()

        filepath = f'{self.path}/{filename}'
        if os.path.exists(filepath): # if exists, append
            # open file once for making tweet ID list
            with open(filepath, 'r', encoding='utf-8') as f:
                tweet_id_exist = [line[1] for line in csv.reader(f, delimiter='\t')]
            write_file = open(filepath, 'a', encoding='utf-8')
        else:
            write_file = open(filepath, 'w', encoding='utf-8')
            tweet_id_exist = []
        writer = csv.writer(write_file, delimiter='\t', lineterminator='\n')

        url = self.url
        driver.get(url)

        # scroll k times
        scrollheight = []
        for t in range(self.scroll_time):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")  # scroll to the bottom
            scrollheight.append(driver.execute_script("return document.body.scrollHeight;"))
            sleep(1)
            if len(scrollheight) >= 3 and len(set(scrollheight[-3:])) == 1:
                break

        # scraping
        id_compile = re.compile('tweet js-stream-tweet .*')
        tweet_compile = re.compile('TweetTextSize .*')
        html = driver.page_source.encode('utf-8')
        soup = BeautifulSoup(html, "html.parser")  # get html
        id_html = soup.find_all('div', class_=id_compile)  # get user id and tweet id
        tweet_html = soup.find_all('p', class_=tweet_compile)  # get tweet and hash tag
        """ hash tags
        if tweet_html[k].find('a') is not None:
            hashtags = tweet_html[k].find_all('a')
            hashtag = [unquote(tag.get('href').split('/hashtag/')[-1].strip('?src=hash')) for tag in hashtags]
        else:
            hashtag = 'None'
        """

        # check banned tweet
        id_html_checked = [a for a in id_html if ('because it violates' not in a.text and 'has been withheld' not in a.text and 'This Tweet is unavailable' not in a.text)]
        for k in range(len(id_html_checked)):
            user_id = id_html_checked[k].get('data-permalink-path').split('/status/')[0].strip('/')
            tweet_id = id_html_checked[k].get('data-permalink-path').split('/status/')[-1]
            tweet = tweet_html[k].text
            line = [user_id, tweet_id, tweet]
            if tweet_id not in tweet_id_exist:
                writer.writerow(line)

        write_file.close()
        #driver.close()
"""
if __name__ == "__main__":
    main()
"""