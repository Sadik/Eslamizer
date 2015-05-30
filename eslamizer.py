__author__ = 'sadik'
import urllib3
import re
import string
from urllib3 import PoolManager
from urllib.parse import urljoin
from bs4.element import Comment
from bs4 import BeautifulSoup

class Eslamizer(object):

    def __init__(self):
        self.entry_list = self.get_all_entries()

    def get_all_entries(self):
        alphabet = list(string.ascii_lowercase)
        basic_alphabet_url = "http://www.eslam.de/alphabet/"

        letter_entries_url = []
        for letter in alphabet:
            url = basic_alphabet_url + letter + ".htm"
            letter_entries_url.append(url)

        return letter_entries_url

    def get_letters_entries(self, url):
        http = urllib3.PoolManager()
        r = http.request("GET", url)
        soup = BeautifulSoup(r.data.decode('ISO-8859-1'), "lxml")

        eslamEntries = []
        for l in soup.findAll('a'):
            if "begriffe" in urljoin(url, l['href']) or "manuskripte" in urljoin(url, l['href']):
                title = re.sub(r'\r\n *', '', l.text)
                title = re.sub(r'^\n', '', title)
                eslamEntries.append(EslamEntry(title, urljoin(url, l['href'])))

        return eslamEntries

class EslamEntry(object):

    def __init__(self, title, url=None):
        self.title = title.lower()
        self.letter = self.title[0]
        if url is None:
            self.url = "http://www.eslam.de/begriffe/"+self.letter+"/"+self.title+".htm"
        else:
            self.url = url
        self.images = []

        self.text = ""

    def __repr__(self):
        return "EslamEntry with name \"" + self.title + "\""

    def getText(self):
        http = urllib3.PoolManager()
        r = http.request("GET", self.url)
        return r.data.decode('ISO-8859-1')

    def soupIt(self):
        soup = BeautifulSoup(self.getText(), "lxml")
        self.title = soup.title.string

        #remove unused header parts
        #in comments because of firefox
        #for p in soup(["meta"]):
        #    p.extract()

        #remove comments
        for element in soup(text=lambda text: isinstance(text, Comment)):
            element.extract()

        #remove some images
        unused_images = soup.find_all('img', {'alt':'bullet'}) \
                        + soup.find_all('img', {'src':'../../images/ilmulislam.gif'}) \
                        + soup.find_all('img', {'src':'../../images/enzykopf.gif'})
        for i in soup.find_all('img'):
            if i in unused_images:
                i.extract()

        # remove all links, but keep text
        # don't keep text for navigation links that don't lead to "begriffe" or "manuskripte"
        for l in soup.findAll('a'):
            if "begriffe" in urljoin(self.url, l['href']) or "manuskripte" in urljoin(self.url, l['href']):
                l.replaceWith(l.text)
            else:
                l.extract()

        #remove top blocks
        topBlocks = soup.findAll('td', {'width': '50%'})
        for block in topBlocks:
            if len(block.findChildren('img')):
                self.images += block.findChildren('img')
            block.extract()

        #remove trash tags and empty tags
        for tag in soup.findAll():

            if tag.name == "meta":
                continue
            if tag.name in ("td", "tr", "table", "center", "div", "font", "strong", "b"):
                tag.unwrap()
            if len(tag.text) == 0 or tag.text == '\n' or re.match(r'^\s*$', tag.text) or tag.is_empty_element or tag.isSelfClosing:
                tag.extract()

        for l in soup.find_all(text=re.compile('^\n')):
            l.extract()

        for l in soup.find_all(text=re.compile('\r\n')):
            l.replaceWith(" ")

        #for l in soup.find_all(text=re.compile('\r\n')):
        #    l.extract()

        #append immages
        for i in self.images:
            soup.body.insert(0, i)

        return soup.prettify()

        #text = BeautifulSoup.get_text(soup)
        #text = re.sub(r'\r\n', ' ', soup.text)
        #text = re.sub(r'\xa0', '', text)
        #text = re.sub(r'\n+', '\n', text)
        #text = re.sub(r' +', ' ', text)
        #return text

if __name__ == '__main__':
    #e = EslamEntry("Allah")
    #print(e.soupIt())
    e = Eslamizer()
    e.get_all_entries()