from time import sleep
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from bs4 import BeautifulSoup
import pandas as pd
import tkinter as tk
import tkinter.ttk as ttk
from tkinter import filedialog
import re, csv, os, sys, glob, tqdm, requests
from datelist import *

### GUI ###

def main():
    root = tk.Tk()
    #root.geometry('750x500+300+100')
    root.title("tweet scraper")

    # Select Language
    label1 = tk.Label(root, text='language'); label1.grid(row=0, sticky=tk.W)
    lang_value = tk.IntVar(); lang_value.set(0)
    lang1 = tk.Radiobutton(root, text='none', variable=lang_value, value=0)
    lang1.grid(row=1, column=0)
    lang2 = tk.Radiobutton(root, text='th', variable=lang_value, value=1)
    lang2.grid(row=1, column=1)
    lang3 = tk.Radiobutton(root, text='en', variable=lang_value, value=2)
    lang3.grid(row=1, column=2)
    lang3 = tk.Radiobutton(root, text='jp', variable=lang_value, value=3)
    lang3.grid(row=1, column=3)
    
    # query
    label2 = tk.Label(root, text='query'); label2.grid(row=2, sticky=tk.W)
    query = tk.StringVar()
    form1 = tk.Entry(root, justify='center', textvariable=query)
    form1.grid(row=3, column=0, columnspan=4, sticky=tk.W)

    # year from
    label3 = tk.Label(root, text='from'); label3.grid(row=4, sticky=tk.W)
    year_from = tk.Entry(root, text='2020'); year_from.grid(row=5, column=0, columnspan=4, sticky=tk.W)

    # every
    label4 = tk.Label(root, text='every n minutes'); label4.grid(row=6, sticky=tk.W)
    every_value = tk.IntVar(); every_value.set(0)
    every1 = tk.Radiobutton(root, text='none', variable=every_value, value=0)
    every1.grid(row=7, column=0)
    every2 = tk.Radiobutton(root, text='60 min', variable=every_value, value=1)
    every2.grid(row=7, column=1)
    every3 = tk.Radiobutton(root, text='30 min', variable=every_value, value=2)
    every3.grid(row=7, column=2)
    every3 = tk.Radiobutton(root, text='10 min', variable=every_value, value=3)
    every3.grid(row=7, column=3)

    # save to (blank for current directory)
    label2 = tk.Label(root, text='save as'); label2.grid(row=8, sticky=tk.W)
    filepath = tk.StringVar()
    form2 = tk.Entry(root, textvariable=filepath)
    form2.grid(row=9, column=0, columnspan=4, sticky=tk.W+tk.E)
    root.mainloop()

    # output file type
    label4 = tk.Label(root, text='file type'); label4.grid(row=10, sticky=tk.W)
    filetype_value = tk.StringVar(); filetype_value.set('.csv')
    filetype1 = tk.Radiobutton(root, text='CSV', variable=filetype_value, value='.csv')
    filetype1.grid(row=11, column=0)
    filetype2 = tk.Radiobutton(root, text='JSON', variable=filetype_value, value='.json')
    filetype2.grid(row=11, column=1)


def __time_convert(tweet_time:str):
    """
    convert time format in tweeter to datetime format
    7:09 PM - 24 Jan 2020 > 2020-01-24T19:09
    1:04 AM - 25 Jan 2020 > 2020-01-25T01:04
    """
    time, ampm, _, day, month, year = tweet_time.split(' ')
    month_dic = {'Jan':'01','Feb':'02','Mar':'03','Apr':'04','May':'05','Jun':'06','Jul':'07','Aug':'08','Sep':'09','Oct':'10','Nov':'11','Dec':'12'}
    hour, minute = time.split(':')
    if ampm == 'PM':
        time = f'{int(hour)+12}:{minute}'
    elif len(hour) == 1:
        time = f'0{hour}:{minute}'
    return f'{year}-{month_dic[month]}-{day} {time}'

