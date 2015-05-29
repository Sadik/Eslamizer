__author__ = 'sadik'
import urllib3
import re
from urllib3 import PoolManager
from bs4.element import Comment
from bs4 import BeautifulSoup

class EslamEntry(object):

    def __init__(self, title):
        self.title = title.lower()
        self.letter = self.title[0]
        self.url = "http://www.eslam.de/begriffe/"+self.letter+"/"+self.title+".htm"
        print ("url: ", self.url)
        self.text = ""

    def __repr__(self):
        return "An eslam entry with name \"" + self.title + "\" and a pain text"

    def getText(self):
        http = urllib3.PoolManager()
        r = http.request("GET", self.url)
        return r.data.decode('ISO-8859-1')

    def soupIt(self):
        soup = BeautifulSoup(self.getText(), "lxml")
        self.title = soup.title.string

        for p in soup(["head", "meta"]):
            p.extract()

        for element in soup(text=lambda text: isinstance(text, Comment)):
            element.extract()

        return soup

        #not optimal
        #text = soup.get_text()
        #lines = (line.strip() for line in text.splitlines())
        #chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        #text = '\n'.join(chunk for chunk in chunks if chunk)
        #return text

if __name__ == '__main__':
    e = EslamEntry("Allah")
    print(e.soupIt())