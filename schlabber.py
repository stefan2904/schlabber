#!/usr/bin/env python3
import os
import argparse
import requests
import json
import pprint
from bs4 import BeautifulSoup

class Soup:
    def assertdir(self,dirname):
        if not os.path.isdir(dirname):
            os.makedirs(dirname)

    def __init__(self, soup, bup_dir):
        self.rooturl = "http://"+soup+".soup.io"
        self.bup_dir = os.path.abspath(bup_dir)
        self.assertdir(self.bup_dir)
        self.dlnextfound = False
        print("Backup: " + self.rooturl)
        print("into: " + self.bup_dir)
    
    def find_next_page(self, cur_page):
        for script in cur_page.find_all('script'):
            if "SOUP.Endless.next_url" in script.get_text():
                print("\t...found")
                self.dlnextfound = True
                return script.get_text().split('\'')[-2].strip()
        self.dlnextfound = False
        return ""
    
    def process_image(self, post):
        pass
    def process_quote(self, post):
        pass
    def process_link(self, post):
        pass
    def process_video(self, post):
        pass
    def process_file(self, post):
        pass
    def process_review(self, post):
        pass
    def process_event(self, post):
        pass
    def process_regular(self, post):
        pass
    def process_unkown(self, post):
        pass

    def process_posts(self, cur_page):
        posts = cur_page.find_all('div', {"class": "post"})
        for post in posts:
            post_type = post.get('class')[1] 
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
                print("Unsuported tpye: " + post_type)
        
    def backup(self):
        dlurl = self.rooturl
        while True:
            print("Get: " + dlurl)
            dl = requests.get(dlurl)
            page = BeautifulSoup(dl.content, 'html.parser')
            print("Looking for next Page")
            dlurl = self.rooturl + self.find_next_page(page)
            print("Process Posts")
            self.process_posts(page)
            break; # debug stop REMOVE!!!
            if self.dlnextfound == False:
                break

def main(soups, bup_dir):
    for site in soups:
        soup = Soup(site, bup_dir)
        soup.backup()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Soup.io backup')
    parser.add_argument('soups', nargs=1, type=str, default=None, help="Name your soup")
    parser.add_argument('-d','--dir', default=os.getcwd(), help="Directory for Backup (default: Working dir)")
    #parser.add_argument('-f','--foo', action='store_true', default=False, help='sample for option (used later)')
    args = parser.parse_args()
    main(args.soups, args.dir)