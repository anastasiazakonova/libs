import wikipedia
import google
import telepot
import pymorphy2
import csv
import re
from copy import deepcopy
from lib_objects import Subject, is_geo
from lib_nlp import morph

re_alphanum = re.compile('[^а-яА-Яa-zA-Z0-9ё,.()№"!—?«»-]')
re_betanum = re.compile('[а-яА-Яё]')


def tokenize(text):
    # remove non letters
    text = re_alphanum.sub(" ", text)
    text = text.replace('.', ' . ')
    text = text.replace('?', ' ? ')
    text = text.replace('!', ' ! ')
    text = text.replace(',', ' , ')
    text = text.replace('«', ' « ')
    text = text.replace('»', ' » ')
    text = text.replace('"', ' " ')
    text = text.replace('(', ' ( ')
    text = text.replace(')', ' ) ')
    text = text.replace('-', ' - ')
    text = text.replace('—', ' — ')
    text = text.replace(':', ' : ')
    text = text.replace('\n', ' ')
    text = text.replace('. . .', '...')
    text = text.replace('. .', '..')
    for i in range(20):
        text = text.replace('  ', ' ')
    # connect 'не' with following word
    # text = text.replace(",", " ")
    # tokenize
    # tokens = word_tokenize(text)
    return text


def is_fake(parse):
    res = 0
    for m in parse.methods_stack:
        res += isinstance(m[0], pymorphy2.units.by_analogy.KnownSuffixAnalyzer.FakeDictionary)
        res += isinstance(m[0], pymorphy2.units.by_analogy.UnknownPrefixAnalyzer)
        res += isinstance(m[0], pymorphy2.units.by_analogy.UnknownSuffixAnalyzer)
    return res > 0


class Wiki:
    names = None
    coords = None

    def __init__(self, source):
        self.coords = []
        self.names = []
        for item in source:
            self.names.append(item[0])
            self.coords.append(item[1])

    def __call__(self, item):
        try:
            i = self.names.index(item[0].upper() + item[1:])
            return self.coords[i]
        except:
            return None

    def score(self, items):
        res = 0
        for item in items:
            res += self(item) is not None
        return res / len(items)


def upper_case(string, method='Sent'):
    if len(string) == 0:
        return ''
    else:
        if method == 'Sent':
            if '-' not in string:
                return string[0].upper() + (string[1:] if len(string) > 1 else '')
            else:
                return ('-'.join([upper_case(st) for st in string.split('-')]))
        elif method == 'lowr':
            return string.lower()
        else:
            return string.upper()


def normal_form(string, case='nomn'):
    words = string.split(' ')
    norm_words = []
    for word in words:
        try:
            if word.isupper():
                capt = 'UPPR'
            elif word[0].isupper():
                capt = 'Sent'
            else:
                capt = 'lowr'
            if capt != 'UPPR' and not is_fake(morph.parse(word)[0]):
                norm_words.append(upper_case(morph.parse(word)[0].inflect({case}).word, method=capt))
            elif capt != 'UPPR' and is_fake(morph.parse(word)[0]):
                norm_words.append(upper_case(word, method=capt))
            else:
                norm_words.append(upper_case(word, method='UPPR'))
        except:
            norm_words.append(word)
    return ' '.join(norm_words)


def not_stop_word(word):
    return word not in ('того', 'пара', 'котор', 'нива', 'выша')


def parse_okato_string(line):
    if line.split(' ')[0][-1] == ',':
        return morph.parse(line.split(' ')[0][:-1])[0].normal_form
    else:
        return morph.parse(line.split(' ')[0])[0].inflect({'sing'}).normal_form


def get_okato_base_by_code(code):
    result = {}
    try:
        with open('/var/data/okato/okato.csv', 'r', encoding='utf-8') as inp:
            reader = csv.reader(inp, delimiter=';')
            lines = [line for line in reader]
    except:
        with open('local/okato.csv', 'r', encoding='utf-8') as inp:
            reader = csv.reader(inp, delimiter=';')
            lines = [line for line in reader]
    # print(len(lines))
    okato_dict = {}
    for line in lines:
        okato_dict[line[1]] = line[0]
    for line in lines:
        if line[1][:2] == str(code):
            string = line[0]
            for obj in string.split(' '):
                if len(obj) > 0:
                    if obj[0].isupper() and not is_geo(upper_case(obj, 'lowr')):
                        if 'ADJF' in morph.parse(obj)[0].tag and line[2] in okato_dict:
                            if len(string.split(' ')) == 1:
                                try:
                                    result[string] = string + ' ' + parse_okato_string(okato_dict[line[2]])
                                except:
                                    print(okato_dict[line[2]].split(' ')[0])
                            else:
                                result[string] = string
                            break
                        else:
                            result[string] = string
                            break

            # result.append(line[0])
            # result.append(line[4])
    # print(len(result))

    return result


