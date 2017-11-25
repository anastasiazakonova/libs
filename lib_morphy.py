# -*- coding: utf-8 -*-
import pymorphy2
morph = pymorphy2.MorphAnalyzer()

def isRusChar(x):
    return u'абвгдеёжзийклмнопрстуфхцчшщъыьэюя'.find(x) >= 0

def getNormalizedWord(word, only_one_value=False):
    word = word.lower()
    word = filter(isRusChar, word)
    res = morph.parse(word)
    uwords = set()
    uwords.add(word)
    for r in res:
        uwords.add(r.normal_form)
        if only_one_value:
            break
    return uwords

def getNormalizedSentence(sentence, only_one_value=False):
    try:
        sentence = sentence.lower()
        totalSet = set()
        for w in sentence.split(' '):
            w = w.strip()
            wset = getNormalizedWord(w, only_one_value=only_one_value)
            totalSet = totalSet | wset
        return totalSet
    except:
        return set()

# q = u'привет, как у тебя дела!'
# q_res = filter(isRusChar, q)
# print q_res
# nset = getNormalizedSentence(q)
# print u' '.join(nset)