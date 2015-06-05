__author__ = 'sadik'
import re
import string
import os
import urllib3
from urllib3 import PoolManager
import urllib
from urllib.parse import urljoin, urlparse
from urllib.error import URLError
import requests

from bs4.element import Comment
from bs4 import BeautifulSoup


def same_domain(url1, url2):
    return get_domain_name(url1) == get_domain_name(url2)


def get_domain_name(url):
    """return domain of url
    needs to be called with absolute path
    :param url: string
    :return: string
    """
    parsed_uri = urlparse(url)
    if parsed_uri.scheme and parsed_uri.netloc:
        return '{uri.scheme}://{uri.netloc}/'.format(uri=parsed_uri)

    if (not parsed_uri.scheme) and parsed_uri.netloc:
        return 'http://{uri.netloc}/'.format(uri=parsed_uri)

def clear_url(url):
    """
    removes unnecessary parts of url, like query or fragment
    example clear_url("www.offenkundiges.de/ueber-uns/#top")
      results in: "http://www.offenkundiges.de/ueber-uns/"
    :param url: string
    :return: string
    """
    parsed_uri = urlparse(url)
    if parsed_uri.scheme and parsed_uri.netloc:
        return '{uri.scheme}://{uri.netloc}{uri.path}'.format(uri=parsed_uri)
    elif parsed_uri.netloc and parsed_uri.path:
        return 'http://{uri.netloc}{uri.path}'.format(uri=parsed_uri)
    else:
        return 'http://{uri.path}'.format(uri=parsed_uri)

def url_exists(url):
    """
    checks for 404 error
    only works with http:// or https://
    :param url: string
    :return: bool
    """
    try:
        return requests.get(url).status_code != 404
    except:
        return False


class Tree(object):

    http = urllib3.PoolManager()
    just_fun = []
    collected_urls = [] #[string]
    collected_rl = {}
    ignore_url = "http://www.eslam.de/arab/"

    def __init__(self, root):
        """

        :param root: RoutedLink
        """
        self.root = root

    def sort_tree(self):
        print("not implemented")

    def print_tree(self, root):
        """

        :param root: RoutedLink
        """
        print(root.depth() * " ", root.url)
        for c in root.children:
            self.print_tree(c)

    def absolute(self, parent_url, url):
        if parent_url:
            return urljoin(parent_url, url)
        else:
            return urljoin(self.root.url, url)

    def start(self):
        print("Start building up tree")
        root_node = self.create_tree(self.root.url)
        print("Tree built up: ", root_node)
        return root_node

    def create_tree(self, url=None, parent_node=None):

        """

        :param url: string
        :param parent_node: RoutedLink
        :return: RoutedLink
        """
        if url is None:
            print ("[URL] creating tree with default root url")
            url = self.root.url

        try:
            r = requests.get(url)
            r.encoding = 'ISO-8859-1'
        except UnicodeEncodeError:
            print ("UnicodeEncodeError in url: " , url)
            #if type(self) == RoutedLink and self.parent is not None:
            #    print ("     Link steht auf: ", self.parent.url, "\n")
            return [] #TODO: check if return of empty list is correct
        except KeyboardInterrupt:
            print ("user interrupted")
            exit(-1)
        except:
            print ("Unexpected Error with url: " , url)
            return [] #TODO: check if return of empty list is correct

        if r.status_code == 404:
            print ("[URL] 404 Error on ", url)
            print ("     comming from: ", parent_node.url)
            return [] #TODO: check if return of empty list is correct

        rl = RoutedLink(url, parent_node)
        if parent_node is not None:
            parent_node.insert_child(rl)

        soup = BeautifulSoup(r.text, "lxml")

        for link in soup.findAll('a'):
            if link.has_attr('href'):
                clear_link = clear_url(self.absolute(rl.url, link['href']))
                fileName, fileExt = os.path.splitext(clear_link)
                if fileExt.lower() in [".jpg", ".png", ".gif"]:
                    continue
                if same_domain(self.root.url, clear_link):
                    if clear_link != url:
                        if clear_link not in self.collected_urls:
                            self.collected_urls.append(clear_link)
                            self.create_tree(clear_link, rl)
                            self.just_fun.append(rl)
                            self.collected_rl[rl.url] = rl.depth()

        #print (rl.url, " with parent: ", rl.parent, " and depth: ", rl.depth())
        return rl

    def build_tree(self, root_url=None, parent=None):
        rl = RoutedLink(root_url, parent)
        print ("depth:",rl.depth(), rl.depth()*"  ", rl.url)

        if root_url is None:
            root_url = self.root.url
        try:
            r = self.http.request("GET", rl.url)
        except UnicodeEncodeError:
            #print ("UnicodeEncodeError in url: " , root.url)
            #if type(self) == RoutedLink and self.parent is not None:
            #    print ("     Link steht auf: ", self.parent.url, "\n")
            return []
        except KeyboardInterrupt:
            #print ("user interrupted")
            exit(-1)
        except:
            #print ("Unexpected Error with url: " , root.url)
            return []

        if rl.url not in self.collected_urls:
            self.collected_urls.append(rl.url)

        soup = BeautifulSoup(r.data.decode('ISO-8859-1'), "lxml")

        children = []
        for link in soup.findAll('a'):
            if link.has_attr('href'):
                if same_domain(self.root.url, self.absolute(self.root.url, link['href'])):
                    clear_link = clear_url(self.absolute(rl.url, link['href']))
                    if clear_link not in self.collected_urls:
                        self.collected_urls.append(clear_link)

                        self.build_tree(clear_link, rl)

                        children.append(rl)
                        rl_children = self.build_tree(rl)
                        self.just_fun.append(rl)
                        self.collected_rl[rl.url] = rl.depth()

        return children


