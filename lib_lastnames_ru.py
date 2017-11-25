# https://bitbucket.org/kmike/pymorphy

#-*- coding: UTF-8
from __future__ import unicode_literals
import re


NOUNS = ('NOUN', 'С',)
PRONOUNS = ('PN', 'МС',)
PRONOUNS_ADJ = ('PN_ADJ', 'МС-П',)
VERBS = ('Г', 'VERB',  'ИНФИНИТИВ',)
ADJECTIVE = ('ADJECTIVE', 'П',)

PRODUCTIVE_CLASSES = NOUNS + VERBS + ADJECTIVE + ('Н',)

#род
RU_GENDERS_STANDARD = {
    'мр': 'm',
    'жр': 'f',
    'ср': 'n',
    'мр-жр': '', #FIXME: ?
}

# падежи
RU_CASES_STANDARD = {
    'им': 'nom',
    'рд': 'gen',
    'дт': 'dat',
    'вн': 'acc',
    'тв': 'ins',
    'пр': 'loc',
    'зв': 'voc',
}

# числа
RU_NUMBERS_STANDARD = {'ед': 'sg', 'мн': 'pl'}

# лица
RU_PERSONS_STANDARD = {'1л': '1p', '2л': '2p', '3л': '3p'}

# времена
RU_TENSES_STANDARD = {
    'нст': 'pres',
    'прш': 'past',
    'буд': 'pres',          #FIXME: ?
}

# залоги
RU_VOICES_STANDARD = {'дст': 'act', 'стр': 'pass'}

# части речи

RU_CLASSES_STANDARD = {
    'С':              'S',
    'П':              'A',
    'МС':             '-',
    'Г' :             'V',
    'ПРИЧАСТИЕ' :     'V',
    'ДЕЕПРИЧАСТИЕ' :  'V',
    'ИНФИНИТИВ':      'V',
    'МС-ПРЕДК':       '-',
    'МС-П':           '-',
    'ЧИСЛ':           '-',
    'ЧИСЛ-П':         '-',
    'Н':              'ADV',
    'ПРЕДК':          '-',
    'ПРЕДЛ':          'PR',
    'СОЮЗ':           'CONJ',
    'МЕЖД':           'ADV',
    'ЧАСТ':           'ADV',
    'ВВОДН':          'ADV',
    'КР_ПРИЛ':        'A',
    'КР_ПРИЧАСТИЕ':   'V',  #FIXME: ?
    'ПОСЛ':           '-',
    'ФРАЗ':           '-',
}

# старые обозначения
RU_GENDERS = RU_GENDERS_STANDARD.keys()
RU_CASES = RU_CASES_STANDARD.keys()
RU_NUMBERS = RU_NUMBERS_STANDARD.keys()
RU_PERSONS = RU_PERSONS_STANDARD.keys()
RU_TENSES = RU_TENSES_STANDARD.keys()
RU_VOICES = RU_VOICES_STANDARD.keys()

RU_ANIMACY = ['од', 'но']  # для этого стандартных обозначений нет

RU_GRAMINFO_STANDARD = dict(list(RU_GENDERS_STANDARD.items()) + list(RU_CASES_STANDARD.items()) +\
                            list(RU_NUMBERS_STANDARD.items()) + list(RU_PERSONS_STANDARD.items()) + \
                            list(RU_TENSES_STANDARD.items()) + list(RU_VOICES_STANDARD.items()))

# данные для упрощения преобразования причастий, деепричастий и инфинитивов в глагол
RU_GRAMINFO_STANDARD.update({'partcp': 'partcp', 'ger': 'ger', 'inf': 'inf'})

# прочие преобразования
RU_GRAMINFO_STANDARD.update({'сравн': 'comp', 'прев': 'supr', 'пвл': 'imper'})

def _parse_gram_str(form_string):
    splitted = form_string.split(',')
    form = [a for a in splitted if a and a[0]!='!']
    denied_form = [a[1:] for a in splitted if a and a[0]=='!']
    return set(form), set(denied_form)

