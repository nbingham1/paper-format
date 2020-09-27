from pyhtml import html
import latex

tolatex = None
process_usr = None

def _title(tag, parent):
	title = ""
	author = ""
	conferral = ""
	for elem in tag.content:
		if isinstance(elem, html.Tag):
			if "class" in elem.attrs:
				titlecls = elem.attrs["class"].split()
				if "title" in titlecls:
					title = elem.content[0].strip()
				elif "author" in titlecls:
					author = elem.content[2].strip()
					conferral = elem.content[4].strip().split()
	
	result = latex.Group()
	process_usr(tag, result, parent)
	result << latex.Cmd("title", [title])
	result << latex.Cmd("author", [author])
	result << latex.Cmd("conferraldate", conferral)
	result << latex.Cmd("degreefield", ["Ph.D."])
	result << latex.Cmd("maketitle")
	return result

def _copyright(tag, parent):
	copy = tag.content[0].split(' ')
	year = copy[1]
	name = ' '.join(copy[2:])
	result = latex.Group()
	process_usr(tag, result, parent)
	result << latex.Cmd("copyrightholder", [name])
	result << latex.Cmd("copyrightyear", [year])
	result << latex.Cmd("makecopyright")
	return result

def _abstract(tag, parent):
	result = latex.Env("abstract")
	process_usr(tag, result, parent)
	result.usr['skip'] = ['h1']
	result << tolatex(tag.content, result)
	return result

def _biography(tag, parent):
	result = latex.Env("biosketch")
	process_usr(tag, result, parent)
	result.usr['skip'] = ['h1']
	result << tolatex(tag.content, result)
	return result

def _dedication(tag, parent):
	result = latex.Env("dedication")
	process_usr(tag, result, parent)
	result.usr['skip'] = ['h1']
	result << tolatex(tag.content, result)
	return result

def _acknowledgements(tag, parent):
	result = latex.Env("acknowledgements")
	process_usr(tag, result, parent)
	result.usr['skip'] = ['h1']
	result << tolatex(tag.content, result)
	return result

def _tableOfContents(tag, parent):
	result = latex.Cmd("contentspage")
	process_usr(tag, result, parent)
	return result

def _listOfFigures(tag, parent):
	result = latex.Cmd("figurelistpage")
	process_usr(tag, result, parent)
	return result

def _listOfTables(tag, parent):
	result = latex.Cmd("tablelistpage")
	process_usr(tag, result, parent)
	return result

def _listOfAbbreviations(tag, parent):
	result = latex.Group()
	process_usr(tag, result, parent)
	result << latex.Cmd("renewcommand{\\nomname}{List of Abbreviations}")
	result << latex.Cmd("makenomenclature")
	result << latex.Cmd("printnomenclature", [("1in",)])
	return result

def _preface(tag, parent):
	result = latex.Group()
	process_usr(tag, result, parent)
	result << tolatex(tag.content, result)
	result << latex.Cmd("normalspacing")
	result << latex.Cmd("setcounter", ["page", 1])
	result << latex.Cmd("pagenumbering", ["arabic"])
	result << latex.Cmd("pagestyle", ["cornell"])
	result << latex.Cmd("addtolength", ["\\parskip", "0.5\\baselineskip"])
	return result

def _appendix(tag, parent):
	result = latex.Env("appendix")
	process_usr(tag, result, parent)
	result.usr['skip'] = ['h1']
	result << tolatex(tag.content, result)
	return result

def _references(tag, parent):
	result = latex.Env("thebibliography", [len(tag.content)])
	process_usr(tag, result, parent)
	result.usr['skip'] = ['h1']
	result << tolatex(tag.content, result)
	return result

idHandlers = {
	'title': _title,
	'copyright': _copyright,
	'abstract': _abstract,
	'biography': _biography,
	'dedication': _dedication,
	'acknowledgements': _acknowledgements,
	'table-of-contents': _tableOfContents,
	'list-of-figures': _listOfFigures,
	'list-of-tables': _listOfTables,
	'list-of-abbreviations': _listOfAbbreviations,
	'preface': _preface,
	'appendix': _appendix,
	'references': _references,
}

classHandlers = {
}

tagHandlers = {
}

def load(a, b):
	global tolatex
	global process_usr
	tolatex = a
	process_usr = b

def setDocument():
	return "\\documentclass[phd,cornellheadings]{cornell}"

def has(tag):
	if "id" in tag.attrs and tag.attrs["id"] in idHandlers:
		return True
	if "class" in tag.attrs:
		cls = tag.attrs["class"].split()
		for c in cls:
			if c in classHandlers:
				return True
	if tag.name in tagHandlers:
		return True
	return False

def set(tag, parent):
	if "id" in tag.attrs and tag.attrs["id"] in idHandlers:
		return idHandlers[tag.attrs["id"]](tag, parent)
	if "class" in tag.attrs:
		cls = tag.attrs["class"].split()
		for c in cls:
			if c in classHandlers:
				return classHandlers[c](tag, parent)
	if tag.name in tagHandlers:
		return tagHandlers[tag.name](tag, parent)
	return None

