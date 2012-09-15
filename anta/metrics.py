import os,sys,mimetypes, math, csv
from datetime import datetime


# get path of the django project
path = ("/").join( sys.path[0].split("/")[:-2] )

if path not in sys.path:
    sys.path.append(path)
    
os.environ['DJANGO_SETTINGS_MODULE'] = 'sven.settings'

from django.conf import settings
from django.db import transaction
from optparse import OptionParser
from sven.anta.models import *
from sven.anta.sync import error
from sven.anta.log import log
from sven.anta.distiller import distill, close_routine, log_routine, decant
from sven.anta.utils import *
from sven.core.utils import dictfetchall
from django.db.models import Count, Avg, Max, Min
from django.db import connection, transaction
from pattern.vector import Document as pvDocument, Corpus as pvCorpus

"""
select all stemmed list

SELECT d.id as doc_id, d.language as doc_lang, d.title as doc_title, s.content, s.stemmed as lemmas, ds.tfidf, ds.tf FROM `anta_document_segment` ds JOIN anta_segment s ON s.id = ds.segment_id JOIN anta_document d on d.id = document_id WHERE d.language='EN' ORDER BY `ds`.`tfidf` DESC, lemmas ASC

[document.language]

group by stem


select all with group by stem

SELECT s.content as sample_content, GROUP_CONCAT(s.content) as concat_content, s.stemmed as lemmas, ds.tfidf, MAX( ds.tf ) as max_tf, COUNT( DISTINCT d.id ) as distribution, d.language as doc_lang FROM `anta_document_segment` ds JOIN anta_segment s ON s.id = ds.segment_id JOIN anta_document d on d.id = document_id WHERE d.language='EN' GROUP BY stemmed ORDER BY `ds`.`tfidf` DESC, max_tf DESC
"""

def standard( corpus, routine ):
	
	number_of_documents = Document.objects.filter(corpus=corpus ).count()

	if number_of_documents == 0:
		return close_routine( routine, error="No document found", status="ERR")

	# 1. distiller.decant (tf computation )
	try:
		decant( corpus=corpus, routine=routine, settings=settings, ref_completion=0.5 )
	except Exception, e:
		return close_routine( routine, error="Exception: %s" % e, status="ERR")

	# 2. get all languages in corpus
	try:
		tfidf( corpus=corpus, routine=routine, completion_start=0.5, completion_score=0.5 )
	except Exception, e:
		return close_routine( routine, error="Exception: %s" % e, status="ERR")

	# 3. for each language, perform a tfidf
	routine.completion = 1.0
	routine.save()
	close_routine( routine, error="", status="OK" )

#
#   Trunk Segemnt table little by little...
#
@transaction.commit_manually
def clean( corpus, routine ):
	print """
	========================
	---- CLEAN SEGMENTS ----
	========================
	"""

	number_of_segments = Segment.objects.count()
	loops = int( math.ceil( number_of_segments / 25.0 ) )
	
	print "number_of_segments: %s" % number_of_segments
	print "loops: %s" % loops
	
	try:
		# manually change
		for i in range(0, loops):
			for j in Segment.objects.all()[0:25]:
				j.delete()
				log_routine( routine, completion = float(i) / loops )
					
			transaction.commit()
		log_routine( routine, completion = 1.0 )
				
		
	except Exception, e:
		close_routine( routine, error="Exception: %s" % e, status="ERR")
		transaction.commit()
	
	close_routine( routine, error="", status="OK" )
	transaction.commit()

#
#   Update tf calculation based on stems groups, per corpus basis
# 
@transaction.commit_manually
def tf( corpus, routine, completion_start=0.0, completion_score=1.0 ):
	print """
	======================
	---- TF, RELOADED ----
	======================
	"""
	# change routine type
	routine.type = "TF"
	routine.save()
	transaction.commit()

	# get percentage info:
	number_of_documents_segments = Document_Segment.objects.count()
	print "number_of_documents_segments: %s" % number_of_documents_segments

	if number_of_documents_segments == 0:
		close_routine( routine, error="Not enought segments in your corpus. Try 'standard' routine first...", status="ERR")
		transaction.commit()
		return

	current_segment = 0

	for d in Document.objects.filter(corpus=corpus):
		print "document: %s" % d
		number_of_stems_per_document = Document_Segment.objects.filter( document=d ).values('segment__stemmed').distinct().count()
		print "number_of_stems_per_document: %s" % number_of_stems_per_document

		for ds in Document_Segment.objects.filter( document=d ):
			# count alliases( segment with same stemmed version )
			number_of_aliases = Document_Segment.objects.filter( document=d, segment__stemmed=ds.segment.stemmed ).count()
			ds.tf = float(number_of_aliases) / number_of_stems_per_document
			ds.save()
			if number_of_aliases > 1: # print just some lines
				print  ds.segment.content, ds.segment.stemmed, number_of_aliases, ds.tf
			if current_segment % 25 == 0:
				log_routine( routine, completion = float(current_segment) / number_of_documents_segments )
				transaction.commit()
	

			current_segment = current_segment + 1
			

	close_routine( routine, error="", status="OK" )
	transaction.commit()
	

