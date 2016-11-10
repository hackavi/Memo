

import feedparser
import string
import time
from project_util import translate_html
from news_gui import Popup


def process(url):
    """
    Fetches news items from the rss url and parses them.
    Returns a list of NewsStory-s.
    """
    feed = feedparser.parse(url)
    entries = feed.entries
    ret = []
    for entry in entries:
        guid = entry.guid
        title = translate_html(entry.title)
        link = entry.link
        summary = translate_html(entry.summary)
        try:
            subject = translate_html(entry.tags[0]['term'])
        except AttributeError:
            subject = ""
        newsStory = NewsStory(guid, title, subject, summary, link)
        ret.append(newsStory)
    return ret


class NewsStory:
    def __init__(self, guid, title, subject, summary, link):
        self.guid = guid
        self.title = title
        self.subject = subject
        self.summary = summary
        self.link = link

    def get_guid(self):
        try:
            return self.guid
        except:
            return ''

    def get_title(self):
        try:
            return self.title
        except:
            return ''

    def get_subject(self):
        try:
            return self.subject
        except:
            return ''
    def get_summary(self):
        try:
            return self.summary
        except:
            return ''
    
    def get_link(self):
        try:
            return self.link
        except:
            return ''

class Trigger(object):
    def evaluate(self, story):
        """
        Returns True if an alert should be generated
        for the given news item, or False otherwise.
        """
        raise NotImplementedError


class WordTrigger (Trigger):
    def __init__(self,word):
        self.word = word.lower()


    def is_word_in(self,text):
        text_lower = text.lower()
        for c in string.punctuation:
            if c in text:
                text_lower = text_lower.replace(c, ' ')
        words = text_lower.split(' ')
        if self.word in words:
            return True
        else:
            return False

        


class TitleTrigger(WordTrigger):
    def __init__(self,word):
        self.word = word.lower()

    def evaluate(self, story):
        if self.is_word_in(story.get_title()):
            return True
        else :
            return False


class SubjectTrigger(WordTrigger):
    def __init__(self,word):
        self.word = word.lower()

    def evaluate(self, story):
        if self.is_word_in(story.get_subject()):
            return True
        else:
            return False


class SummaryTrigger(WordTrigger) :
    def __init__(self,word):
        self.word = word.lower()

    def evaluate(self, story):
        if self.is_word_in(story.get_summary()):
            return True
        else:
            return False
        



class NotTrigger(Trigger):
    def __init__(self, trigger):
        self.trigger = trigger

    def evaluate(self,story):
        return not(self.trigger.evaluate(story))
    

class AndTrigger(Trigger):
    def __init__(self, trig1, trig2):
        self.trig1 = trig1
        self.trig2 = trig2

    def evaluate(self,story):
        return (self.trig1.evaluate(story))and(self.trig2.evaluate(story))
    

class OrTrigger(Trigger):
    def __init__(self, trig1, trig2):
        self.trig1 = trig1
        self.trig2 = trig2

    def evaluate(self,story):
        return ( self.trig1.evaluate(story) ) or ( self.trig2.evaluate(story) )



class PhraseTrigger(Trigger):
    def __init__(self, phrase):
        self.phrase = phrase

    def evaluate(self,story):
        title = story.get_title()
        subject = story.get_subject()
        summary = story.get_summary()
        phrase = self.phrase
        if (phrase in title) or (phrase in subject) or (phrase in summary):
            return True
        else:
            return False
    




def filter_stories(stories, triggerlist):
    
    filteredStories = []
    for story in stories :
        alert = False
        for trigger in triggerlist:
            alert = trigger.evaluate(story)
            if alert:
                break
        if alert:
            filteredStories.append(story)
        
        
    return filteredStories


def readTriggerConfig(filename):
    """
    Returns a list of trigger objects
    that correspond to the rules set
    in the file filename
    """
    
    triggerfile = open(filename, "r")
    all = [ line.rstrip() for line in triggerfile.readlines() ]
    lines = []
    for line in all:
        if len(line) == 0 or line[0] == '#':
            continue
        lines.append(line)

    
    triggers = {}
    triggerlist = []
    for line in lines:
        words = line.split(' ', 2)
        if words[0].lower() != 'add':
            types = words[1].lower()
            if types == 'title':
                triggers[words[0]] = TitleTrigger(words[2])
            elif types == 'subject':
                triggers[words[0]] = SubjectTrigger(words[2])
            elif types == 'summary':
                triggers[words[0]] = SummaryTrigger(words[2])
            elif types == 'not':
                triggers[words[0]] = NotTrigger(triggers[words[2]])
            elif types == 'and':
                ands = words[2].split(' ')
                triggers[words[0]] = AndTrigger(triggers[ands[0]], triggers[ands[1]])
            elif types == 'or':
                ors = words[2].split(' ')
                triggers[words[0]] = OrTrigger(triggers[ors[0]], triggers[ors[1]])
            elif types == 'phrase':
                triggers[words[0]] = PhraseTrigger(words[2])

        else :
            words = line.split(' ')
            for word in words[1:]:
                triggerlist.append(triggers[word])

    return triggerlist


            
        
        
    
import thread

def main_thread(p):


    t1 = SubjectTrigger("Trump")
    t2 = SummaryTrigger("Hillary")
    t3 = PhraseTrigger("Election")
    t4 = OrTrigger(t2, t3)
    triggerlist = [t1, t4]
    
    
    triggerlist = readTriggerConfig("triggers.txt")

    guidShown = []
    
    while True:
        print "Polling..."

        # Get stories from Google's Top Stories RSS news feed
        stories = process("http://news.google.com/?output=rss")
        # Get stories from Yahoo's Top Stories RSS news feed
        stories.extend(process("http://rss.news.yahoo.com/rss/topstories"))

        # Only select stories we're interested in
        stories = filter_stories(stories, triggerlist)
    
        # Don't print a story if we have already printed it before
        newstories = []
        for story in stories:
            if story.get_guid() not in guidShown:
                newstories.append(story)
        
        for story in newstories:
            guidShown.append(story.get_guid())
            p.newWindow(story)

        print "Sleeping..."
        time.sleep(SLEEPTIME)

SLEEPTIME = 60 #seconds -- how often we poll
if __name__ == '__main__':
    p = Popup()
    thread.start_new_thread(main_thread, (p,))
    p.start()

