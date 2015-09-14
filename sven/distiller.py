#!/usr/bin/env python
# -*- coding: utf-8 -*-
import re, math, logging, urllib, urllib2, json
import pattern.en, pattern.nl, pattern.fr

from pattern.search import search
from pattern.vector import LEMMA, Document as PatternDocument
from pattern.web import PDF
logger = logging.getLogger("sven")

NL_STOPWORDS = [u"aan",u"af",u"al",u"alles",u"als",u"altijd",u"andere",u"ben",u"bij",u"daar",u"dan",u"dat",u"de",u"der",u"deze",u"die",u"dit",u"doch",u"doen",u"door",u"dus",u"een",u"eens",u"en",u"er",u"ge",u"geen",u"geweest",u"haar",u"had",u"heb",u"hebben",u"heeft",u"hem",u"het",u"hier",u"hij",u"hij ",u"hoe",u"hun",u"iemand",u"iets",u"ik",u"in",u"is",u"ja",u"je",u"je ",u"kan",u"kon",u"kunnen",u"maar",u"me",u"meer",u"men",u"met",u"mij",u"mijn",u"moet",u"na",u"naar",u"niet",u"niets",u"nog",u"nu",u"of",u"om",u"omdat",u"onder",u"ons",u"ook",u"op",u"over",u"reeds",u"te",u"tegen",u"toch",u"toen",u"tot",u"u",u"uit",u"uw",u"van",u"veel",u"voor",u"want",u"waren",u"was",u"wat",u"we",u"wel",u"werd",u"wezen",u"wie",u"wij",u"wil",u"worden",u"wordt",u"zal",u"ze",u"zei",u"zelf",u"zich",u"zij",u"zijn",u"zo",u"zonder",u"zou"]
EN_STOPWORDS = [u"the",u"i",u"me",u"my",u"myself",u"we",u"us",u"our",u"ours",u"ourselves",u"you",u"your",u"yours",u"yourself",u"yourselves",u"he",u"him",u"his",u"himself",u"she",u"her",u"hers",u"herself",u"it",u"its",u"itself",u"they",u"them",u"their",u"theirs",u"themselves",u"what",u"which",u"who",u"whom",u"this",u"that",u"these",u"those",u"am",u"is",u"are",u"was",u"were",u"be",u"been",u"being",u"have",u"has",u"had",u"having",u"do",u"does",u"did",u"doing",u"will",u"would",u"shall",u"should",u"can",u"could",u"may",u"might",u"must",u"ought",u"i'm",u"you're",u"he's",u"she's",u"it's",u"we're",u"they're",u"i've",u"you've",u"we've",u"they've",u"i'd",u"you'd",u"he'd",u"she'd",u"we'd",u"they'd",u"i'll",u"you'll",u"he'll",u"she'll",u"we'll",u"they'll",u"isn't",u"aren't",u"wasn't",u"weren't",u"hasn't",u"haven't",u"hadn't",u"doesn't",u"don't",u"didn't",u"won't",u"wouldn't",u"shan't",u"shouldn't",u"can't",u"cannot",u"couldn't",u"mustn't",u"let's",u"that's",u"who's",u"what's",u"here's",u"there's",u"when's",u"where's",u"why's",u"how's",u"daren't",u"needn't",u"oughtn't",u"mightn't",u"a",u"an",u"the",u"and",u"but",u"if",u"or",u"because",u"as",u"until",u"while",u"of",u"at",u"by",u"for",u"with",u"about",u"against",u"between",u"into",u"through",u"during",u"before",u"after",u"above",u"below",u"to",u"from",u"up",u"down",u"in",u"out",u"on",u"off",u"over",u"under",u"again",u"further",u"then",u"once",u"here",u"there",u"when",u"where",u"why",u"how",u"all",u"any",u"both",u"each",u"few",u"more",u"most",u"other",u"some",u"such",u"no",u"nor",u"not",u"only",u"own",u"same",u"so",u"than",u"too",u"very"]
FR_STOPWORDS = [u"alors",u"au",u"aucuns",u"un", u"une",u"aussi",u"autre",u"avant",u"avec",u"avoir",u"bon",u"car",u"ce",u"cela",u"ces",u"ceux",u"chaque",u"ci",u"comme",u"comment",u"dans",u"des",u"du",u"dedans",u"dehors",u"depuis",u"deux",u"devrait",u"doit",u"donc",u"dos",u"droite",u"début",u"elle",u"elles",u"en",u"encore",u"essai",u"est",u"et",u"eu",u"fait",u"faites",u"fois",u"font",u"force",u"haut",u"hors",u"ici",u"il",u"ils",u"je  juste",u"la",u"le",u"les",u"leur",u"là",u"ma",u"maintenant",u"mais",u"mes",u"mine",u"moins",u"mon",u"mot",u"même",u"ni",u"nommés",u"notre",u"nous",u"nouveaux",u"ou",u"où",u"par",u"parce",u"parole",u"pas",u"personnes",u"peut",u"peu",u"pièce",u"plupart",u"pour",u"pourquoi",u"quand",u"que",u"quel",u"quelle",u"quelles",u"quels",u"qui",u"sa",u"sans",u"ses",u"seulement",u"si",u"sien",u"son",u"sont",u"sous",u"soyez sujet",u"sur",u"ta",u"tandis",u"tellement",u"tels",u"tes",u"ton",u"tous",u"tout",u"trop",u"très",u"tu",u"valeur",u"voie",u"voient",u"vont",u"votre",u"vous",u"vu",u"ça",u"étaient",u"état",u"étions",u"été",u"être"]
IT_STOPWORDS = [u'a',u'abbastanza',u'accidenti',u'ad',u'adesso',u'affinche',u'agli',u'ahime',u'ahimè',u'ai',u'al',u'alcuna',u'alcuni',u'alcuno',u'all',u'alla',u'alle',u'allo',u'allora',u'altre',u'altri',u'altrimenti',u'altro',u'altrui',u'anche',u'ancora',u'anni',u'anno',u'ansa',u'assai',u'attesa',u'avanti',u'avendo',u'avente',u'aver',u'avere',u'avete',u'aveva',u'avevano',u'avuta',u'avute',u'avuti',u'avuto',u'basta',u'ben',u'bene',u'benissimo',u'berlusconi',u'brava',u'bravo',u'buono',u'c',u'casa',u'caso',u'cento',u'certa',u'certe',u'certi',u'certo',u'che',u'chi',u'chicchessia',u'chiunque',u'ci',u'ciascuna',u'ciascuno',u'cima',u'cinque',u'cio',u'cioe',u'cioè',u'circa',u'citta',u'città',u'ciò',u'codesta',u'codesti',u'codesto',u'cogli',u'coi',u'col',u'colei',u'coll',u'coloro',u'colui',u'come',u'comprare',u'con',u'concernente',u'consecutivi',u'consecutivo',u'consiglio',u'contro',u'cortesia',u'cos',u'cosa',u'cosi',u'così',u'cui',u'd',u'da',u'dagli',u'dai',u'dal',u'dall',u'dalla',u'dalle',u'dallo',u'davanti',u'degli',u'dei',u'del',u'dell',u'della',u'delle',u'dello',u'dentro',u'detto',u'deve',u'devo',u'di',u'dice',u'dietro',u'dire',u'dirimpetto',u'dopo',u'doppio',u'dove',u'dovra',u'dovrà',u'due',u'dunque',u'durante',u'e',u'ecco',u'ed',u'egli',u'ella',u'eppure',u'era',u'erano',u'esse',u'essendo',u'esser',u'essere',u'essi',u'ex',u'fa',u'fare',u'fatto',u'favore',u'fin',u'finalmente',u'finche',u'fine',u'fino',u'forse',u'fra',u'fuori',u'gente',u'gia',u'giacche',u'giorni',u'giorno',u'giu',u'già',u'gli',u'gliela',u'gliele',u'glieli',u'glielo',u'gliene',u'governo',u'grande',u'grazie',u'gruppo',u'ha',u'hai',u'hanno',u'ho',u'i',u'ieri',u'il',u'improvviso',u'in',u'indietro',u'infatti',u'insieme',u'intanto',u'intorno',u'invece',u'io',u'l',u'la',u'lavoro',u'le',u'lei',u'li',u'lo',u'lontano',u'loro',u'lui',u'lungo',u'là',u'ma',u'macche',u'magari',u'mai',u'male',u'malgrado',u'malissimo',u'me',u'medesimo',u'mediante',u'meglio',u'meno',u'mentre',u'mesi',u'mezzo',u'mi',u'mia',u'mie',u'miei',u'mila',u'miliardi',u'milioni',u'ministro',u'mio',u'molta',u'molti',u'moltissimo',u'molto',u'mondo',u'nazionale',u'ne',u'negli',u'nei',u'nel',u'nell',u'nella',u'nelle',u'nello',u'nemmeno',u'neppure',u'nessuna',u'nessuno',u'niente',u'no',u'noi',u'nome',u'non',u'nondimeno',u'nostra',u'nostre',u'nostri',u'nostro',u'nove',u'nulla',u'nuovi',u'nuovo',u'o',u'od',u'oggi',u'ogni',u'ognuna',u'ognuno',u'oltre',u'oppure',u'ora',u'ore',u'osi',u'ossia',u'otto',u'paese',u'parecchi',u'parecchie',u'parecchio',u'parte',u'partendo',u'peccato',u'peggio',u'per',u'perche',u'perchè',u'percio',u'perciò',u'perfino',u'pero',u'persone',u'però',u'piedi',u'pieno',u'piglia',u'piu',u'più',u'po',u'pochissimo',u'poco',u'poi',u'poiche',u'press',u'prima',u'primo',u'promesso',u'proprio',u'puo',u'pure',u'purtroppo',u'può',u'qua',u'qualche',u'qualcuna',u'qualcuno',u'quale',u'quali',u'qualunque',u'quando',u'quanta',u'quante',u'quanti',u'quanto',u'quantunque',u'quarto',u'quasi',u'quattro',u'quel',u'quella',u'quelli',u'quello',u'quest',u'questa',u'queste',u'questi',u'questo',u'qui',u'quindi',u'quinto',u'riecco',u'rispetto',u'salvo',u'sara',u'sarebbe',u'sarà',u'scopo',u'scorso',u'se',u'secondo',u'seguente',u'sei',u'sembra',u'sembrava',u'sempre',u'senza',u'sette',u'si',u'sia',u'siamo',u'siete',u'solito',u'solo',u'sono',u'sopra',u'soprattutto',u'sotto',u'sta',u'staranno',u'stata',u'state',u'stati',u'stato',u'stesso',u'su',u'sua',u'subito',u'successivo',u'sue',u'sugli',u'sui',u'sul',u'sull',u'sulla',u'sulle',u'sullo',u'suo',u'suoi',u'tale',u'talvolta',u'tanto',u'te',u'tempo',u'terzo',u'ti',u'torino',u'tra',u'tranne',u'tre',u'triplo',u'troppo',u'tu',u'tua',u'tue',u'tuo',u'tuoi',u'tutta',u'tuttavia',u'tutte',u'tutti',u'tutto',u'uguali',u'ultimo',u'un',u'una',u'uno',u'uomo',u'va',u'vai',u'vale',u'varia',u'varie',u'vario',u'verso',u'vi',u'via',u'vicino',u'visto',u'vita',u'voi',u'volta',u'volte',u'vostra',u'vostre',u'vostri',u'vostro',u'è']