class GramForm(object):
    """ Класс для работы с грамматической формой """

    def __init__(self, form_string):
        self.form, self.denied_form = _parse_gram_str(form_string)

    def get_form_string(self):
        return ",".join(self.form)

    def clear_number(self):
        ''' убрать информацию о числе '''
        self.form.difference_update(RU_NUMBERS)
        return self

    def clear_case(self):
        ''' убрать информацию о падеже '''
        self.form.difference_update(RU_CASES)
        return self

    def clear_gender(self):
        ''' убрать информацию о роде '''
        self.form.difference_update(RU_GENDERS)
        return self

    def clear_person(self):
        ''' убрать информацию о лице '''
        self.form.difference_update(RU_PERSONS)
        return self

    def clear_tense(self):
        ''' убрать информацию о времени '''
        self.form.difference_update(RU_TENSES)
        return self

    def clear_voice(self):
        ''' убрать информацию о залоге '''
        self.form.difference_update(RU_VOICES)
        return self

    def clear_animacy(self):
        ''' убрать информацию о одушевленности '''
        self.form.difference_update(RU_ANIMACY)

    def update(self, form_string):
        """ Обновляет параметры, по возможности оставляя все, что можно. """
        requested_form = [a for a in form_string.split(',') if a and a[0]!='!']

        for item in requested_form:

            if item in RU_NUMBERS:
                self.clear_number()
                if item=='мн':
                    self.clear_gender()

            if item in RU_CASES:
                self.clear_case()

            if item in RU_GENDERS:
                self.clear_gender()

            if item in RU_TENSES:
                self.clear_tense()
                if item != "нст":
                    self.clear_person()
                if item != "прш":
                    self.clear_gender()

            if item in RU_PERSONS:
                self.clear_person()

            if item in RU_VOICES:
                self.clear_voice()

            if item in RU_ANIMACY:
                self.clear_animacy()

            if item == 'сравн':
                self.clear_case()
                self.clear_number()
                self.clear_gender()

        self.form.update(requested_form)
        return self

    def match(self, gram_form):
        if not self.form.issuperset(gram_form.form): # не все параметры из gram_form есть тут
            return False
        if self.form.intersection(gram_form.denied_form):
            return False
        return True

    def match_string(self, str_form):
        return str_form if self.match(GramForm(str_form)) else None

# Порядок важен: ЯНЦ должно быть перед ЯН для правильного срабатывания.
LASTNAME_PATTERN = re.compile(r'(.*('
    r'ОВ|ИВ|ЕВ'
    r'|ИН'
    r'|СК|ЦК'
    r'|ИЧ'
    r'|ЮК|УК'
    r'|ИС|ЭС|УС'
    r'|ЫХ|ИХ'
    r'|ЯНЦ|ЕНЦ|АН|ЯН'
    # Фамилии без явного суффикса (-ок, -ия, -иа) сюда включать не надо - decline() попытается угадать лемму.
    # Несклоняемые фамилии включать так же не надо - у них нет игнорируемой части после суффикса.
    # Фамилии с суффиксами -ых/-их включены сюда т.к. эти окончания образуют множ. форму CASES_OV
    r'))',
    re.UNICODE | re.VERBOSE)

# XXX: Й тут нет сознательно?
CONSONANTS = 'БВГДЖЗКЛМНПРСТФХЦЧШЩ'

# http://www.gramota.ru/spravka/letters/?rub=rubric_482
# http://planeta-imen.narod.ru/slovar-smolenskich-familij/struktura-familij.html

# 13.1.1, 13.1.3
CASES_OV = {
    'мр': ('', 'А', 'У', 'А', 'ЫМ', 'Е'),
    'жр': ('А', 'ОЙ', 'ОЙ', 'У', 'ОЙ', 'ОЙ'),
}
# 13.1.2
CASES_SK = {
    'мр': ('ИЙ', 'ОГО', 'ОМУ', 'ОГО', 'ИМ', 'ОМ'),
    'жр': ('АЯ', 'ОЙ', 'ОЙ', 'УЮ', 'ОЙ', 'ОЙ'),
}
# Белорусские фамилии на -ич, украинские на -ук, -юк
CASES_CH = {
    'мр': ('', 'А', 'У', 'А', 'ЕМ', 'Е'),
    'жр': ('', '', '', '', '', ''),
}
# Фамилии заканчивающиеся на -ок
CASES_OK = {
    'мр': ('ОК', 'КА', 'КУ', 'КА', 'КОМ', 'КЕ'),
    'жр': ('ОК', 'ОК', 'ОК', 'ОК', 'ОК', 'ОК'),
}
# Фамилии заканчивающиеся на -ец
CASES_EC = {
    'мр': ('ЕЦ', 'ЦА', 'ЦУ', 'ЦА', 'ЦОМ', 'ЦЕ'),
    'жр': ('ЕЦ', 'ЕЦ', 'ЕЦ', 'ЕЦ', 'ЕЦ', 'ЕЦ'),
}
# Литовские, эстонские, часть армянских
CASES_IS = {
    'мр': ('', 'А', 'У', 'А', 'ОМ', 'Е'),
    'жр': ('', '', '', '', '', ''),
}
# 13.1.12 (not really)
CASES_IA = {
    'мр': ('ИЯ', 'ИЮ', 'ИИ', 'ИЮ', 'ИЕЙ', 'ИИ'),
    'жр': ('ИЯ', 'ИЮ', 'ИИ', 'ИЮ', 'ИЕЙ', 'ИИ'),
}
# 13.1.6, 13.1.10
INDECLINABLE_CASES = {
    'мр': ('', '', '', '', '', ''),
    'жр': ('', '', '', '', '', ''),
}

