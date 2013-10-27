import lxml.html
from urlparse import urlparse, urljoin, urldefrag
from urllib2 import URLError, urlopen
import tinycss


class Crawler:
    def __init__(self, urls, limit=0):
        self.urls = urls
        self.limit = limit
        self.styles = dict()
        self.parser = tinycss.CSS21Parser()

    def run(self):
        for url in self.urls:
            try:
                doc = urlopen(url)
            except URLError:
                continue

            page = Page(url, doc.read())
            css_links = page.parse_css_links()
            for css_link in css_links:
                if css_link not in self.styles:
                    try:
                        res = urlopen(css_link)
                    except URLError:
                        continue

                    css = self.parser.parse_stylesheet_file(res)
                    rules_set = set()

                    def del_pseudo(tokens):
                        def iter_del_pseudo(ts, i):
                            try:
                                if ts[i].type == ':':
                                    del ts[i]
                                    if ts[i].type == ':':
                                        iter_del_pseudo(ts, i)
                                    else:
                                        del ts[i]
                                        iter_del_pseudo(ts, i)
                            except IndexError:
                                pass
                            return ts

                        for k, token in enumerate(tokens):
                            iter_del_pseudo(tokens, k)
                        return tokens

                    def parse_rules(rules_list):
                        for rule in rules_list:
                            if rule.at_keyword is None:
                                if len(rule.declarations):
                                    rules_set.add((rule.selector.as_css(), del_pseudo(rule.selector).as_css()))
                            elif rule.at_keyword == '@media':
                                parse_rules(rule.rules)
                            elif rule.at_keyword == '@import':
                                css_links.append(rule.uri)

                    parse_rules(css.rules)
                    if rules_set:
                        self.styles[css_link] = list(rules_set)

            page.set_css_links(css_links)
            self.delete_used_styles(page)

            unique_page_links = list(set(page.page_links).difference(set(self.urls)))
            if self.limit > 0:
                extend_len = self.limit - len(self.urls) - len(unique_page_links)
                self.urls.extend(unique_page_links[:extend_len])
            else:
                self.urls.extend(unique_page_links)

    def delete_used_styles(self, page):
        for css_link in page.css_links:
            if css_link in self.styles:
                for key, selector in enumerate(self.styles[css_link]):
                    if page.dom.cssselect(selector[1]):
                        self.styles[css_link][key] = False
                self.styles[css_link] = filter(None, self.styles[css_link])


class Page:
    def __init__(self, url, doc):
        self.url = url
        self.netloc = urlparse(url).netloc
        self.dom = lxml.html.document_fromstring(doc)
        self.page_links = self.parse_page_links()
        self.css_links = None

    def set_css_links(self, links):
        self.css_links = links

    def parse_page_links(self):
        return [urljoin(self.url, urldefrag(l)[0]) for l in self.dom.xpath('//a/@href')
                if urlparse(l).netloc in (self.netloc, '')
                and urlparse(l).scheme in ('http', 'https', '')]

    def parse_css_links(self):
        return [urljoin(self.url, l) for l in self.dom.xpath("/html/head/link[@rel='stylesheet']/@href")
                if urlparse(l).netloc in (self.netloc, '')]