def tf_filter(tf):
  return float(tf) > 0.0



def dictfetchall(cursor):
    "Returns all rows from a cursor as a dict"
    desc = cursor.description
    return [
      dict(zip([col[0] for col in desc], row))
      for row in cursor.fetchall()
    ]



def dry(content):
  '''
  Return a purged, celaned text. Try into test.
  '''
  #content = content.replace("’", "'")
  #content = content.replace(u' ', u' ')# strange space char
  return content



def distill(content="",language="en", stopwords=EN_STOPWORDS, query='NP'):
  '''
  Return a list of tuples: [("NP", "NPlemmata"),]
  '''
  language=language.lower()

  p = re.compile(ur'[^a-zA-ZàâäôéèëêïîçùûüÿæœÀÂÄÔÉÈËÊÏÎŸÇÙÛÜÆŒäöüßÄÖÜẞąćęłńóśźżĄĆĘŁŃÓŚŹŻàèéìíîòóùúÀÈÉÌÍÎÒÓÙÚáéíñóúüÁÉÍÑÓÚÜ]')

  try:
    
    if language == "nl":
      text = pattern.nl.Text( pattern.nl.parse(content, lemmata=True))
    elif language == "fr":
      text = pattern.fr.Text( pattern.fr.parse(content, lemmata=True))
    elif language == "it":
      text = pattern.it.Text( pattern.it.parse(content, lemmata=True))
    elif language == "es":
      text = pattern.es.Text( pattern.es.parse(content, lemmata=True))
    else:
      text = pattern.en.Text( pattern.en.parse(content, lemmata=True))
  except UnicodeWarning, e:
    logger.exception(e)

  pattern_document = PatternDocument(content, language=language, exclude=stopwords, stemmer=LEMMA)
  
  sentences = [search(query, s) for s in text]
  segments = {}
  tuples = []
  total_segments = 0.0;

  for sentence in sentences:
    for match in sentence:
      lemmas = []
      words = []

      for word in match.words:
        print word
        word.lemma = p.sub('', word.lemma)
        if len( word.lemma ) < 2 :
          continue
        if p.match(word.lemma):
          continue
        if word.lemma in stopwords:
          continue
        lemmas.append(word.lemma)
        words.append(word)

      if len(words):
        print [pattern_document.tf(l.lemma) for l in words]
        # tfs = filter(tf_filter, [pattern_document.tf(l.lemma) for l in words]) # let's use pattern calculation
        # tf = sum(tfs)/float(len(tfs)) if len(tfs) > 0 else 0.0
        # wf = math.log(tf+1.0, 2) if tf > 0.0 else 0.0
        key = ' '.join(sorted(set(lemmas)))
        if not key in segments:
          segments[u''+key] = {
            's':  match.string, 
            'l':  key,
            'c': 0.0
          }
          total_segments+= 1.0

        segments[key]['c'] = segments[key]['c'] + 1.0

        # segments.append((match.string, ' '.join(sorted(set(lemmas))), tf, wf))

  for segment in segments.items():
    print segment
    tf = segment[1]['c'] / total_segments
    wf = math.log(tf+1.0, 2) if tf > 0.0 else 0.0
    tuples.append((segment[1]['s'], segment[1]['l'], tf, wf))

  return tuples