#
#   Perform tfidf calculation based on stems groups
#  
@transaction.commit_manually
def tfidf( corpus, routine, completion_start=0.0, completion_score=1.0, column="stemmed" ):
	print """
	===========================
	---- TFIDF COMPUTATION ----
	===========================
	"""

	# 1. get number of document
	number_of_documents = Document.objects.filter(corpus=corpus ).count()
	
	# 2. get all languages in corpus
	number_of_languages = Document.objects.values('language').distinct().count()

	# 3. get GLOBAL number of segments (aka stems, segments grouped by their stemmed version: they do not need to be in the same corpus!!!)
	number_of_stems = Segment.objects.values('stemmed', 'language').annotate(Count('stemmed'), Count('language')).count()

	#SELECT COUNT(*), stemmed FROM anta_segment GROUP BY stemmed 

	# out some information
	print "column:",column
	print "corpus:",corpus.json()
	print "document in corpus:",number_of_documents
	print "stems in corpus (grouped by stemmed, language):",number_of_stems

	cursor = connection.cursor()

	# global counter (all languages cycle)
	current_stem = 0

	# 3. for each language, perform a tfidf
	for i in Document.objects.filter(corpus=corpus ).values('language').annotate(num_document=Count('language')).distinct():
		print "language info: ",i
		
		language = i['language']
		# count tfidf group
		# SELECT COUNT(*), stemmed FROM anta_segment WHERE language="EN" GROUP BY stemmed 
		stem_count = Segment.objects.filter(language=language).values('stemmed').annotate(Count('stemmed')).count()
		
		# check length. If it's 0, exit with error....
		if stem_count == 0:
			close_routine( routine, error="Not enought segments in your corpus. Try standard routine first...", status="ERR")
			transaction.commit()
			return 

		# 5. for each segment in this language...
		cursor.execute("""
			SELECT
				COUNT( DISTINCT ds.document_id ) as distribution, 
				s.language,
				s.stemmed 
			FROM `anta_document_segment` ds
			JOIN anta_segment s ON ds.segment_id = s.id
			JOIN anta_document d ON d.id = ds.document_id
			WHERE d.corpus_id = %s AND s.language = %s
			GROUP BY s.stemmed ORDER BY distribution DESC, stemmed ASC""", [ corpus.id, language ]
		)

		for row in dictfetchall(cursor):
			# increment global runner (stats)
			current_stem = current_stem + 1;
			
			# store tfidf inside each segment-document relationships
			try:
				dss = Document_Segment.objects.filter( segment__stemmed=row['stemmed'], segment__language=language)
				
				df = float( row['distribution'] ) / number_of_documents
				print float(current_stem) / number_of_stems * 100.0, row[ column ], row['distribution'], df
			except Exception, e:
				print e
				close_routine( routine, error="Exception: %s" % e, status="ERR")
				transaction.rollback()
				return
			for ds in dss:
				ds.tfidf = ds.tf * math.log(1/df) 
				ds.save()
			
				# tf is term frequency exactly from words
				print ds.tf,ds.document.id, ds.segment.content
			print

			if current_stem % 25 == 0:
				log_routine( routine, completion = completion_start + (float(current_stem) / number_of_stems)*completion_score )
				# save percentage and commit transaction
				transaction.commit()

	transaction.commit()
	return
	
	# group by stem!
	
	
    
	for row in dictfetchall(cursor):
		
		print row[ column ], row['distribution']
		kwargs = {
    		'{0}__{1}'.format('document', 'corpus'): corpus,
			'{0}__{1}'.format('segment', column ): row[ column ],
		}
		ds = Document_Segment.objects.filter( **kwargs ).all().order_by('-tf')
		
		df = float( row['distribution'] ) / number_of_documents
		# computate tf idf for the given value
		first = True
		
		for s in ds:
			# computate and store tfidf
			s.tfidf = s.tf * math.log(1/df) 
			s.save()
			
			if first:
				print "sample tfidf for '",row[ column ], '{', row['distribution'],"}': tf[",s.tf,"] df[", df, "] idf[",math.log(1/df),"] tfidf[", s.tfidf,"]"
				first = False
	# cycle thouhg segments
	
	print corpus.name, number_of_documents