# Склонение в множественную форму: общие суффиксы для обоих родов

# Множественная форма для CASES_OV
PLURAL_OV = ('Ы', 'ЫХ', 'ЫМ', 'ЫХ', 'ЫМИ', 'ЫХ')
# для CASES_SK
PLURAL_SK = ('ИЕ', 'ИХ', 'ИМ', 'ИХ', 'ИМИ', 'ИХ')
# для CASES_OK
PLURAL_OK = ('КИ', 'КОВ', 'КАМ', 'КОВ', 'КАМИ', 'КАХ')
# для CASES_EC
PLURAL_EC = ('ЦЫ', 'ЦОВ', 'ЦАМ', 'ЦОВ', 'ЦАМИ', 'ЦАХ')
# для INDECLINABLE_CASES (и фамилий которые не склоняются во множ. числе)
PLURAL_INDECLINABLE_CASES = ('', '', '', '', '', '')

# Суффикс -> (Склонение единственной формы, Склонение множественной формы)
CASEMAP = {
    'ОВ': (CASES_OV, PLURAL_OV),
    'ИВ': (CASES_OV, PLURAL_OV),
    'ЕВ': (CASES_OV, PLURAL_OV),
    'ИН': (CASES_OV, PLURAL_OV),
    'СК': (CASES_SK, PLURAL_SK),
    'ЦК': (CASES_SK, PLURAL_SK),
    'ИЧ': (CASES_CH, PLURAL_INDECLINABLE_CASES),
    'ЮК': (CASES_CH, PLURAL_INDECLINABLE_CASES),
    'УК': (CASES_CH, PLURAL_INDECLINABLE_CASES),
    'ИС': (CASES_IS, PLURAL_INDECLINABLE_CASES),
    'ЭС': (CASES_IS, PLURAL_INDECLINABLE_CASES),
    'УС': (CASES_IS, PLURAL_INDECLINABLE_CASES),
    # Часть армянских фамилий склоняется так же как литовские
    'АН': (CASES_IS, PLURAL_INDECLINABLE_CASES),
    'ЯН': (CASES_IS, PLURAL_INDECLINABLE_CASES),
    # Другая часть армянских фамилий склоняется как украинские
    # заканчивающиеся на ИЧ
    'УНЦ': (CASES_CH, PLURAL_INDECLINABLE_CASES),
    'ЯНЦ': (CASES_CH, PLURAL_INDECLINABLE_CASES),
    'ЕНЦ': (CASES_CH, PLURAL_INDECLINABLE_CASES),
    'ИЯ': (CASES_IA, PLURAL_INDECLINABLE_CASES),
    'ОК': (CASES_OK, PLURAL_OK),
    # Склонение -ец похоже на фамилии с суффиксом -ок
    'ЕЦ': (CASES_EC, PLURAL_EC),
    'ЫХ': (INDECLINABLE_CASES, PLURAL_INDECLINABLE_CASES),
    'ИХ': (INDECLINABLE_CASES, PLURAL_INDECLINABLE_CASES),
    'КО': (INDECLINABLE_CASES, PLURAL_INDECLINABLE_CASES),
    'АГО': (INDECLINABLE_CASES, PLURAL_INDECLINABLE_CASES),
    'ЯГО': (INDECLINABLE_CASES, PLURAL_INDECLINABLE_CASES),
    'ИА': (INDECLINABLE_CASES, PLURAL_INDECLINABLE_CASES),
    'ХНО': (INDECLINABLE_CASES, PLURAL_INDECLINABLE_CASES),
}


