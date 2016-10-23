from datetime import datetime
import scrapy
import re

# scrapy runspider --nolog fetch.py

class QuotesSpider(scrapy.Spider):
    name = "quotes"
    start_urls = [
    ]

    for ep in range(250, 253):
        start_urls.append('https://twit.tv/shows/floss-weekly/episodes/' + str(ep))

    def parse(self, response):
        data = {
            'keywords' : [],
            'guests'   : {},
            'hosts'    : {},
        }
        #print(response)
        data['permalink'] = response.url
        full_title = response.css('title::text').extract_first()
        print(full_title)
        published  = response.css('p.air-date::text').extract_first()
        print(published) # Apr 25th 2012
        parsable = re.sub(r'\A(\w+)\s+(\d+)\w+\s+(\d+)\Z', r'\1 \2 \3', published)
        print(parsable)
        dt = datetime.strptime(parsable, '%b %d %Y')  # Apr 25 2012
        print(dt)
        data['date'] = dt.strftime('%Y-%m-%d')
        m = re.search(r'FLOSS Weekly (\d+)\s+(.*?)\s+\| TWiT', full_title)
        #m = re.search(r'FLOSS Weekly (\d+)\s+(.*)', full_title)
        if m:
            data['ep'] = m.group(1)
            data['title'] = m.group(2)
        print(data)

# vim: expandtab