def export( corpus, language, parser, column="stemmed" ):
	print """
	===========================================
	---- EXPORT SEGMENTS FOR REFINE SAMPLE ----
	===========================================
	"""
	try:
		c = Corpus.objects.get( name=corpus )
	except Exception, e:
		print "Exception: %s" % e
		return error( message="corpus '%s' was not found!" % corpus, parser=parser )
	
	ss = Segment.objects.raw("""
		SELECT 
			`anta_segment`.`id`, `anta_segment`.`content`, `anta_segment`.`language`, 
			`anta_segment`.`stemmed`, `anta_segment`.`status`, 
			MAX(`anta_document_segment`.`tfidf`) AS `max_tfidf`,
			MAX(`anta_document_segment`.`tf`) AS `max_tf`, 
			COUNT(`anta_document_segment`.`document_id`) AS `distro` 
		FROM `anta_segment`
			JOIN `anta_document_segment` ON (`anta_segment`.`id` = `anta_document_segment`.`segment_id`) 
			JOIN `anta_document` ON (`anta_document_segment`.`document_id` = `anta_document`.`id`) 
		WHERE `anta_document`.`corpus_id` = %s AND content NOT REGEXP '^[[:alpha:]][[:punct:]]$'
		GROUP BY `anta_segment`.`id`
		""",[c.id]
	) 
	
	print ss.query	

	for s in ss:
		print s.id, s.stemmed, s.distro, s.max_tfidf, s.max_tf
		break


@transaction.commit_manually
def importcsv( routine, csvfile, column="stemmed" ):
	print """
	========================================
	---- IMPORT SEGMENTS ROM REFINE CSV ----
	========================================
	"""
	
	log_routine( routine, entry="importcsv started", completion=0 );
	transaction.commit()

	rows = list(csvfile)
	totalrows = len(rows)
	for i, row in enumerate(rows):
		# update stemmed_refined cell
		try:
			s = Segment.objects.get(id=row['segment_id'])
			buffer_stemmed = s.stemmed
			s.stemmed = row['concept']
			s.stemmed_refined = buffer_stemmed
			s.save()

		except Exception, e:
			#print	" segemnt id %s was not found!" % row['segment_id']
			close_routine( routine, error="Exception: %s %s" % (e,row), status="ERR" )
			transaction.commit()
			return

		if i % 25 == 0:
			log_routine( routine, entry="importcsv at line: %s" % i, completion=i/float(totalrows) )
			print i, i/float(totalrows)
			
			transaction.commit()

	close_routine( routine, status="OK" )
	transaction.commit()
	

def similarity( corpus, language, parser, column="stemmed" ):
	print """
	====================
	---- SIMILARITY ----
	====================
	"""
	
	try:
		corpus = Corpus.objects.get( name=corpus )
	except:
		return error( message="corpus '%s' was not found!" % corpus, parser=parser )
	
	print "corpus:",corpus.id, corpus.name
	
	number_of_documents = Document.objects.filter(corpus=corpus ).count()
	print "document in corpus:",number_of_documents
	
	# get stemmed list per document
	cursor = connection.cursor()
	cursor.execute("SELECT " + column + ", d.id as doc_id FROM anta_document_segment ds  JOIN anta_segment s ON ds.segment_id = s.id JOIN anta_document d ON ds.document_id = d.id WHERE d.corpus_id=%s",[ corpus.id ] ) # we do not need ORDER BY d.id, ds.id
	
	# build corpus 
	documents = {}
	
	for row in dictfetchall(cursor):
		if row['doc_id'] not in documents:
			documents[ row['doc_id'] ] = []
		documents[ row['doc_id'] ].append( row[ column ] )	
		
	# translate corpus id
	pattern_id_translation = {}
	
	# reformat documents, join space separated stemmed segment values.
	for d in documents:
		documents[d] = pvDocument( " ".join( documents[d] ) )
		pattern_id_translation[ documents[d].id ] = d
		
	print "pattern_id_translation table:", pattern_id_translation
	print "document in corpus:",number_of_documents
	print "similarity neighborood ",number_of_documents / 2
	
	# store document in corpus.
	c = pvCorpus( documents.values() )
	
	# computate and save similarities
	for d in documents:
		for n in c.neighbors( documents[d], top=number_of_documents):
			alpha_id = pattern_id_translation[ documents[d].id ]
			omega_id = pattern_id_translation[ n[1].id ]
			cosine_similarity = n[0]
			
			try:
				dist = Distance.objects.get( alpha__id=alpha_id, omega__id=omega_id )
				print "distantce exists:", dist.id, cosine_similarity
			except:
				dist = Distance( alpha_id=alpha_id, omega_id=omega_id )
				print "create Distance object", dist.id, cosine_similarity
			#	print a distance exist between these two document	
			dist.cosine_similarity = cosine_similarity
			dist.save()
			# print documents[d].id, alpha_id,omega_id
		
	return
	