def decline(lastname, gram_form=''):
    ''' Склоняет фамилию и возвращает все возможные формы '''

    # Из фамилии выделяется предполагаемая лемма (Табуретов -> Табуретов,
    # Табуретовым -> Табуретов), лемма склоняется по правилам склонения фамилий

    lastname = lastname.upper()
    def guess_lemma(name):
        '''
        Попытаться угадать сложносклоняемую фамилию (Цапок, Бегунец, Берия)

        Возвращает пару (name=lemma+suffix, lemma) либо (None, None)
        '''

        name_len = len(name)

        # Попытка угадать склонённую фамилию из 13.1.12 ("Берией")
        if name_len > 2 and name[-2:] in ('ИИ', 'ИЮ',):
            return (lastname[:-2] + 'ИЯ', lastname[:-2])
        elif name_len > 3 and name[-3:] in ('ИЕЙ',):
            return (lastname[:-3] + 'ИЯ', lastname[:-3])

        # Попытка угадать склонённую фамилию, закачивающуюся на -ок ("Цапка")
        # Работает, только если буква перед окончанием согласная.
        # Проверка согласной делается для исключения склонённых фамилий на -ак
        # ("Собчака")
        if name_len > 3 and name[-2:] in ('КА', 'КУ', 'КЕ',) and name[-3] in CONSONANTS:
            return (lastname[:-2] + 'ОК', lastname[:-2])
        elif name_len > 4 and name[-3:] in ('КОМ',) and name[-4] in CONSONANTS:
            return (lastname[:-3] + 'ОК', lastname[:-3])

        # Попытка угадать склонённую фамилию, закачивающуюся на -ец ("Бегунец")
        # FIXME: необходима проверка на коллизии с другими фамилиями (как в
        # случае с "Цапок")
        if name_len > 3 and name[-2:] in ('ЦА', 'ЦУ', 'ЦЕ',):
            return (lastname[:-2] + 'ЕЦ', lastname[:-2])

        return (None, None)


    match = LASTNAME_PATTERN.search(lastname)
    lemma = name = match.group(1) if match else lastname # name is lemma + suffix
    name_len = len(name)

    guessed_name, guessed_lemma = guess_lemma(name)
    if guessed_name and guessed_lemma:
        name, lemma = guessed_name, guessed_lemma

    cases, plural_cases = {}, ()
    if name_len > 2:
        cases, plural_cases = CASEMAP.get(name[-2:], ({}, ()))
        if cases:
            lemma = name[:-2]

    if not cases and name_len > 3:
        cases, plural_cases = CASEMAP.get(name[-3:], ({}, ()))
        if cases:
            lemma = name[:-3]

    # В случае 13.1.12 лемма состоит из фамилии, за исключением
    # двух последних букв
    if cases is CASES_IA or cases is CASES_OK:
        lemma = name = name[:-2]

    if not cases:
        return []

    expected_form = GramForm(gram_form)

    forms = []
    for i, case in zip(range(6), ('им', 'рд', 'дт', 'вн', 'тв', 'пр',)):
        for gender_tag in ('мр', 'жр',):
            form = GramForm('%s,%s,фам,ед' % (case, gender_tag,))

            if gram_form and not form.match(expected_form):
                continue

            forms.append({
                'word': '%s%s' % (name, cases[gender_tag][i]),
                'class': 'С',
                'info': form.get_form_string(),
                'lemma': name,
                'method': 'decline_lastname (%s)' % lastname,
                'norm': '%s%s' % (name, cases[gender_tag][0]),
            })

        plural_form = GramForm('%s,мр-жр,фам,мн' % (case,))

        if gram_form and not plural_form.match(expected_form):
            continue

        forms.append({
            'word': '%s%s' % (name, plural_cases[i]),
            'class': 'С',
            'info': plural_form.get_form_string(),
            'lemma': name,
            'method': 'decline_lastname (%s)' % lastname,
            'norm': '%s%s' % (name, plural_cases[0]),
        })

    # Просклонять рекурсивно для случая с множественным числом фамилии.
    # Козловых -> фам,им; Козловых (мн) -> Козлов -> фам,им
    if lemma != name and LASTNAME_PATTERN.match(lemma):
        refinement = decline(lemma)
        if refinement:
            return forms + refinement

    return forms


