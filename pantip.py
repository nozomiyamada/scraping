import requests
import os
import json
from bs4 import BeautifulSoup
from selenium.webdriver import Chrome, ChromeOptions

def text_trim(text):
    """
    trim scraped text from html
    """
    text = text.replace('\n\t\t\t\t\t\t\t\t', '')  # beginning of content
    text = text.replace('\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t', '')  # end of content
    text = text.replace('\n\n\t\t\t\t\t\t', '')  # beginning of comment
    text = text.replace('\n\t\t\t\t\t\t\n\n\n', '')  # end of comment
    text = text.replace('\n', ' ')
    text = text.replace('\t', ' ')
    text = text.replace('\u200b', '')
    text = text.replace('\xa0', ' ')
    text = text.replace('&nbsp;', ' ')
    text = text.replace('&ndash;', '–')
    text = text.replace('&amp;', '&')
    text = text.replace('&lsquo;', '‘')
    text = text.replace('&rsquo;', '’')
    text = text.replace('&ldquo;', '“')
    text = text.replace('&rdquo;', '”')
    text = text.strip()  # remove before and after whitespace
    return text


def return_str(text):
    """
    return original text if any
    return '' if None
    """
    if text is None:
        return ''
    else:
        return text_trim(text)


def scrape_pantip(start_id, end_id, file_path='/Users/Nozomi/files/pantip.json'):

    # if json file exists, load it as dict
    if os.path.exists(file_path) == True:
        print('file exists')
        with open(file_path, 'r', encoding='utf-8') as f:  # open existing file
            dic_all = json.load(f)
    else:
        dic_all = {}  # create a new dict

    # selenium (headless)
    options = ChromeOptions()
    options.add_argument('--headless')  # not open browser
    driver = Chrome(options=options)

    # scraping
    url = 'https://pantip.com/topic/'

    for article_id in range(start_id, end_id):  # id = 30000000 (8 digits)
        response = requests.get(url + str(article_id))
        if response.status_code == 200:  # if 404 pass
            driver.get(url + str(article_id))
            html = driver.page_source.encode('utf-8')
            soup = BeautifulSoup(html, "lxml")  # get html

            dic = {}
            title = soup.find('h2', class_="display-post-title").text
            tags = [x.text for x in soup.find_all('a', class_="tag-item cs-tag_topic_title")]
            content = soup.find('div', class_="display-post-story")
            content = return_str(content.text)  # remove whitespaces
            comments = soup.find_all('div', class_='display-post-story-wrapper comment-wrapper')
            comments = [return_str(comment.text) for comment in comments]
            comments = [comment for comment in comments if comment != '']

            dic['title'] = title
            dic['tags'] = tags
            dic['content'] = content
            dic['comment'] = comments
            dic_all[article_id] = dic

    with open(file_path, 'w', encoding='utf-8') as f:  # save as json
        json.dump(dic_all, f, indent=4)


def open_json(file_path='/Users/Nozomi/files/pantip.json'):

    with open(file_path, 'r', encoding='utf-8') as f:
        dic_all = json.load(f)
    return dic_all

