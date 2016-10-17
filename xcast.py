import argparse
import glob
import json
import os
import re
import csv
from jinja2 import Environment, PackageLoader

def main():

    with open('data/sources.json') as fh:
        sources = json.load(fh)

    parser = argparse.ArgumentParser()
    parser.add_argument('--list', help = 'List sources', action='store_true')
    parser.add_argument('--html', help = 'Generate HTML', action='store_true')
    args = parser.parse_args()

    
    if args.list:
        for s in sources:
            print('{:20} {}'.format(s.get('name', ''), s.get('title', '')))
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
            for h in e['hosts'].keys():
                if h not in people:
                    exit("ERROR: '{}' is not in the list of people".format(h))
                people[h]['hosting'].append(e)
        generate_pages(sources, people, tags)
    else:
        parser.print_help()

def generate_pages(sources, people, tags):
    env = Environment(loader=PackageLoader('xcast', 'templates'))

    person_template = env.get_template('person.html')
    if not os.path.exists('html/p/'):
        os.mkdir('html/p/')
    for p in people.keys():
        with open('html/p/' + p, 'w') as fh:
            fh.write(person_template.render(
                id     = p,
                person = people[p],
                h1     = people[p]['info']['name'],
                title  = 'Podcasts of and interviewes with {}'.format(people[p]['info']['name']),
            ))

    source_template = env.get_template('source.html')
    if not os.path.exists('html/s/'):
        os.mkdir('html/s/')
    for s in sources:
    #    #print(s)
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
            print("ERROR: {} in file {}".format(e, filename))

    return people

def read_episodes(sources):
    episodes = []
    for src in sources:
        print("Processing source {}".format(src['name']))
        file = 'data/' + src['name'] + '.json'
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
                    print("ERROR: Could not read in {}".format(file))
                    print(e)
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