def get_okato_centers(max_code_size=5):
    result = []
    try:
        with open('/var/data/okato/okato.csv', 'r', encoding='utf-8') as inp:
            reader = csv.reader(inp, delimiter=';')
            lines = [line for line in reader]
    except:
        with open('local/okato.csv', 'r', encoding='utf-8') as inp:
            reader = csv.reader(inp, delimiter=';')
            lines = [line for line in reader]

    for line in lines:
        if len(line[1]) <= max_code_size:
            result.append(line[0])
            result.append(line[4])

    return result


general_okato_base = get_okato_centers()
spb_okato_base = get_okato_base_by_code(41)
okato_base = spb_okato_base #+ general_okato_base


def is_in_okato(name):
    try:
        parses = morph.parse(name)
        for parse in parses:
            try:
                if upper_case(parse.inflect({'femn'}).word) in okato_base:
                    return True, okato_base[upper_case(parse.inflect({'femn'}).word)]
                elif upper_case(parse.inflect({'masc'}).word) in okato_base:
                    return True, okato_base[upper_case(parse.inflect({'femn'}).word)]
                elif upper_case(parse.inflect({'neut'}).word) in okato_base:
                    return True, okato_base[upper_case(parse.inflect({'femn'}).word)]
            except:
                pass
        is_in = upper_case(name) in okato_base
        if is_in:
            return True, okato_base[upper_case(name)]
        else:
            return False, upper_case(name)
    except:
        return False, upper_case(name)


def geo_adj(word, trust_score=0.2):
    res = False
    n_word = word
    # print(word)
    if word[-4:] == 'ский':
        parse = morph.parse(word[:-4])
        res = 'Geox' in parse[0].tag and parse[0].score >= trust_score
        if res:
            n_word = word[:-4]
        if not res and word[-5] in ('н', 'в'):
            parse = morph.parse(word[:-4] + 'о')
            res = 'Geox' in parse[0].tag and parse[0].score >= trust_score
            if res:
                n_word = word[:-4] + 'о'
            if not res:
                parse = morph.parse(word[:-4] + 'а')
                res = 'Geox' in parse[0].tag and parse[0].score >= trust_score
                if res:
                    n_word = word[:-4] + 'а'
        if not res and is_fake(morph.parse(word)[0]):
            if word[-2:] == 'ий':
                parse = morph.parse(word[:-2])
                res = 'Geox' in parse[0].tag and parse[0].score >= trust_score
                if res:
                    n_word = word[:-2]
    return res, word


def is_org(word):
    return morph.parse(word)[0].normal_form in ['администрация', 'министерство', 'палата', 'собрание', 'служба',
                                                'комитет', 'служба', 'пресс-служба', 'отдел', 'отделение', 'комиссия',
                                                'организация', 'ассамблея', 'совет']


def is_of_what(ps):
    return ('gent' in ps.tag or 'nomn' in ps.tag) and ('NOUN' in ps.tag or 'ADJF' in ps.tag or
                                        'ADJS' in ps.tag or 'Abbr' in ps.tag) \
           and 'Apro' not in ps.tag or 'CONJ' in ps.tag


def quotes_entities(text):
    cont = []
    stack = []
    collect_flag = False
    words = text.split(' ')
    add_flag = True
    for word in words:
        if word == '"' or (word == '«' and not collect_flag) or (word == '»' and collect_flag):
            collect_flag = not collect_flag
            if not collect_flag:
                to_add = normal_form(' '.join(stack))
                if 0 < len(stack) < 3 and to_add not in cont and add_flag:
                    cont.append(to_add)
                stack = []
                add_flag = True
        if collect_flag and word not in ('"', '«', '»') and len(word) > 0 and word[0].isupper():
            stack.append(word)
        elif collect_flag and word not in ('"', '«', '»') and len(word) > 0:
            add_flag = False

    return cont


