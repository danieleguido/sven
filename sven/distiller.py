#!/usr/bin/env python
# -*- coding: utf-8 -*-
import math, logging
import pattern.en, pattern.nl, pattern.fr
from pattern.search import search
from pattern.vector import LEMMA, Document as PatternDocument

logger = logging.getLogger("sven")

NL_STOPWORDS = [u"aan",u"af",u"al",u"alles",u"als",u"altijd",u"andere",u"ben",u"bij",u"daar",u"dan",u"dat",u"de",u"der",u"deze",u"die",u"dit",u"doch",u"doen",u"door",u"dus",u"een",u"eens",u"en",u"er",u"ge",u"geen",u"geweest",u"haar",u"had",u"heb",u"hebben",u"heeft",u"hem",u"het",u"hier",u"hij",u"hij ",u"hoe",u"hun",u"iemand",u"iets",u"ik",u"in",u"is",u"ja",u"je",u"je ",u"kan",u"kon",u"kunnen",u"maar",u"me",u"meer",u"men",u"met",u"mij",u"mijn",u"moet",u"na",u"naar",u"niet",u"niets",u"nog",u"nu",u"of",u"om",u"omdat",u"onder",u"ons",u"ook",u"op",u"over",u"reeds",u"te",u"tegen",u"toch",u"toen",u"tot",u"u",u"uit",u"uw",u"van",u"veel",u"voor",u"want",u"waren",u"was",u"wat",u"we",u"wel",u"werd",u"wezen",u"wie",u"wij",u"wil",u"worden",u"wordt",u"zal",u"ze",u"zei",u"zelf",u"zich",u"zij",u"zijn",u"zo",u"zonder",u"zou"]
EN_STOPWORDS = [u"i",u"me",u"my",u"myself",u"we",u"us",u"our",u"ours",u"ourselves",u"you",u"your",u"yours",u"yourself",u"yourselves",u"he",u"him",u"his",u"himself",u"she",u"her",u"hers",u"herself",u"it",u"its",u"itself",u"they",u"them",u"their",u"theirs",u"themselves",u"what",u"which",u"who",u"whom",u"this",u"that",u"these",u"those",u"am",u"is",u"are",u"was",u"were",u"be",u"been",u"being",u"have",u"has",u"had",u"having",u"do",u"does",u"did",u"doing",u"will",u"would",u"shall",u"should",u"can",u"could",u"may",u"might",u"must",u"ought",u"i'm",u"you're",u"he's",u"she's",u"it's",u"we're",u"they're",u"i've",u"you've",u"we've",u"they've",u"i'd",u"you'd",u"he'd",u"she'd",u"we'd",u"they'd",u"i'll",u"you'll",u"he'll",u"she'll",u"we'll",u"they'll",u"isn't",u"aren't",u"wasn't",u"weren't",u"hasn't",u"haven't",u"hadn't",u"doesn't",u"don't",u"didn't",u"won't",u"wouldn't",u"shan't",u"shouldn't",u"can't",u"cannot",u"couldn't",u"mustn't",u"let's",u"that's",u"who's",u"what's",u"here's",u"there's",u"when's",u"where's",u"why's",u"how's",u"daren't",u"needn't",u"oughtn't",u"mightn't",u"a",u"an",u"the",u"and",u"but",u"if",u"or",u"because",u"as",u"until",u"while",u"of",u"at",u"by",u"for",u"with",u"about",u"against",u"between",u"into",u"through",u"during",u"before",u"after",u"above",u"below",u"to",u"from",u"up",u"down",u"in",u"out",u"on",u"off",u"over",u"under",u"again",u"further",u"then",u"once",u"here",u"there",u"when",u"where",u"why",u"how",u"all",u"any",u"both",u"each",u"few",u"more",u"most",u"other",u"some",u"such",u"no",u"nor",u"not",u"only",u"own",u"same",u"so",u"than",u"too",u"very"]
FR_STOPWORDS = [u"alors",u"au",u"aucuns",u"un", u"une",u"aussi",u"autre",u"avant",u"avec",u"avoir",u"bon",u"car",u"ce",u"cela",u"ces",u"ceux",u"chaque",u"ci",u"comme",u"comment",u"dans",u"des",u"du",u"dedans",u"dehors",u"depuis",u"deux",u"devrait",u"doit",u"donc",u"dos",u"droite",u"début",u"elle",u"elles",u"en",u"encore",u"essai",u"est",u"et",u"eu",u"fait",u"faites",u"fois",u"font",u"force",u"haut",u"hors",u"ici",u"il",u"ils",u"je  juste",u"la",u"le",u"les",u"leur",u"là",u"ma",u"maintenant",u"mais",u"mes",u"mine",u"moins",u"mon",u"mot",u"même",u"ni",u"nommés",u"notre",u"nous",u"nouveaux",u"ou",u"où",u"par",u"parce",u"parole",u"pas",u"personnes",u"peut",u"peu",u"pièce",u"plupart",u"pour",u"pourquoi",u"quand",u"que",u"quel",u"quelle",u"quelles",u"quels",u"qui",u"sa",u"sans",u"ses",u"seulement",u"si",u"sien",u"son",u"sont",u"sous",u"soyez sujet",u"sur",u"ta",u"tandis",u"tellement",u"tels",u"tes",u"ton",u"tous",u"tout",u"trop",u"très",u"tu",u"valeur",u"voie",u"voient",u"vont",u"votre",u"vous",u"vu",u"ça",u"étaient",u"état",u"étions",u"été",u"être"]



def tf_filter(tf):
  return float(tf) > 0.0



def dry(content):
  '''
  Return a purged, celaned text. Try into test.
  '''
  content = content.replace("’", "'")
  content = content.replace(r' ', r' ')# strange space char
  return content



def distill(content="",language="en", stopwords=EN_STOPWORDS, query='NP'):
  '''
  Return a list of tuples: [("NP", "NPlemmata"),]
  '''
  language=language.lower()

  try:
    pattern_document = PatternDocument(content, language=language, exclude=stopwords, stemmer=LEMMA)
  
    if language == "nl":
      text = pattern.nl.Text( pattern.nl.parse(content, lemmata=True))
    elif language == "fr":
      text = pattern.fr.Text( pattern.fr.parse(content, lemmata=True))
    else:
      text = pattern.en.Text( pattern.en.parse(content, lemmata=True))
  except UnicodeWarning, e:
    logger.exception(e)

  sentences = [search(query, s) for s in text]
  segments = []

  for sentence in sentences:
    for match in sentence:
      words = []
      for word in match.words:
        if len( word.lemma ) < 2 :
          continue

        if word.lemma in stopwords:
          continue
        words.append(word.lemma)

      if len(words):
        tfs = filter(tf_filter, [pattern_document.tf(l) for l in words]) # let's use pattern calculation
        tf = sum(tfs)/float(len(tfs)) if len(tfs) > 0 else 0.0
        wf = math.log(tf+1.0, 2) if tf > 0.0 else 0.0
        segments.append((match.string, ' '.join(sorted(set(words))), tf, wf))

  return segments



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