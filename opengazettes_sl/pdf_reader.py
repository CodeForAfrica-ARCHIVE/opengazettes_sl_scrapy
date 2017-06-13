from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfdocument import PDFDocument
import urllib2
from urllib2 import Request
from pdfminer.pdfparser import PDFParser
from cStringIO import StringIO
import re
import dateparser

def parsePDF(url):
	open = urllib2.urlopen(Request(url)).read()
	# Cast to StringIO object
	from StringIO import StringIO
	memory_file = StringIO(open)

	# Create a PDF parser object associated with the StringIO object
	parser = PDFParser(memory_file)

	# Create a PDF document object that stores the document structure
	document = PDFDocument(parser)

	# Define parameters to the PDF device objet
	rsrcmgr = PDFResourceManager()
	retstr = StringIO()
	laparams = LAParams()
	codec = 'utf-8'

	# Create a PDF device object
	device = TextConverter(rsrcmgr, retstr, codec = codec, laparams = laparams)

	# Create a PDF interpreter object
	interpreter = PDFPageInterpreter(rsrcmgr, device)

	# Process each page contained in the document
	for page in PDFPage.create_pages(document):
		interpreter.process_page(page)
		text =  retstr.getvalue()

	time = get_date([line for line in text.split('\n') if line][:20])
	vol = get_vol([line for line in text.split('\n') if line][:20])
	return time, vol

def get_date(data):
	for item in data:
		if dateparser.parse(item):
			return dateparser.parse(item)
def get_vol(data):
	for item in data:
		if item.lower().startswith('vol'):
			vol =  re.findall(r'\b[A-Za-z]+\b', item)[-1]
			return vol