class SingleTagEntities:
    # global morph
    # morph = pymorphy2.MorphAnalyzer()
    tokenize = tokenize
    interact = False
    min_score = 0.3
    max_dist = 0.1
    wiki = None
    tag = None
    additional_local_test = lambda self, word: (False, word)
    additional_global_test = lambda self, text: []

    def __init__(self, morph_v=None, tokenize_v=None, tag_v='None', min_score=None, max_dist_v=None,
                 local_test=None, global_test=None, interact=None):
        if interact is not None:
            self.interact = interact
        if tokenize_v is not None:
            self.tokenize = tokenize_v
        if tag_v is not None:
            self.tag = tag_v
        if max_dist_v is not None:
            self.max_dist = max_dist_v
        if local_test is not None:
            self.additional_local_test = local_test
        if global_test is not None:
            self.additional_global_test = global_test
        if min_score is not None:
            self.min_score = min_score

    def __call__(self, samples):
        samples_res = []
        for sample in samples:
            words = tokenize(sample).split(' ')
            loc_res = self.additional_global_test(' '.join(words))
            for word in words:
                # print(word)
                if word.isupper():
                    capt = 'UPPR'
                else:
                    capt = 'Sent'
                parse = morph.parse(word)
                for p in parse:
                    # print('>> ', p.tag)
                    (is_adj, n_word) = self.additional_local_test(p.normal_form)
                    if ((self.tag in p.tag if self.tag is not None else False) or is_adj) and\
                                    p.score > self.min_score and p.score > parse[0].score - self.max_dist:
                        # if is_adj:
                            # n_word = p.normal_form
                            if not_stop_word(n_word):
                                if 'Abbr' not in p.tag and capt != 'UPPR':
                                    if upper_case(n_word) not in loc_res:
                                        loc_res.append(upper_case(n_word))
                                else:
                                    if n_word.upper() not in loc_res:
                                        loc_res.append(n_word.upper())
                if loc_res not in samples_res:
                    samples_res.append(loc_res)
        return samples_res

    def connect_to_wiki(self, source):
        if source is not None:
            self.wiki = Wiki(source)

    def validate(self, samples):
        res = self(samples)
        pos = 0
        nul = 0
        for r in res:
            if len(r) > 0:
                pos += self.wiki.score(r)
            else:
                nul += 1
        return pos / (len(res) - nul)


def maybe_name(string, tag='Name', where_from=-1, force_surn=False):
    # print('MN Req from ' + str(where_from) + ' for ' + tag + ': ' + string)
    if len(string) == 0 or not is_letter(string):
        return None
    elif string[0].isupper():
        if len(string) == 1 and tag != 'Surn':
            return morph.parse(string)[0]
        else:
            for p in morph.parse(string):
                # print(p)
                if tag in p.tag:
                    # print(p.normal_form + ' ' + tag + ' ' + str(where_from))
                    return p
        if force_surn and tag == 'Surn' and len(string) > 3:
            # print('Force Surn')
            return string[0].isupper() and string[1:].islower()
    else:
        return None


def next_element(lst, prev_len=2):
    res = ''
    ind = -1
    if len(lst) > 0:
        if is_letter(lst[0]) and prev_len != 1:
            res = lst[0]
            ind = 0
        elif prev_len == 1 and len(lst) > 1 and lst[1] != '.' and lst[0] == '.':
            res = lst[1]
            ind = 1
    return res, ind


def is_letter(symbol):
    return re_betanum.sub('', str(symbol)) == ''


def next_two_elements(lst, prev_len=2):
    second = ''
    first, ind = next_element(lst, prev_len=prev_len)
    if ind > -1 and ind + 1 <= len(lst) and is_letter(first):
        second, ind = next_element(lst[ind+1:], prev_len=len(first))
    return first, second


