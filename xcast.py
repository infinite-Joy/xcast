import argparse
from datetime import datetime
import glob
import json
import os
import sys
import re
import csv
from jinja2 import Environment, PackageLoader

if sys.version_info.major < 3:
    exit("This code requires Python 3.\nThis is {}".format(sys.version))

def main():

    parser = argparse.ArgumentParser()
    parser.add_argument('--list', help = 'List sources', action='store_true')
    parser.add_argument('--html', help = 'Generate HTML', action='store_true')
    parser.add_argument('--check', help = 'Check the RSS feed', action='store_true')
    parser.add_argument('--source', help = 'Check the RSS feed of given source')
    args = parser.parse_args()


    with open('data/sources.json') as fh:
        sources = json.load(fh)
    
    if args.list:
        for s in sources:
            print('{:20} {}'.format(s.get('name', ''), s.get('title', '')))
    elif args.source:
        source = list(filter(lambda x: x['name'] == args.source, sources))
        if not source:
            exit("'{}' is not one of the sources".format(args.source))
        #print(source[0])
        
        import feedparser
        d = feedparser.parse(source[0]['feed'])
        for e in d.entries:
            if args.source == 'floss-weekly':
                data = {}
                full_title = e['title']
                published = e['published']
                date = datetime.strptime(published, '%a, %d %b %Y %H:%M:%S %z')  # Tue, 18 Oct 2016 10:33:51 -0700
                #comments  http://twit.tv/floss/408
                #print(e['comments'])
                #m = re.search(r'\d+$', e['comments'])
                m = re.search(r'FLOSS Weekly (\d+):\s*(.*)', full_title)
                ep = None
                if m:
                    data['ep'] = m.group(1)
                    data['title'] = m.group(2)
                    data['permalink'] = 'https://twit.tv/shows/floss-weekly/episodes/' + data['ep']
                    data['date'] = date.strftime('%Y-%m-%d')
                    data['guests'] = {}
                    data['hosts'] = {}
            else:
                exit("Cannot handle this feed")
            print(data)
            print('---')
            #exit()
 
        #for k in d.entries[0].keys():
        #    print("{}  {}\n".format(k, d.entries[0][k]))

    elif args.check:
        import feedparser
        for s in sources:
            if 'feed' in s:
                print(s['feed'])
                d = feedparser.parse(s['feed'])
                print(d['feed']['title'])
                print(d.entries[0].title)
                print(d.entries[0].link)
                print(d.entries[0])
                print()
                exit()

            #else:
            #    print('No feed for {}'.format(s['name']))
    elif args.html:
        episodes = read_episodes(sources)
        people = read_people()
        tags = read_tags()

        for e in episodes:
            #print(e)
            #exit()
            if 'tags' in e:
                for tag in e['tags']:
                    path = tag2path(tag)
                    if path not in tags:
                        # TODO report tag missing from the tags.csv file
                        tags[path] = {}
                        tags[path]['tag'] = tag
                        tags[path]['episodes'] = []
                    tags[path]['episodes'].append(e)

            if 'guests' in e:
                for g in e['guests'].keys():
                    if g not in people:
                        exit("ERROR: '{}' is not in the list of people".format(g))
                    people[g]['episodes'].append(e)
            if 'hosts' in e:
                for h in e['hosts'].keys():
                    if h not in people:
                        exit("ERROR: '{}' is not in the list of people".format(h))
                    people[h]['hosting'].append(e)
        generate_pages(sources, people, tags, episodes)
    else:
        parser.print_help()

