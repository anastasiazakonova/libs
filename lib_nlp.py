from functools import lru_cache

from stop_words import get_stop_words

stopWords = get_stop_words('russian')

import os
import pickle
import pymorphy2
import re
import shlex
# import Stemmer
import subprocess

morph = pymorphy2.MorphAnalyzer()

from collections import defaultdict
from itertools import combinations
from nltk.stem import SnowballStemmer
from nltk import word_tokenize

stemmer = SnowballStemmer('russian')
re_alphanum = re.compile('[^а-яА-Я]')


def stem_tokens(tokens, stemmer):
    stemmed = []
    for item in tokens:
        stemmed.append(stemmer.stem(item))
    return stemmed


@lru_cache(maxsize=1024 * 5)
def tokenize(text):
    # remove non letters
    text = re_alphanum.sub(' ', text)
    # connect 'не' with following word
    text = text.replace('не ', 'не')
    # tokenize
    tokens = word_tokenize(text)
    stems = stem_tokens(tokens, stemmer)
    return stems


re_alphanum_norm = re.compile(u'[^а-яa-zА-ЯA-Zёй0-9\-]')
re_many_s = re.compile('\s+')
emoji_pattern = re.compile('['
                           u'\U0001F600-\U0001F64F'  # emoticons
                           u'\U0001F300-\U0001F5FF'  # symbols & pictographs
                           u'\U0001F680-\U0001F6FF'  # transport & map symbols
                           u'\U0001F1E0-\U0001F1FF'  # flags (iOS)
                           ']+', flags=re.UNICODE)

# https://stackoverflow.com/questions/33404752/removing-emojis-from-a-string-in-python
@lru_cache(maxsize=1024 * 5)
def only_alphanum_and_punct(text_inp):
    text = emoji_pattern.sub(' ', text_inp)
    return ' '.join(text.split())


@lru_cache(maxsize=1024 * 5)
def only_alphanum(text_inp):
    text = re_alphanum_norm.sub(u' ', text_inp)
    text = re_many_s.sub(' ', text)
    return text


re_alpha_norm = re.compile(u'[^а-яa-zА-ЯA-Zёй\-]')


@lru_cache(maxsize=1024 * 5)
def only_alpha(text_inp):
    text = re_alpha_norm.sub(u' ', text_inp)
    text = re_many_s.sub(' ', text)
    return text


re_alpharus_norm = re.compile(u"[^а-яА-Яёй\-]")
@lru_cache(maxsize=1024)
def only_alpha_rus(text_inp):
    text = re_alpharus_norm.sub(u' ', text_inp)
    text = re_many_s.sub(' ', text)
    return text.strip()


import pymorphy2

morph = pymorphy2.MorphAnalyzer()


def get_morph():
    global morph
    return morph


@lru_cache(maxsize=1024 * 5)
def norm_alphanum_text(text):
    text = only_alphanum(text)
    return ' '.join([morph.parse(t)[0].normal_form for t in text.split(' ')])


re_tagsymbols = re.compile(u'[^а-яА-Яa-zA-Zёй0-9()№!—?«»#\'\"\»\«\-\ \.]')


@lru_cache(maxsize=1024 * 5)
def strip_object_text(text):
    text = re_tagsymbols.sub(u' ', text)
    text = re_many_s.sub(' ', text)
    return text


def leave_only_noun(text):
    parts = text.split(' ')
    nouns = set()
    for p in parts:
        w = morph.parse(p)[0]
        if 'NOUN' in w.tag:
            nouns.add(p)
    return list(nouns)


def vk_remove_mention(text):
    if not '[id' in text:
        return text
    from_pos = text.index('[id')
    to_pos = text.index(']')
    return text[to_pos+2:]


def leave_only_noun_phrases(words: list):
    result = []
    for obj in words:
        if len(obj.split()) > 1:
            result.append(obj)
        try:
            gr = morph.parse(obj)[0].tag.POS
            if gr == 'NOUN':
                result.append(obj)
        except:
            continue
    return result


import requests

from pyaspeller import YandexSpeller, Word
from pymystem3 import Mystem

mystem = Mystem()
speller = YandexSpeller()


def spell_text(text: str):
    return text  ## temporary disable yandex speller while not wrapper is ready
    try:
        word_error = {}
        for error in speller._spell_text(text):
            w, s = error['word'], error['s']
            if s:
                # Don't edit tags
                if '#' + w in text:
                    continue
                word_error[w] = s[0]

        for w in word_error:
            text = text.replace(w, word_error[w])
        return text
    except Exception as e:
        print('Yandex Speller doesn\'t work: {}'.format(str(e)))
        return text


def spell_word(word: str):
    try:
        gr = morph.parse(word)[0].tag.POS
        if gr not in ['PREP', 'CONJ', 'PRCL', 'INTJ', 'NPRO'] and len(word) > 2:
            speller_w = Word(word)
            return word if speller_w.correct else speller_w.spellsafe
        return word
    except:
        return word