def evaporate(segments):
  '''
  Take the result of distill and count lemmata duplicates.
  '''
  uniques = {}

  for i, (match, lemmata) in enumerate(segments):
    if lemmata not in uniques:
      uniques[lemmata] = []
    uniques[lemmata].append(match) # various forms

  return uniques
  pass



def pdftotext(path):
  '''
  try to get the text from a pdf file (pattern module)
  @param path from
  @param to
  '''
  import codecs
  with codecs.open(path, "r" ) as source:
    content = PDF(source).string
  return content


def gooseapi(url):
  '''
  Return a goose instance (with title and content only) for a specific url provided.
  '''
  from goose import Goose
  goo = Goose({'enable_image_fetching':False})
  opener = urllib2.build_opener(urllib2.HTTPCookieProcessor())
  opener.addheaders = [('User-agent', 'User-Agent:Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/38.0.2125.122 Safari/537.36'), ('Accept', '*/*')]
  response = opener.open(url)
  raw_html = response.read()
  return goo.extract(raw_html=raw_html)



def freebase(api_key, query, lang):
  '''
  return some dummy tuple of "notable" id and result id in the freebase format.
  Because we do not have a context, we will provide filtering mechanism somehow later.
  Try Londres in FR. THe second notable is "Olympic Games" :D
  we do not store anything else..!

  Test from shell:
from sven.distiller import freebase
from django.conf import settings
  
freebase(query="Londres", api_key=settings.FREEBASE_KEY, lang='fr')
  '''
  if api_key is None:
    return None

  request = urllib2.Request(
    'https://www.googleapis.com/freebase/v1/search?query=%s&key=%s&lang=%s&stemmed=true' % (
      query,
      api_key,
      lang
    ), headers={'User-Agent': "Freebase for Sven"}
  )
  try:
    contents = urllib2.urlopen(request).read()
    j  = json.loads(contents)
  except Exception, e:
    logger.exception(e)
    return None
  else:
    results = []
    # print j
    if j['result']:
      results = ((res['notable']['id'], res['id']) for res in j['result'] if 'notable' in res and 'id' in res)
    else:
      logger.error(j['status'], contents)
    return results



