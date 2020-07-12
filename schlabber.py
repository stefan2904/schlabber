#!/usr/bin/env python3
import os
import stat
import argparse
import requests
import json
import pprint
import hashlib
from bs4 import BeautifulSoup

class Soup:
    def assertdir(self,dirname):
        if not os.path.isdir(dirname):
            os.makedirs(dirname)

    def has_valid_timestamp(self, meta):
        return meta and 'time' in meta and meta['time']

    def __init__(self, soup, bup_dir):
        self.rooturl = "http://"+soup+".soup.io"
        self.bup_dir = os.path.abspath(bup_dir)
        self.assertdir(self.bup_dir)
        self.dlnextfound = False
        self.sep = os.path.sep
        print("Backup: " + self.rooturl)
        print("into: " + self.bup_dir)

    def find_next_page(self, cur_page):
        for script in cur_page.find_all('script'):
            if script.string and "SOUP.Endless.next_url" in script.string:
                print("\t...found")
                self.dlnextfound = True
                return script.string.split('\'')[-2].strip()
        self.dlnextfound = False
        return ""

    def get_asset_name(self, name):
        return name.split('/')[-1].split('.')[0]

    def get_timstemp(self, post):
        for time_meta in post.find_all("abbr"):
            return time_meta.get('title').strip().split(" ")
        return None

    def write_meta(self, meta):
        basepath = self.bup_dir + self.sep
        self.assertdir(basepath + "meta" + self.sep )
        filename = basepath + "meta" + self.sep + meta['id'] + ".json"
        if os.path.isfile(filename):
            # skip, it exists:
            return
        with open(filename, 'w') as outfile:
            json.dump(meta, outfile)

    def write_raw(self, post):
        basepath = self.bup_dir + self.sep + "raw" + self.sep
        self.assertdir(basepath)
        with open(basepath + post['id'] + ".html", 'w') as outfile:
            outfile.write(str(post))

    def process_image(self, post):
        print("\t\tImage:")
        meta = {}
        meta['time'] = self.get_timstemp(post)
        for caption in post.find_all("div", {'class': 'caption'}):
            meta['source'] = caption.find('a').get("href")
        for desc in post.find_all("div", {'class': 'description'}):
            meta['text'] = desc.get_text()
        for link in post.find_all('div', {"class":"imagecontainer"}):
            lightbox = link.find("a", {"class": "lightbox"})
            if lightbox:
                meta['soup_url'] = lightbox.get('href')
            else:
                meta['soup_url'] = link.find("img").get('src')
        if 'soup_url' in meta:
            basepath = self.bup_dir + self.sep
            if self.has_valid_timestamp(meta):
                basepath = basepath + meta['time'][2] + self.sep + meta['time'][0] + self.sep
            filename = self.get_asset_name(meta['soup_url'])
            path = basepath + filename + "." + meta['soup_url'].split(".")[-1]
            if os.path.isfile(path) == True:
                print("\t\t\tSkip " + meta['soup_url'] + ": File exists")
            else:
                print("\t\t\tsoup_url: " + meta['soup_url'] + " -> " + path)
                self.assertdir(basepath)
                r = requests.get(meta['soup_url'], allow_redirects=True)
                with open(path, "wb") as tf:
                    tf.write(r.content)
                self.write_raw(post)

    def process_quote(self, post):
        print("\t\tQuote:")
        meta = {}
        meta['time'] = self.get_timstemp(post)
        body = post.find("span", {"class", 'body'}).get_text()
        author = post.find("cite").get_text()
        quote = '"' + body + '"' + "\n\t" + author + "\n"
        qhash = hashlib.sha256(quote.encode())
        hashsum = str(qhash.hexdigest().upper())
        filename = "quote_" + hashsum + ".txt"
        basepath = self.bup_dir + self.sep
        if self.has_valid_timestamp(meta):
            basepath = basepath + meta['time'][2] + self.sep + meta['time'][0] + self.sep
        path = basepath + filename
        if os.path.isfile(path) == True:
            print("\t\t\tSkip: " + filename + ": File exists")
        else:
            self.assertdir(basepath)
            print("\t\t\t-> " + path)
            with open(path, "w") as qf:
                qf.write(quote)
            self.write_raw(post)


    def process_link(self, post):
        print("\t\tLink:")
        meta = {}
        meta['time'] = self.get_timstemp(post)
        linkelem = post.find("h3")
        meta["link_title"] = linkelem.get_text().strip()
        meta["url"] = linkelem.find('a').get('href')
        meta["text"] = post.find('span', {'class','body'}).get_text().strip()
        qhash = hashlib.sha256(meta["url"].encode())
        hashsum = str(qhash.hexdigest().upper())
        filename = "dl-link_" + hashsum + ".sh"
        basepath = self.bup_dir + self.sep
        if self.has_valid_timestamp(meta):
            basepath = basepath + meta['time'][2] + self.sep + meta['time'][0] + self.sep
        path = basepath + filename
        if os.path.isfile(path) == True:
            print("\t\t\tSkip: " + filename + ": File exists")
        else:
            self.assertdir(basepath)
            print("\t\t\t-> " + path)
            filecontent="#! /bin/bash\nwget -c " + meta['url'] + "\n"
            with open(path, "w") as df:
                df.write(filecontent)
            st = os.stat(path)
            os.chmod(path, st.st_mode | stat.S_IEXEC)
            self.write_raw(post)

    def process_video(self, post):
        print("\t\tVideo:")
        meta = {}
        meta['time'] = self.get_timstemp(post)
        meta['embeded'] = post.find("div", {'class':'embed'}).prettify()
        bodyelem = post.find("div", {'class':'body'})
        if bodyelem:
            meta['body'] = bodyelem.get_text().strip()
        else:
            meta['body'] = "";
        data = meta['embeded'] + meta['body']
        qhash = hashlib.sha256(data.encode())
        hashsum = str(qhash.hexdigest().upper())
        filename = "video_" + hashsum + ".json"
        basepath = self.bup_dir + self.sep
        if self.has_valid_timestamp(meta):
            basepath = basepath + meta['time'][2] + self.sep + meta['time'][0] + self.sep
        path = basepath + filename
        if os.path.isfile(path) == True:
            print("\t\t\tSkip: " + filename + ": File exists")
        else:
            self.assertdir(basepath)
            print("\t\t\t-> " + path)
            self.write_raw(post)

    def process_file(self, post):
        print("\t\tFile:")
        meta = {}
        meta['time'] = self.get_timstemp(post)
        linkelem = post.find("h3")
        if linkelem:
            meta["link_title"] = linkelem.get_text().strip()
            meta["soup_url"] = linkelem.find('a').get('href')
        meta["text"] = post.find('div', {'class','body'}).get_text().strip()
        if 'soup_url' in meta:
            filename = meta["soup_url"].split("/")[-1]
        else:
            filename = "file_unkown"
        basepath = self.bup_dir + self.sep
        if self.has_valid_timestamp(meta):
            basepath = basepath + meta['time'][2] + self.sep + meta['time'][0] + self.sep
        path = basepath + filename
        if os.path.isfile(path) == True:
            print("\t\t\tSkip: " + filename + ": File exists")
        else:
            if 'soup_url' in meta:
                print("\t\t\tsoup_ulr: " + meta['soup_url'] + " -> " + path)
                self.assertdir(basepath)
                r = requests.get(meta['soup_url'], allow_redirects=True)
                with open(path, "wb") as df:
                    df.write(r.content)
            self.assertdir(basepath + "meta" + self.sep )
            jsonname = filename.split(".")[0]
            self.write_meta(meta, jsonname)
            self.write_raw(post)

    def process_review(self, post):
        print("\t\tReview:")
        meta = {}
        meta['time'] = self.get_timstemp(post)
        for link in post.find_all('div', {"class":"imagecontainer"}):
            lightbox = link.find("a", {"class": "lightbox"})
            if lightbox:
                meta['soup_url'] = lightbox.get('href')
            else:
                meta['soup_url'] = link.find("img").get('src')
        descelem = post.find("div", {'class','description'})
        if descelem:
            meta['description'] = descelem.get_text().strip()
        meta['rating'] = post.find("abbr", {"class", "rating"}).get("title")
        h3elem = post.find("a", {"class":"url"})
        meta['url'] = h3elem.get("href")
        meta['title'] = h3elem.get_text()
        if 'soup_url' in meta:
            basepath = self.bup_dir + self.sep
            if self.has_valid_timestamp(meta):
                basepath = basepath + meta['time'][2] + self.sep + meta['time'][0] + self.sep
            filename = "review_" + self.get_asset_name(meta['soup_url'])
            path = basepath + filename + "." + meta['soup_url'].split(".")[-1]
            if os.path.isfile(path) == True:
                print("\t\t\tSkip " + meta['soup_url'] + ": File exists")
            else:
                print("\t\t\tsoup_ulr: " + meta['soup_url'] + " -> " + path)
                self.assertdir(basepath)
                r = requests.get(meta['soup_url'], allow_redirects=True)
                with open(path, "wb") as tf:
                    tf.write(r.content)
                self.write_raw(post)

    def process_event(self, post):
        print("\t\tEvent:")
        meta = {}
        meta['time'] = self.get_timstemp(post)
        for link in post.find_all('div', {"class":"imagecontainer"}):
            lightbox = link.find("a", {"class": "lightbox"})
            if lightbox:
                meta['soup_url'] = lightbox.get('href')
            else:
                meta['soup_url'] = link.find("img").get('src')
        h3elem = post.find("a", {"class":"url"})
        meta['url'] = h3elem.get("href")
        meta['title'] = h3elem.get_text()
        meta['dtstart'] = post.find("abbr", {'class':'dtstart'}).get("title")
        dtelem = post.find("abbr", {'class':'dtend'})
        if dtelem:
            meta['dtend'] = dtelem.get("title")
        meta['location'] = post.find("span", {'class':'location'}).get_text().strip()
        meta['ical_url'] = post.find("div", {'class': 'info'}).find('a').get('href')
        descelem = post.find("div", {'class','description'})
        if descelem:
            meta['description'] = descelem.get_text().strip()
        if 'soup_url' in meta:
            basepath = self.bup_dir + self.sep
            if self.has_valid_timestamp(meta):
                basepath = basepath + meta['time'][2] + self.sep + meta['time'][0] + self.sep
            filename = "event_" + self.get_asset_name(meta['soup_url'])
            path = basepath + filename + "." + meta['soup_url'].split(".")[-1]
            if os.path.isfile(path) == True:
                print("\t\t\tSkip " + meta['soup_url'] + ": File exists")
            else:
                print("\t\t\tsoup_ulr: " + meta['soup_url'] + " -> " + path)
                self.assertdir(basepath)
                r = requests.get(meta['soup_url'], allow_redirects=True)
                with open(path, "wb") as tf:
                    tf.write(r.content)
                i = requests.get(meta['ical_url'], allow_redirects=True)
                with open(basepath + filename + ".ical", "wb") as icf:
                    icf.write(i.content)
                self.write_raw(post)

    def process_regular(self, post):
        print("\t\tRegular:")
        meta = {}
        meta['time'] = self.get_timstemp(post)
        h3elem = post.find("h3")
        content = {}
        if h3elem:
            content['title'] = str(h3elem)
        body = post.find("div", {'class':'body'})
        content['body'] = str(body)
        filename = "regular_" + post['id'] + ".json"
        basepath = self.bup_dir + self.sep
        if self.has_valid_timestamp(meta):
            basepath = basepath + meta['time'][2] + self.sep + meta['time'][0] + self.sep

        path = basepath + filename
        if os.path.isfile(path) == True:
            print("\t\t\tSkip: " + filename + ": File exists")
        else:
            self.assertdir(basepath)
            print("\t\t\t-> " + path)
            with open(path, "w") as rf:
                json.dump(content, rf)
            self.write_raw(post)

    def process_unkown(self, post, post_type):
        print("\t\tUnsuported tpye:")
        print("\t\t\tType: " + post_type)
        meta = {}
        meta['type'] = post_type
        meta['time'] = self.get_timstemp(post)
        content = post.prettify()
        qhash = hashlib.sha256(content.encode())
        hashsum = str(qhash.hexdigest().upper())
        meta['content'] = content
        filename = "unknown_" + hashsum + ".txt"
        basepath = self.bup_dir + self.sep
        if self.has_valid_timestamp(meta):
            basepath = basepath + meta['time'][2] + self.sep + meta['time'][0] + self.sep
        path = basepath + filename
        if os.path.isfile(path) == True:
            print("\t\t\tSkip: " + filename + ": File exists")
        else:
            print("\t\t\t-> " + path)
            self.write_raw(post)

    def get_meta(self, post):
        meta = {}
        meta['type'] = post.get('class')[1]
        meta['time'] = self.get_timstemp(post)
        meta['id'] = post['id']
        permalink = post.select('.meta .icon.type a')[0]
        author = post.select('.meta div.author .user_container')[0]
        meta['permalink'] = permalink['href']
        author_id = [id for id in author.get('class') if id != 'user_container'][0]
        meta['author_id'] = author_id
        meta['author_url'] = author.select('a.url')[0]['href']
        return meta


    def process_posts(self, cur_page):
        posts = cur_page.find_all('div', {"class": "post"})
        for post in posts:
            post_type = post.get('class')[1]
            meta = self.get_meta(post)
            self.write_meta(meta)
            if post_type == "post_image":
                self.process_image(post)
            elif post_type == "post_quote":
                self.process_quote(post)
            elif post_type == "post_video":
                self.process_video(post)
            elif post_type == "post_link":
                self.process_link(post)
            elif post_type == "post_file":
                self.process_file(post)
            elif post_type == "post_review":
                self.process_review(post)
            elif post_type == "post_event":
                self.process_event(post)
            elif post_type == "post_regular":
                self.process_regular(post)
            else:
                self.process_unkown(post, post_type)

    def backup(self, cont_url = ""):
        dlurl = self.rooturl + cont_url
        while True:
            print("Get: " + dlurl)
            dl = requests.get(dlurl)
            page = BeautifulSoup(dl.content, 'html.parser')
            print("Looking for next Page")
            dlurl = self.rooturl + self.find_next_page(page)
            print("Process Posts")
            self.process_posts(page)
            if self.dlnextfound == False:
                print("no next found.")
                break

def main(soups, bup_dir, cont_from):
    for site in soups:
        soup = Soup(site, bup_dir)
        soup.backup(cont_from)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Soup.io backup')
    parser.add_argument('soups', nargs=1, type=str, default=None, help="Name your soup")
    parser.add_argument('-d','--dir', default=os.getcwd(), help="Directory for Backup (default: Working dir)")
    parser.add_argument('-c', '--continue_from', default="", help='Continue from given suburl (Example: /since/696270106?mode=own)')
    args = parser.parse_args()
    main(args.soups, args.dir, args.continue_from)