class Name:
    def __init__(self, name_obj):
        if isinstance(name_obj, str):
            entities = name_obj.split(' ')
            self.patron = Word('')
            self.name = Word('')
            self.surname = Word('')
            aux_ent = name_obj.split(' ')
            for e in entities:
                word = Word(e)
                if 'Surn' in morph.parse(e)[0].tag and self.surname.empty and not word.short:
                    self.surname = word # Word(morph.parse(e)[0].normal_form)
                    aux_ent.remove(e)
                elif ('Name' in morph.parse(e)[0].tag or word.short) and self.name.empty:
                    self.name = word # (Word(morph.parse(e)[0].normal_form) if not word.short else word)
                    aux_ent.remove(e)
                elif ('Patr' in morph.parse(e)[0].tag or word.short) and self.patron.empty:
                    self.patron = word # (Word(morph.parse(e)[0].normal_form) if not word.short else word)
                    aux_ent.remove(e)
            entities = aux_ent
            if len(entities) > 0:
                w0 = Word(entities[0])
                if self.name.empty:
                    self.name = w0
                elif self.surname.empty and not w0.short:
                    self.surname = w0
                elif self.patron.empty:
                    self.patron = w0
            if len(entities) > 1:
                w1 = Word(entities[1])
                if self.name.empty:
                    self.name = w1
                elif self.surname.empty and not w1.short:
                    self.surname = w1
                elif self.patron.empty:
                    self.patron = w1
        elif isinstance(name_obj, list):
            if len(name_obj) == 3:
                self.surname = Word(name_obj[0])
                self.name = Word(name_obj[1])
                self.patron = Word(name_obj[2])
            else:
                self.patron = Word('')
                self.name = Word('')
                self.surname = Word('')
                print('WARNING: len of the name_obj list is not equal to 3')
        self.gndr = 'None'
        if len(self) > 0:
            self.normalize()

    def __eq__(self, other):
        return self.surname == other.surname and self.name == other.name and self.patron == other.patron

    def __add__(self, other):
        if self != other and not len(self) == len(other) == 1 and self.surname != other.surname and \
                not self.surname.empty and not other.surname.empty:
            return self
        else:
            new_obj = deepcopy(self)
            if self.surname.empty or other.surname.empty:
                new_obj.surname += other.surname
            if self.name == other.name and self.patron == other.patron:
                new_obj.name += other.name
                new_obj.patron += other.patron
        return new_obj

    def __len__(self):
        res = 3
        if self.patron.empty:
            res -= 1
        if self.name.empty:
            res -= 1
        if self.surname.empty:
            res -= 1
        return res

    def __repr__(self):
        return str(self.surname) + (' ' + str(self.name) if len(self.name) > 0 else '') + \
               (' ' + str(self.patron) if len(self.patron) > 0 else '')

    def normalize(self):
        done_flag = False
        surn_subj = Subject(self.surname.word)
        name_subj = (Subject(self.name.word) if not self.name.empty else Subject(self.surname.word))
        name_subj2 = (Subject(self.name.word) if not self.name.empty else Subject(self.surname.word))
        patr_subj = (Subject(self.patron.word) if not self.patron.empty else Subject(self.surname.word))
        # res = ''  # str(surn_subj.post) + ' | ' + str(name_subj) + ' | ' + str(patr_subj.post)
        if len(surn_subj.morph_tags) > 0:
            for srn_mt in surn_subj.morph_tags:
                if not done_flag:
                    for nam_mt in name_subj.morph_tags:
                        if not done_flag:
                            for patr_mt in patr_subj.morph_tags:
                                try:
                                    if srn_mt.dict['GNdr'] == nam_mt.dict['GNdr'] == patr_mt.dict['GNdr']:
                                        if srn_mt.dict['CAse'] == nam_mt.dict['CAse'] == patr_mt.dict['CAse']:
                                            self.gndr = srn_mt.dict['GNdr']
                                            self.surname = Word(srn_mt.inflect({'nomn', 'sing'}))
                                            if not self.name.empty:
                                                self.name = Word(nam_mt.inflect({'nomn', 'sing'}))
                                            if not self.patron.empty:
                                                self.patron = Word(patr_mt.inflect({'nomn', 'sing'}))
                                            done_flag = True
                                            break
                                except:
                                    pass
            if not done_flag and self.patron.empty:
                patr_subj = name_subj2
            if not done_flag:
                for nam_mt in name_subj.morph_tags:
                    if not done_flag:
                        for patr_mt in patr_subj.morph_tags:
                            try:
                                if nam_mt.dict['GNdr'] == patr_mt.dict['GNdr']:
                                    if nam_mt.dict['CAse'] == patr_mt.dict['CAse']:
                                        self.gndr = nam_mt.dict['GNdr']
                                        if not self.name.empty:
                                            self.name = Word(nam_mt.inflect({'nomn', 'sing'}))
                                        if not self.patron.empty:
                                            self.patron = Word(patr_mt.inflect({'nomn', 'sing'}))
                                        done_flag = True
                                        break
                            except:
                                pass
        if str(self.patron) == 'Юриевна':
            self.patron = Word('Юрьевна')
        return ''