def generate_pages(sources, people, tags, episodes):
    env = Environment(loader=PackageLoader('xcast', 'templates'))

    search = {}

    for e in episodes:
        search[ e['title'] + ' (ext)' ] = e['permalink']

    person_template = env.get_template('person.html')
    if not os.path.exists('html/p/'):
        os.mkdir('html/p/')
    for p in people.keys():
        people[p]['episodes'].sort(key=lambda x : x['date'], reverse=True)
        people[p]['hosting'].sort(key=lambda x : x['date'], reverse=True)
        name = people[p]['info']['name']
        path = '/p/' + p
        search[name] = path

        with open('html' + path, 'w') as fh:
            fh.write(person_template.render(
                id     = p,
                person = people[p],
                h1     = people[p]['info']['name'],
                title  = 'Podcasts of and interviews with {}'.format(people[p]['info']['name']),
            ))

    source_template = env.get_template('source.html')
    if not os.path.exists('html/s/'):
        os.mkdir('html/s/')
    for s in sources:
        search[ s['title'] ] = '/s/' + s['name'];
        with open('html/s/' + s['name'], 'w') as fh:
            fh.write(source_template.render(
                source = s,
                h1     = s['title'],
                title  = s['title'],
            ))

    tag_template = env.get_template('tag.html')
    if not os.path.exists('html/t/'):
        os.mkdir('html/t/')
    for t in tags:
        search[ tags[t]['tag'] ] = '/t/' + t;
        with open('html/t/' + t, 'w') as fh:
            #tags[t]['path'] = t
            fh.write(tag_template.render(
                tag   = tags[t],
                h1    = tags[t]['tag'],
                title = tags[t]['tag'],
                #title = 'Podcasts and discussions about {}'.format(tags[t]['tag'])
            ))


    stats = {
        'sources'  : len(sources),
        'people'   : len(people),
        'episodes' : sum(len(x['episodes']) for x in sources)
    }

    main_template = env.get_template('index.html')
    with open('html/index.html', 'w') as fh:
        fh.write(main_template.render(
            h1      = 'xCast - Tech related podcast and presentations',
            title   = 'xCast - Tech related podcast and presentations',
            stats   = stats,
            tags    = tags,
            sources = sources,
            people = people,
            people_ids = sorted(people.keys()),
        ))

    with open('html/people', 'w') as fh:
        fh.write(env.get_template('people.html').render(
            h1      = 'List of people',
            title   = 'xCast - list of people',
            stats   = stats,
            tags    = tags,
            sources = sources,
            people = people,
            people_ids = sorted(people.keys()),
        ))
    with open('html/sources', 'w') as fh:
        fh.write(env.get_template('sources.html').render(
            h1      = 'List of podcasts',
            title   = 'xCast - list of podcasts',
            stats   = stats,
            tags    = tags,
            sources = sorted(sources, key=lambda x: x['title']),
            people = people,
            people_ids = sorted(people.keys()),
         ))
    with open('html/tags', 'w') as fh:
        fh.write(env.get_template('tags.html').render(
            h1      = 'Tags',
            title   = 'xCast - tags',
            stats   = stats,
            tags    = tags,
            sources = sources,
            people = people,
            people_ids = sorted(people.keys()),
        ))
    with open('html/search.json', 'w') as fh:
        json.dump(search, fh)



def read_people():
    people = {}
    for filename in glob.glob("data/people/*.txt"):
        try:
            this = {}
            nickname = os.path.basename(filename)
            nickname = nickname[0:-4]
            with open(filename) as fh:
                for line in fh:
                    line = line.rstrip('\n')
                    if re.search(r'\A\s*\Z', line):
                        continue
                    k,v = re.split(r'\s*:\s*', line, maxsplit=1)
                    this[k] = v
            for field in ['twitter', 'github', 'home']:
                if field not in this:
                    warn("{} missing for {}".format(field, nickname))
            people[nickname] = {
                'info': this,
                'episodes' : [],
                'hosting' : []
            }
        except Exception as e:
            exit("ERROR: {} in file {}".format(e, filename))

    return people

def read_episodes(sources):
    episodes = []
    for src in sources:
        print("Processing source {}".format(src['name']))
        file = 'data/' + src['name'] + '.json'
        src['episodes'] = []
        if os.path.exists(file):
            with open(file) as fh:
                try:
                    new_episodes = json.load(fh)
                    for episode in new_episodes:
                        episode['source'] = src['name']
                        if 'ep' not in episode:
                            warn("ep missing from {} episode {}".format(src['name'], episode['permalink']))
                    episodes.extend(new_episodes)
                    src['episodes'] = new_episodes
                except json.decoder.JSONDecodeError as e:
                    exit("ERROR: Could not read in {} {}".format(file, e))
                    src['episodes'] = [] # let the rest of the code work
                    pass
    return episodes

def tag2path(tag):
    return re.sub(r'[\W_]+', '-', tag.lower())

def read_tags():
    tags = {}
    with open('data/tags.csv') as fh:
        rd = csv.DictReader(fh, delimiter=';') 
        for row in rd:
            row['path'] = tag2path(row['tag'])
            row['episodes'] = []
            tags[ row['path'] ] = row
    return tags

def warn(msg):
    pass
    #print("WARN ", msg)

main()

# vim: expandtab