def textrazor(api_key, text, service='entities'):
  if api_key is None:
    return None

  request = urllib2.Request(url='http://api.textrazor.com',
    data=urllib.urlencode({
      'apiKey': api_key,
      'extractors' : service,
      'text': text.encode('utf8')
    }),
    headers={
      #'Content-type': "application/x-www-form-urlencoded",
    }
  )

  contents = urllib2.urlopen(request).read()
  return json.loads(contents)  



def alchemyapi(api_key, text, service='TextGetRankedNamedEntities'):
  '''
  Note that text should be utf8 string.
  '''
  if api_key is None:
    return None

  request = urllib2.Request(url='http://access.alchemyapi.com/calls/text/%s' % service,
    data=urllib.urlencode({
      'outputMode': 'json',
      'apikey': api_key,
      'text': text.encode('utf8')
    }),
    headers={
      'User-Agent': "AlchemyAPI for Sven",
      'Content-type': "application/x-www-form-urlencoded",
    }
  )
  
  contents = urllib2.urlopen(request).read()
  return json.loads(contents)  



def alchemyapi_url(api_key, url, service='URLGetText'):
  if api_key is None:
    return None

  request = urllib2.Request(url='http://access.alchemyapi.com/calls/url/%s' % service,
    data=urllib.urlencode({
      'outputMode': 'json',
      'apikey': api_key,
      'url': url
    }),
    headers={
      'User-Agent': "AlchemyAPI for Sven",
      'Content-type': "application/x-www-form-urlencoded",
    }
  )
  
  contents = urllib2.urlopen(request).read()
  return json.loads(contents)  