from bs4 import BeautifulSoup, SoupStrainer
import urllib2
from urlparse import urljoin

def extractPdf(url, levels):
    outurls = [] #pdfs found within n levels
    thiscycle = [url] #List of urls to look through on current loop iteration
    linkstrainer = SoupStrainer("a")
    hdr = {'User-Agent': 'Mozilla/5.0'}
    for i in range (0, levels):
        nextcycle = [] #Urls to look at in next loop iteration
        for currurl in thiscycle:
            print currurl
            request = urllib2.Request(currurl, headers=hdr)
            try:
                page = urllib2.urlopen(request)
            except:
                print 'fuck'
                continue
            soup = BeautifulSoup(page, parse_only=linkstrainer)
            for link in soup.find_all('a'):
                linkurl = link.get('href')
                if not linkurl:
                    continue
                elif linkurl[-4:] == '.pdf':
                    print linkurl
                    if linkurl[:4] == 'http':
                        outurls.append(linkurl)
                    else:
                        finalurl = urljoin(currurl, linkurl)
                        outurls.append(finalurl)
                elif i != levels-1:
                    if linkurl[:4] == 'http':
                        nextcycle.append(linkurl)
                    else:
                        finalurl = urljoin(currurl, linkurl)
                        nextcycle.append(finalurl)
        if not nextcycle:
            return outurls
        thiscycle = nextcycle[:]
    return outurls