class RoutedLink(object):
    http = urllib3.PoolManager()

    def __init__(self, url, parent=None, children=[]):
        """

        :param url: string
        :param level: int
        :param parent: RoutedLink
        :param children: [RoutedLink]
        """
        #if url.endswith('/'): # problem with urljoin
        self.url = url

        self.children = children

        self.parent = parent

    def __repr__(self):
        return "RoutedLink: \"" + self.url + "\""

    def eslam_site_found(self):
        try:
            r = self.http.request("GET", self.url)
        except UnicodeEncodeError:
           # print ("UnicodeEncodeError in url: " , self.url)
           # print ("     Link steht auf: ", self.parent.url, "\n")
            return False
        soup = BeautifulSoup(r.data.decode('ISO-8859-1'), "lxml")
        txt = soup.get_text()
        wrong_url_txt = '\n\n\n\n\n\nEnzyklopädie des Islam\n\n\n\n\n\n\n\n\n\n\xa0\n\n\n\n\n\xa0\n\n\n\xa0\n\n\n\n\n\n\n\n\r\n            Hinweis\n\n\n\n\n\n\n\nStartseite\n\n\nSuche\n\n\nImpressum\n\n\n\n\n\n\n\n\n\n\n\n\n\nSehr geehrter Besucher der \r\n        Enzyklopädie des Islam,\ndie von Ihnen gewählte Seite \r\n        existiert leider nicht (mehr) \r\n        auf unserem Server.\nBitte informieren sie uns, woher der Link stammt, damit wir \r\n        die Seite ggf. korrigieren können. Über eine\r\n        Information per e-Mail an\r\n        \r\n        info@eslam.de\xa0\xa0\r\n        bezüglich des defekten Links wären wir sehr dankbar.\nZu unserer Homepage gelangen Sie unter\r\n        www.eslam.de \nIhre \r\n        Enzyklopädie des Islam\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n© 2006-2009 - \r\nm-haditec GmbH & \r\nCo KG - \ninfo@eslam.de\n\n\n\n\n\n\n\n\n\n\n\n'
        if txt == wrong_url_txt:
            return False
        return True

    def insert_children(self, children):
        self.children += children

    def insert_child(self, child_node):
        self.children.append(child_node)

    def get_tree(self):
        if (len(self.children) == 0):
            return []
        for child in self.children:
            return [child] + child.get_tree()

    def depth(self):
        if self.parent is not None:
            return  1 + self.parent.depth()
        else:
            return 0

    def get_route(self):
        return list(reversed(self.get_route_helper(self)))

    def get_route_helper(self, parent=None):
        if hasattr(parent, 'parent'):
            return [parent] + self.get_route_helper(parent.parent)
        else:
            return [parent]

    def get_all_links(self, url):
        """
        returns a list of links that can be reached directly
        (i.e. with one click) from url
        Only collects links on hte same domain

        example: get_all_likns("www.eslam.de") will scan
        "www.eslam.de" for links that point at something like
        "www.eslam.de/a/b/c.html". External links are being ignored.
        :param url: links on this url will be collected
        :return: list of urls (strings)
        """
        r = self.http.request("GET", url)
        soup = BeautifulSoup(r.data.decode('ISO-8859-1'), "lxml")
        found_links = [link for link in soup.findAll('a') if link.has_attr('href')]
        for link in found_links:
            link_href = urljoin(self.start, link['href'])
            if same_domain(self.start, link_href):
                if link_href not in self.all_links:
                    self.all_links.append(link_href)

        return self.all_links

if __name__ == '__main__':
    r0 = RoutedLink("http://www.eslam.de/")
    print ("depth: ", r0.depth())
    r1 = RoutedLink("www.eslam.de/impressum.htm",  r0)
    print ("depth: ", r1.depth())
    r2 = RoutedLink("www.eslam.de/alphabet/a.htm",  r0)
    print ("depth: ", r2.depth())
    r3 = RoutedLink("www.eslam.de/begriffe/a/allah.htm", r2)
    print ("depth: ", r3.depth())
    print ("##############################")

    r = RoutedLink("http://www.offenkundiges.de")
    tree = Tree(r)
    tree.start()

    #for r in result:
    #    print (r)
    #    print ("anzahl children: ", len(r.children))
    #    for child in r.children:
    #        print ("    ", child)