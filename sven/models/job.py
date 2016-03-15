#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os, codecs

from sven import helpers
from django.conf import settings
from django.db import models

from sven.models import Corpus, Document

class Job(models.Model):
  STARTED = 'BOO'
  RUNNING = 'RUN'
  LOST = 'RIP'
  COMPLETED = 'END'
  ERROR = 'ERR'

  STATUS_CHOICES = (
    (STARTED, u'started'),
    (RUNNING, u'running'),
    (LOST, u'process not found'),
    (COMPLETED, u'job completed'),  
    (ERROR, u'job error') ,
  )

  pid = models.CharField(max_length=32)
  cmd = models.TextField()
  corpus = models.OneToOneField(Corpus, null=True, related_name='job')
  document = models.ForeignKey(Document, null=True, blank=True) # current working on document...

  status = models.CharField(max_length=3, choices=STATUS_CHOICES, default=STARTED)
  completion = models.FloatField(default='0')

  date_created = models.DateTimeField(auto_now_add=True)
  date_last_modified = models.DateTimeField(auto_now=True)


  def __unicode__(self):
    return '%s [pid=%s]' % (self.corpus.name, self.pid)


  def is_alive(self):
    logger.debug('Checking if a job is already running... ')
    
    try:
      s = subprocess.check_output('ps aux | grep "%s"' % self.cmd, shell=True, close_fds=True).split('\n')
      logger.debug(s)
    except OSError, e:
      logger.exception(e)
      return True
    #print s
    for g in s:
      if re.search(r'\d\s%s' % self.cmd, g) is None:
        logger.debug('no job running with pid=%s' % self.pid)
        return False
    logger.debug('job running... take it easy')
    return True


  @staticmethod
  def is_busy():
    running_jobs = Job.objects.filter(status__in=[Job.RUNNING, Job.STARTED])
    logger.debug('Job.is_busy() : checking already working jobs')
      
    if running_jobs.count() > 0:
      for r in running_jobs:
        if r.is_alive():
          logger.debug('A job is currently running!')
          return True
        else:
          r.status = Job.LOST
          r.save()
      # if reached the end of the loop, all running job found are lost... so Job can do something again!
      logger.debug('closing all previous job, since no one is alive.')
      return False
    else:
      logger.debug('no jobs running...')
      return False


  @staticmethod
  def start(corpus, command='harvest', csv='', popen=True):
    '''
    Check if there are jobs running, otherwise
    Ouptut None or the created job.
    Test with:
    http://localhost:8000/api/corpus/1/start/harvest
    http://localhost:8000/api/corpus/1/start/whoosher
    '''

    # check if there are similar job running...
    #if Job.is_busy():
    #  logger.debug('job is busy %s , you need to wait for your turn...' % command)
    #  return None
    running_jobs = Job.objects.filter(status__in=[Job.RUNNING, Job.STARTED])
    if running_jobs.count() > 0:
      logger.debug('ouch, your corpus is busy in doing something else ...')
      return None
    # creating corpus related job
    job, created = Job.objects.get_or_create(corpus=corpus)
    job.status = Job.RUNNING
    job.completion = 0
    # set as default
    logger.debug('init start "%s"' % command) 
    popen_args = [
      settings.PYTHON_INTERPRETER, # the virtualenv python
      os.path.join(settings.BASE_DIR, 'manage.py'), # local manage script
      'start_job', 
      '--cmd', command,
      '--job', str(job.pk),
      '--csv', str(csv)
    ]

    
    s = subprocess.Popen(popen_args, stdout=None, stderr=None, close_fds=True)
    job.cmd = ' '.join(popen_args)
    logger.debug('cmd "%s"' % job.cmd) 
    job.pid = s.pid
    job.save()

    return job

    print popen_args
    

    if command not in settings.STANDALONE_COMMANDS:
      logger.debug('command "%s" not stored as management command, running start command instead' % command) 
      # cpmmand stored into start
      popen_args = [settings.PYTHON_INTERPRETER, os.path.join(settings.BASE_DIR,'manage.py'), 'start', '--cmd', command, '--corpus']
    else:
      logger.debug('command "%s" popopened' % command) 
      popen_args = [settings.PYTHON_INTERPRETER, os.path.join(settings.BASE_DIR,'manage.py'), command, '--corpus']
    logger.debug('starting cmd "%s"%s' % (command, ' as subprocess' if popen else '' ))
    job, created = Job.objects.get_or_create(corpus=corpus)
    job.status = Job.RUNNING
    job.cmd = ' '.join(popen_args[:-1])
    job.save()

    popen_args.append(str(corpus.id))
    if popen:
      s = subprocess.Popen(popen_args, stdout=None, stderr=None, close_fds=True)
      job.pid = s.pid
    else:
      job.pid = 0

    return job


  def stop(self):
    self.status=Job.COMPLETED
    self.save()
    #if self.pid != 0:
    #  logger.debug('killing pid %s' % int(self.pid))
    #  try:
    #    os.kill(int(self.pid), signal.SIGKILL)
    #  except OSError, e:
    #    logger.exception(e)
    # everything below will not be executed, since the process id has benn killed.


  def json(self, deep=False):
    d = {
      'cmd': self.cmd,
      'completion': self.completion,
      'document': None,
      'id': self.id,
      'pid': self.pid,
      'status': self.status
    }
    return d