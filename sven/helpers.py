#!/usr/bin/env python
# -*- coding: utf-8 -*-
import urllib2, json
from django.utils.text import slugify


def uuslug(model, instance, value, max_length=128):
  '''
  return s unique slug string
  '''
  slug = slugify(value)[:max_length] # safe autolimiting
  slug_base = slug
  i = 1;

  while model.objects.exclude(pk=instance.pk).filter(slug=slug).count():
    candidate = '%s-%s' % (slug_base, i)
    if len(candidate) > max_length:
      slug = slug[:max_length-len('-%s' % i)]
    slug = re.sub('\-+','-',candidate)
    i += 1

  return slug



def palette():
  '''
  return a json dict containing a random generate palette.
  first result image, e.g http://www.colourlovers.com/paletteImg/94582D/B97820/F3B503/EA8407/957649/ThePeanuttyProfessor.png
    
    print helper_palette().pop()['imageUrl']
  
  '''
  request = urllib2.Request('http://www.colourlovers.com/api/palettes/random?format=json',
    headers={'User-Agent': "ColourLovers Browser"}
  )
  
  contents = urllib2.urlopen(request).read()
  return json.loads(contents)



def colour():
  '''
  return a json dict containing a random generate color with a generated image.
  first result image, e.g http://www.colourlovers.com/paletteImg/94582D/B97820/F3B503/EA8407/957649/ThePeanuttyProfessor.png
    
    print helper_colour().pop()['hex']
    print helper_colour().pop()['imageUrl'] "hex":"A5CA68"
  
  '''
  request = urllib2.Request('http://www.colourlovers.com/api/colors/random?format=json',
    headers={'User-Agent': "ColourLovers Browser"}
  )
  
  contents = urllib2.urlopen(request).read()
  return json.loads(contents)  


def truncatesmart(value, limit=80):
    """
    Truncates a string after a given number of chars keeping whole words.
    
    Usage as templatetag:
        {{ string|truncatesmart }}
        {{ string|truncatesmart:50 }}
        # Join the words and return
    """
    value = unicode(value).strip() # Make sure it's unicode
    
    if len(value) <= limit:# Return the string itself if length is smaller or equal to the limit
      return value
    
    value = value[:limit] # Cut the string
    words = value.split(' ')[:-1] # Break into words and remove the last
    
    return ' '.join(words) + '...'