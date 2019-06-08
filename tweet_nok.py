from time import sleep
import re
import date
from bs4 import BeautifulSoup
from selenium.webdriver import Chrome, ChromeOptions
from urllib.parse import unquote
import csv
from os import makedirs


def nok(month, append=True, scroll=10
        , sleep_time=1):  # month = date.month2013_10
    """
    example:

    month = date.month2013_10 = ['2013-10-1', '2013-10-2',...]
    month[0].rsplit('-', 1) = ['2013-10', '1']
    path = './tweet_nok/nok2013-10'
    """
    # selenium (headless)
    driver = Chrome()
    sleep(1)

    path = '/Users/Nozomi/files/tweet_nok/nok' + month[0].rsplit('-', 1)[0]

    # loop for each day
    for i in range(len(month) - 1):

        since = month[i]  # the same day, if the time is 23:00, override 'until'
        until = month[i]

        if append == True:
            # open file once for making tweet ID list
            read_file = open('{}/nok{}.tsv'.format(path, since), 'r', encoding='utf-8')
            id_list = [line[1] for line in csv.reader(read_file, delimiter='\t')]
            read_file.close()

            # open file again for saving tweets in one day
            file = open('{}/nok{}.tsv'.format(path, since), 'a', encoding='utf-8')
        else:
            file = open('{}/nok{}.tsv'.format(path, since), 'w', encoding='utf-8')
        writer = csv.writer(file, delimiter='\t', lineterminator='\n')

        # loop for every hour in one day
        tweet_one_day = 0  # initialize
        for j in range(48):  # date.time30 = list of 24h

            if j == 47:  # override "since:2013-1-1_23:35:00_ICT until:2013-1-2_0:35:00_ICT"
                until = month[i+1]

            time1 = date.time30[j]
            time2 = date.time30[j+1]

            # search url e.g. "นก since:2013-1-1_16:25:00_ICT until:2013-1-1_17:25:00_ICT"
            url = "https://twitter.com/search?f=tweets&q=นก%20since%3A{}_{}_ICT%20until%3A{}_{}_ICT".format(since, time1, until, time2)
            driver.get(url)

            # scroll k times
            for t in range(scroll):
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")  # scroll to the bottom
                sleep(sleep_time)

            # scraping
            id_compile = re.compile('tweet js-stream-tweet .*')
            tweet_compile = re.compile('TweetTextSize .*')
            html = driver.page_source.encode('utf-8')
            soup = BeautifulSoup(html, "html.parser")  # get html
            id_html = soup.find_all('div', class_=id_compile)  # get user id and tweet id
            tweet_html = soup.find_all('p', class_=tweet_compile)  # get tweet and hash tag
            tweet_one_day += len(id_html)

            # check banned tweet
            id_html_checked = [a for a in id_html if ('違反しているため' not in a.text and 'because it violates' not in a.text and 'has been withheld' not in a.text and 'This Tweet is unavailable' not in a.text)]

            for k in range(len(id_html_checked)):
                user_id = id_html_checked[k].get('data-permalink-path').split('/status/')[0].strip('/')
                tweet_id = id_html_checked[k].get('data-permalink-path').split('/status/')[-1]
                tweet = tweet_html[k].text
                """
                if tweet_html[k].find('a') is not None:
                    hashtags = tweet_html[k].find_all('a')
                    hashtag = [unquote(tag.get('href').split('/hashtag/')[-1].strip('?src=hash')) for tag in hashtags]
                else:
                    hashtag = 'None'
                """
                line = [user_id, tweet_id, tweet]
                if append == True:
                    if tweet_id not in id_list:
                        writer.writerow(line)
                else:
                    writer.writerow(line)

        file.close()

    driver.close()

def sort(year_month_day):  # year_month_day = '2015-1-1'
    year_month = year_month_day.rsplit('-', 1)[0]
    path1 = '/Users/Nozomi/files/tweet_nok/nok{}/nok{}.tsv'.format(year_month, year_month_day)
    path2 = '/Users/Nozomi/files/tweet_nok/nok{}/nok{}_sort.tsv'.format(year_month, year_month_day)
    read_file = open(path1, 'r', encoding='utf-8')
    save_file = open(path2, 'w', encoding='utf-8')
    writer = csv.writer(save_file, delimiter='\t', lineterminator='\n')

    id_list = []
    for line in csv.reader(read_file, delimiter='\t'):
        if line[1] not in id_list:
            writer.writerow(line)
            id_list.append(line[1])

    read_file.close()
    save_file.close()