def normalize(morph, lastname, hints=''):
    '''
    Возвращает нормальную форму (именительный падеж) фамилии для заданного рода

    Параметры:

    * hints - подсказки об исходной форме фамилии ('мр' или 'жр',
      по-умолчанию принимается 'мр')
    '''

    hints_form = GramForm(hints)
    gender_tag = (hints_form.match_string('жр') or 'мр')

    # FIXME: эта функция возвращает саму форму, а Morph.normalize возвращает
    # множество (set) возможных форм, одно из двух лучше поправить.
    return inflect(morph, lastname, 'им,ед,%s' % gender_tag)


def inflect(morph, lastname, gram_form):
    '''
    Вернуть вариант фамилии который соотвествует данной грамматической
    форме

    Параметры:

    * morph - объект Morph
    * lastname - фамилия которую хотим склонять
    * gram_form - желаемые характеристики грам. формы (если 'жр' отсутствует
      в этом параметре, то по-умолчанию принимается 'мр', или 'мр-жр', если
      указано 'мн')
    '''

    lastname = lastname.upper()
    expected_form = GramForm(gram_form)

    gender_tag = ('мр-жр' if expected_form.match_string('мн') else None)
    if not gender_tag:
        gender_tag = (expected_form.match_string('жр') or 'мр')

    # За один проход проверяется, что исходное слово может быть склонено как
    # фамилия и выбирается форма подходящая под gram_form

    present_in_decline = False
    accepted = {}
    for item in decline(lastname):
        form = GramForm(item.get('info', ''))

        # Если в результате склонения не получилось исходной формы - ложное срабатывание

        # Обязательно проверяется род: при склонении в противоположном роде
        # может получиться исходная форма но нас интересует совпадение только в
        # заданном роде

        if item.get('word', '') == lastname:
            # В случае склонения во множественную форму, род игнорируется.
            # Род всех фамилий во множественном числе - мр-жр.
            if expected_form.match_string('мн') or form.match_string(gender_tag):
                present_in_decline = True

        expected = form.match(expected_form)

        if expected and not accepted:
            accepted = item
            # Здесь break не нужен т.к. present_in_decline всё ещё может быть
            # не установлена в корректное значение

    # Если в результате склонения исходной формы не получилось,
    # возвращается результат склонения как для обычного слова

    if present_in_decline and accepted:
        return accepted.get('word', '').lower().capitalize()
    else:
        return morph.parse(lastname)[0].normal_form.capitalize()


def get_graminfo(lastname):
    '''Вернуть грамматическую информацию о фамилии и её нормальную форму'''

    info = []
    for item in decline(lastname):
        if item.get('word', '') == lastname:
            info.append(item)

    return info


def pluralize(morph, lastname, gram_form=''):
    '''
    Вернуть фамилию  во множественном числе.

    Параметры:

    * morph - объект Morph
    * lastname - фамилия которую хотим склонять
    * gram_form - желаемые характеристики грам. формы
    '''

    expected_form = GramForm(gram_form)

    # Удалить из желаемой формы признаки рода и числа
    refined_form = GramForm(gram_form).clear_gender().clear_number()

    # Если дан gram_form - склонить в указанную форму
    if refined_form.get_form_string():
        return inflect(
            morph,
            lastname,
            ','.join((refined_form.get_form_string(), 'мн',)))

    # Иначе - найти форму исходной фамилии и склонить в неё же, но во мн. числе
    # Если в желаемой форме был указан род - использовать как подсказку
    gender_tag = (expected_form.match_string('жр') or 'мр')

    for item in decline(lastname):
        form = GramForm(item.get('info', ''))

        # Проверить наличие исходной формы в заданном роде (аналогично inflect())
        if item.get('word', '') == lastname and form.match_string(gender_tag):
            for case in ('им', 'рд', 'дт', 'вн', 'тв', 'пр'):
                if form.match_string(case):
                    return inflect(morph, lastname, 'мн,%s' % case)

    # В случае неудачи - просклонять как обычное слово
    return morph.pluralize_ru(lastname, gram_form)


def pluralize_inflected(morph, lastname, num, hints=''):
    '''
    Вернуть фамилию в форме, которая будет сочетаться с переданным числом.
    Например: 1 Попугаев, 2 Попугаевых, 5 Попугаевых.

    Параметры:

    * morph - объект Morph
    * lastname - фамилия которую хотим склонять
    * num - число
    * hints - подсказки об исходной форме фамилии ('мр' или 'жр')
    '''

    if num == 1:
        return normalize(morph, lastname, hints)

    hints_form = GramForm(hints)

    gender_tag = (hints_form.match_string('жр') or 'мр')
    return pluralize(morph, lastname, 'мн,рд,%s' % gender_tag)