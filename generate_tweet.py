import json
import os
from models.markov_model import Markov
from nltk.corpus import stopwords


def find_last(lst, sought_elt):
    for r_idx, elt in enumerate(reversed(lst)):
        if elt.endswith(sought_elt):
            return len(lst) - 1 - r_idx

with open("clean/11.txt", "r") as g:
    lines = g.readlines()


tweet_generator = Markov(lines)

for i in range(1):
    yes = True
    while yes == True:
        try:
            remove = ["(", ")", "'"]
            title = tweet_generator.generate_tweet(size=10).lower()
            ttokens = title.split()
            ttokens = [token.translate(None, ''.join(remove)) for token in ttokens]
            #print tokens
            #print " ".join(ttokens)
            #we want tweets to end on a period
            element = find_last(ttokens, ("?",".","!",";","-"))

            new_title = " ".join(ttokens[0:element+1])
            print new_title
            yes = False
        except:
            continue
