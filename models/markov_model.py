import random

class Markov(object):

    def __init__(self, entry_data):
        self.cache = {}
        self.entry_data = entry_data
        self.tokens = self.tokenize()
        self.num_tokens = len(self.tokens)
        self.db()

    def tokenize(self):
        tokeny = " ".join(self.entry_data)
        words = tokeny.split()
        return words

    def triples(self, ngrams = 3):
        """ expand this to accomodate for n-grams instead of just triples
        """

        if self.num_tokens < 3:
            return

        for i in range(self.num_tokens - 2):
            yield (self.tokens[i], self.tokens[i+1], self.tokens[i+2])

    def db(self):
        for w1, w2, w3 in self.triples():
            pair = (w1, w2)

            if pair in self.cache:
                self.cache[pair].append(w3)
            else: self.cache[pair] = [w3]

    def generate_tweet(self, size = 3):
        # let user choose seed
        seed = random.randint(0, self.num_tokens - 3)
        seed_word, next_word = self.tokens[seed], self.tokens[seed+1]
        w1, w2 = seed_word, next_word
        gen_words = []
        for i in range(size):
            gen_words.append(w1)
            w1, w2 = w2, random.choice(self.cache[(w1, w2)])
        gen_words.append(w2)
        return ' '.join(gen_words)