class NameEntities(SingleTagEntities):

    def __call__(self, samples):
        samples_res = []
        samples_lst = []
        for sample in samples:
            words = tokenize(sample).split(' ')
            skip = 0
            for i in range(len(words)-1):
                if skip == 0:
                    loc_res = ''
                    loc_lst = ['', '', '']
                    if maybe_name(words[i], 'Name', where_from=0) is not None:
                        two_next = list(next_two_elements(words[i+1:], len(words[i])))
                        if maybe_name(two_next[0], 'Patr', where_from=2) is not None:
                            if maybe_name(two_next[1], 'Surn', where_from=3, force_surn=True) is not None:
                                loc_res = ' '.join([words[i]] + two_next)
                                loc_lst = [two_next[1], words[i], two_next[0]]
                                skip = 2
                            else:
                                loc_res = ' '.join([words[i], two_next[0]])
                                loc_lst = ['', words[i], two_next[0]]
                                skip = 1
                        elif maybe_name(two_next[0], 'Surn', where_from=1, force_surn=True) is not None:
                            loc_res = ' '.join([words[i], two_next[0]])
                            loc_lst = [two_next[0], words[i], '']
                            skip = 1
                        else:
                            loc_res = ''
                            loc_lst = ['', '', ''] #words[i]
                            skip = 0
                    elif maybe_name(words[i], 'Surn', where_from=4) is not None:
                        two_next = list(next_two_elements(words[i + 1:], len(words[i])))
                        if maybe_name(two_next[0], 'Name', where_from=5) is not None:
                            if maybe_name(two_next[1], 'Patr', where_from=6) is not None:
                                loc_res = ' '.join([words[i]] + two_next)
                                loc_lst = [words[i], two_next[0], two_next[1]]
                                skip = 2
                            else:
                                loc_res = ' '.join([words[i], two_next[0]])
                                loc_lst = [words[i], two_next[0], '']
                                skip = 1
                        else:
                            loc_res = '' #words[i]
                            loc_lst = ['', '', '']
                    if loc_res not in samples_res and loc_res != '':
                        samples_res.append(loc_res)
                    loc_name = Name(loc_lst)
                    if loc_name not in samples_lst and len(loc_name) > 0:
                        samples_lst.append(loc_name)
                        # print(samples_lst)
                    else:
                        for i in range(len(samples_lst)):
                            # print(str(samples_lst[i]) + ' + ' + str(loc_name) + ' = ' + str(samples_lst[i] + loc_name))
                            samples_lst[i] += loc_name
                else:
                    skip -= 1
        return samples_lst


class Word:

    def __init__(self, word, uppercase=True):
        self.word = word
        self.uppercase = uppercase
        self.empty = len(self.word) == 0
        if self.empty:
            self.punct = ''
            self.short = False
        else:
            if self.word[-1] == '.':
                self.word = self.word[:-1]
            self.short = len(self.word) == 1
            if self.uppercase:
                if self.short:
                    self.word = self.word.upper()
                    self.punct = '.'
                else:
                    self.word = '-'.join([w[0].upper() + w[1:].lower() for w in self.word.split('-')])
                    self.punct = ''
            else:
                self.word = self.word.lower()

    def __eq__(self, other):
        if self.empty or other.empty:
            return True
        else:
            if self.short and other.short:
                return self.word == other.word
            elif not self.short and not other.short:
                w1 = self.word.replace('е', 'ё')
                w2 = other.word.replace('е', 'ё')
                return (w1 in w2 or w2 in w1) and abs(len(w1) - len(w2)) < 2
            elif self.short and not other.short:
                return self.word == other.word[0]
            elif not self.short and other.short:
                return self.word[0] == other.word
            else:
                return False

    def __add__(self, other):
        if (self.empty and not other.empty or self.short and not (other.empty or other.short)) and self == other:
            return Word(other.word)
        elif (other.empty and not self.empty or other.short and not (self.empty or self.short)) and self == other:
            return Word(self.word)
        else:
            return self

    def __len__(self):
        return len(self.word)

    def __repr__(self):
        if self.short:
            return self.word + self.punct
        else:
            return self.word


def name_upper_case(string):
    if len(string) > 1:
        return string[0].upper() + string[1:].lower()
    else:
        return string.upper() + '.'


def merge_names(names, stop_lst=None):
    merged = names
    if stop_lst is None:
        return [str(n) for n in merged]
    else:
        res = []
        for name in merged:
            s_name = Subject(name.surname.word)
            try:
                some_object_iterator = iter(stop_lst)
            except:
                stop_lst = []
            if True not in [r > s_name for r in stop_lst] and not name.surname.empty:
                res.append(name)
        return res