def lemma(objects: str):
    try:
        return ' '.join([''.join(mystem.lemmatize(object)).strip() for object in objects.split()])
    except RuntimeError:
        return ' '.join([morph.parse(object)[0].normal_form for object in objects.split()])



def remove_quotes(word):
    quotes = {'\'', '"', '»', '«'}
    return ''.join(ch for ch in word if ch not in quotes)

import time


def millis():
    return time.time() * 1000


def tokenizer_norm(text):
    text = norm_alphanum_text(text)
    text = text.lower()
    text = text.strip()
    tokens = text.split(' ')
    return [token.strip() for token in tokens if len(token.strip()) > 0]


def tokenizer(text):
    text = only_alphanum(text)
    text = text.lower()
    text = text.strip()
    tokens = text.split(' ')
    return [token.strip() for token in tokens if len(token.strip()) > 0]


def short_text(text, n=10):
    return ' '.join(text.split()[:n])


def clean_html_from_text(t):
    from bs4 import BeautifulSoup
    return BeautifulSoup(t, 'lxml').text


# Replacement class
class SimilarWords:
    def __init__(self, dictionary=None):
        self.prior = {'NOUN': 4, 'ADJF': 3, 'INFN': 2, 'ADVB': 1}
        self.dictionary = dictionary if dictionary else defaultdict(set)
        self._is_train = False
        # self.stemmer = Stemmer.Stemmer('russian')
        self.stemmer = stemmer

    def _add_word(self, word: str):
        # stem = self.stemmer.stemWord(word)
        stemm = self.stemmer.stem(word)
        self.dictionary[stemm].add(word)

    # docs: list of lists
    def train(self, docs, model, threshold=0.75):
        if self._is_train:
            self.dictionary = defaultdict(set)

        for doc in docs:
            for word in doc:
                self._add_word(word)

        self._train(model, threshold=threshold)
        self._is_train = True

    def _train(self, model, threshold):
        for stem in self.dictionary:
            values = self.dictionary[stem]
            if len(values) == 1:
                self.dictionary[stem] = {list(values)[0]: values}
                continue

            result_word = []
            viewed_words = set()
            for w1, w2 in combinations(values, 2):
                try:
                    if self.sim(model, w1, w2) >= threshold:
                        _is_add = False
                        for result in result_word:
                            if w1 in result or w2 in result:
                                for w in [w1, w2]:
                                    result.add(w)
                                _is_add = True
                                break
                        if not _is_add:
                            result_word.append({w1, w2})
                        for w in [w1, w2]:
                            viewed_words.add(w)
                    else:
                        for w in [w1, w2]:
                            if w not in viewed_words:
                                result_word.append({w})
                                viewed_words.add(w)
                except KeyError:
                    continue

            self.dictionary[stem] = {self._priority_part_of_speech(words): words for words in result_word}

    # predict
    def form_of_word(self, word):
        tag = 'Geox'
        for tag_w in morph.tag(word):
            if tag in tag_w:
                return morph.normal_forms(word)[0]

        # stem = self.stemmer.stemWord(word)
        stem = self.stemmer.stem(word)
        try:
            if word in self.dictionary[stem]:
                return word
            else:
                for word_norm, values in self.dictionary[stem].items():
                    if word in values:
                        return word_norm
                return word
        except:
            return word

    def sim(self, model, word1, word2):
        return model.similarity(word1, word2)

    def _priority_part_of_speech(self, words):
        def priority_w(word):
            try:
                pos = morph.tag(word)[0].POS
                pos = (word, self.prior[pos])
            except KeyError:
                pos = (word, 0)
            return pos

        if len(words) == 1:
            return list(words)[0]

        pos = [priority_w(word) for word in words]
        pos.sort(key=lambda x: x[-1], reverse=True)
        max_w = []
        for word, w in pos:
            if w != pos[0][1]:
                break
            max_w.append((word, len(word)))
        max_w.sort(key=lambda x: x[-1])

        return max_w[0][0]

    def save_dictionary(self, path):
        file_name = path.split('.')
        if len(file_name) == 1:
            path += '.pkl'
        else:
            if file_name[-1] == 'pkl':
                pass
            else:
                file_name[-1] = 'pkl'
                path = ''.join(file_name)

        with open(path, 'wb') as file:
            pickle.dump(self.dictionary, file)


# https://github.com/facebookresearch/fastText
def model_fastText(path_fasttext, input_file, output_model, alg='skipgram', params=''):
    cur = os.getcwd()
    os.chdir(path_fasttext)

    try:
        if params:
            params = ' ' + ' '.join(['-{} {{1}}'.format(param, value) for param, value in params.items()])
        command_line = './fasttext {} -input {} -output {}'.format(alg, input_file, output_model)
        command_line += params
        args = shlex.split(command_line)
        print(command_line)

        print(subprocess.check_output(args))
    finally:
        os.chdir(cur)