def scrape_from_html(html:str):
    """
    scrape all tweets from html of one page
    """
    soup = BeautifulSoup(html, 'html.parser')

    # get the list of tweet contents, <li class='js-stream-item stream-item stream-item'>
    contents = soup.find_all('li', class_='js-stream-item stream-item stream-item')
    
    # 
    tweet_list = []

    # iterate content in list
    for content in contents:

        # date : 7:09 PM - 24 Jan 2020
        date = content.small.a.get('title') 
        if date == None:
            date = content.small.a.get('data-original-title')
        name = content.div.get('data-name') # unique username
        username = content.div.get('data-screen-name') 
        userid = content.div.get('data-user-id')
        tweetid = content.get('data-item-id')
        tweet = content.find('div', class_='js-tweet-text-container').text.strip()
        lang = content.find('div', class_='js-tweet-text-container').p.get('lang')
        reply = content.find_all('span', class_='ProfileTweet-actionCount')[0].get('data-tweet-stat-count')
        retweet = content.find_all('span', class_='ProfileTweet-actionCount')[1].get('data-tweet-stat-count')
        like = content.find_all('span', class_='ProfileTweet-actionCount')[2].get('data-tweet-stat-count')
        # hashtag
        tags = content.find('div', class_='js-tweet-text-container').find_all('b')
        if tags == []:
            hashtag = None
        else:
            hashtag = ';'.join([tag.text for tag in tags])

        dic = {
            'date':__time_convert(date),
            'name':name,
            'username':username,
            'userid':userid,
            'tweet':tweet,
            'hashtag':hashtag,
            'language':lang,
            'reply':reply,
            'retweet':retweet,
            'like':like,
            'url':f'https://twitter.com/tweet/status/{tweetid}',
        }

        tweet_list.append(dic)
    
    return sorted(tweet_list, key=lambda x:x['url'])

class ScrapeTweet:
    def __init__(self, path, query=None, times_per_hour=6, scroll_time=30):
        """
        request url - use : (%3A) and space (%20)
        https://twitter.com/search?q=query%20parameter1%3Avalue%20parameter2%3Avalue
        """
        self.path = path  # '/Users/Nozomi/files/tweet/'
        self.times_per_hour = times_per_hour
        self.scroll_time = scroll_time
        if query == None:
            self.url = 'https://twitter.com/search?q=lang%3Ath'
        else:
            self.url = f'https://twitter.com/search?q={query}'

    def scrape_tweet(self, month, start_date=1): # times per hour = 6,3,2,1
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
            day_until = month[day_idx]  # if the time is 23:50, override 'day_to' below

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

            # loop for every x minute in one day
            repeat_times = 24 * self.times_per_hour
            time_list = {1:min60, 2:min30, 3:min20, 6:min10}[self.times_per_hour]
            for j in tqdm.tqdm(range(repeat_times), desc='time'):
                if j == repeat_times - 1:  # override "since:2013-1-1_23:50:00_ICT until:2013-1-2_0:00:00_ICT"
                    day_until = month[day_idx+1]

                time_since, time_until = time_list[j], time_list[j+1]
                url = self.url + f'%20since%3A{day_since}_{time_since}_ICT%20until%3A{day_until}_{time_until}_ICT'
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
                html = driver.page_source.encode('utf-8')
                soup = BeautifulSoup(html, "html.parser")  # get html
                contents = soup.find_all('li',class_="js-stream-item stream-item stream-item")
                times = [x.small.a.get('title') for x in contents]
                ids = [x.find('div', class_="stream-item-header").a.get('href')[1:] for x in contents]
                tweets = [x.find('div', class_="js-tweet-text-container").text.strip() for x in contents]
                """ hash tags
                if tweet_html[k].find('a') is not None:
                    hashtags = tweet_html[k].find_all('a')
                    hashtag = [unquote(tag.get('href').split('/hashtag/')[-1].strip('?src=hash')) for tag in hashtags]
                else:
                    hashtag = 'None'
                """

                # check banned tweet
                #id_html_checked = [a for a in id_html if ('because it violates' not in a.text and 'has been withheld' not in a.text and 'This Tweet is unavailable' not in a.text)]
                for k in range(len(times)):
                    line = [times[k], ids[k], tweets[k]]
                    writer.writerow(line)
            write_file.close()
        driver.close()

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
        driver.close()


if __name__ == "__main__":
    main()