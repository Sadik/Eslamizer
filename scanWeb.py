__author__ = 'sadik'
import re
import string
import urllib3
from urllib3 import PoolManager
from urllib.parse import urljoin, urlparse
from bs4.element import Comment
from bs4 import BeautifulSoup


def same_domain(url1, url2):
    return get_domain_name(url1) == get_domain_name(url2)

def get_domain_name(url):
    parsed_uri = urlparse(url)
    if parsed_uri.scheme and parsed_uri.netloc:
        return '{uri.scheme}://{uri.netloc}/'.format(uri=parsed_uri)

    return get_domain_name("http://" + url)


class Tree(object):

    http = urllib3.PoolManager()
    collected_urls = [] #[string]

    def __init__(self, root):
        """

        :param root: RoutedLink
        """
        self.root = root

    def __repr__(self):
        return self.root.get_tree()

    def absolute(self, url):
        return urljoin(self.root.url, url)

    def build_tree(self, root=None):
        if root is None:
            root = self.root
        try:
            r = self.http.request("GET", root.url)
        except UnicodeEncodeError:
            print ("UnicodeEncodeError in url: " , root.url)
            return []
        except:
            print ("Unexpected Error with url: " , root.url)
            return []

        soup = BeautifulSoup(r.data.decode('ISO-8859-1'), "lxml")
        cur_level_links =  [self.absolute(link['href']) for link in soup.findAll('a') if link.has_attr('href')
                            and same_domain(self.root.url, urljoin(self.root.url, link['href']))
                            and self.absolute(link['href']) not in self.collected_urls]

        self.collected_urls += cur_level_links

        children = []
        for link in soup.findAll('a'):
            if link.has_attr('href'):
                absolute_link = self.absolute(link['href'])
                if same_domain(self.root.url,absolute_link):
                    if absolute_link not in self.collected_urls:
                        cur_level_links.append(absolute_link)
                        rl = RoutedLink(absolute_link, root)
                        rl.children = self.build_tree(rl)
                        children.append(rl)

        for l in cur_level_links:
            rl = RoutedLink(l, root)
            rl.children = self.build_tree(rl)
            children.append(rl)

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
        if parent is not None:
            self.parent = parent

    def __repr__(self):
        return "RoutedLink: \"" + self.url + "\""

    def insert_child(self, child_node):
        self.children.append(child_node)

    def get_tree(self):
        if (len(self.children) == 0):
            return []
        for child in self.children:
            return [child] + child.get_tree()

    def depth(self):
        if hasattr(self, 'parent'):
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
    tree = Tree(r0)
    result = tree.build_tree()
    #for r in result:
    #    print (r)
    #    print ("anzahl children: ", len(r.children))
    #    for child in r.children:
    #        print ("    ", child)