def main( argv):
	usage = "usage: %prog -f function [ standard|importcsv [-o column] [-x csvfile] ]"
	parser = OptionParser( usage=usage )
	
	parser.add_option("-r", "--routine", dest="routine",
		help="anta routine id")

	parser.add_option("-c", "--corpus", dest="corpus",
		help="anta Corpus.id")
		
	parser.add_option( "-l", "--language", dest="language", default="en",
		help="language")
	
	parser.add_option("-f", "--function", dest="func",
		help="function")
	
	parser.add_option("-d", "--delimiter", dest="delimiter", default="\t",
		help="csv cell delimiter")

	parser.add_option( "-o", "--tfidfcolumn", dest="tfidfcolumn", default="stemmed",
		help="function")
	
	parser.add_option( "-x", "--csv", dest="filename", default="",
		help="csv file absolute path")

	( options, argv ) = parser.parse_args()
	
	if options.routine is None:
		error( message="Use -r to specify the routine", parser=parser )
	try:	
		routine = Routine.objects.get( pk=options.routine)
	except Exception, e:
		error( message="Exception: %s" % e, parser=parser )
	
	# change routine status to CRE.. script is alive!
	routine.status="CRE"
	routine.last_entry="routine started!"
	routine.save()

	error_message = None
	
	if options.func is None:
		error( message="Use -f to specify the desired function.", parser=parser )
		
	
	# load corpus only for certain options
	if options.func == "standard" or options.func == "tfidf" or options.func == "clean" or options.func == "tf":
		if options.corpus is None:
			error_message = "Use -c to specify the corpus"
		try:
			corpus = Corpus.objects.get( pk=options.corpus )
		except Exception, e:
			error_message = "Exception: %s" % e

	if options.func == "importcsv":
		import unicodecsv,codecs
		try:
			f = open( options.filename, "rU")
			#f = open( options.csv, 'rb' )
			csvfile = csv.DictReader( f, delimiter=options.delimiter )
			#content = f.read()
			#print "delimiter: options.delimiter", content
			#csv.reader(f, dialect, **kwds)
			#csvfile = unicodecsv.reader( content, encoding='utf-8')
			
		except Exception, e:
			error_message = "Exception: %s" % e
	#
	#     ==============================
	#     ---- otuput error message ----
	#     ==============================
	#
	if error_message is not None:
		print error_message
		close_routine( routine, error=error_message, status="ERR")
		error( message=error_message, parser=parser )
	
	#
	#     =================================
	#     ---- execute valid functions ----
	#     =================================
	#
	if options.func == "standard":
		return standard( routine=routine, corpus=corpus ) # pattern tf + stems tfidf
	
	elif options.func == "clean":
		return clean( routine=routine, corpus=corpus ) # delete segments

	elif options.func == "tf":
		return tf( routine=routine, corpus=corpus ) # update tf

	elif options.func == "tfidf":
		return tfidf( routine=routine, corpus=corpus ) # tfidf ONLY, per language analysis

	elif options.func == "importcsv":
		return importcsv( routine=routine, csvfile=csvfile )

	close_routine( routine, error="Fatal: function not found", status="ERR")
	
	
if __name__ == '__main__':
	# get corpus name
	main(sys.argv[1:])	
