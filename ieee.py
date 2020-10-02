from pyhtml import html
import latex

tolatex = None
process_usr = None

def _titleSection(tag, parent):
	result = latex.Group([], "\n")
	process_usr(tag, result, parent)
	if 'skip' in result.usr and result.usr['skip']:
		result.usr['skip'].append('p')
	else:
		result.usr['skip'] = ['p']
	result << tolatex(tag.content, result)
	result << latex.Cmd("maketitle")
	return result

def _title(tag, parent):
	result = latex.Cmd("title")
	process_usr(tag, result, parent)
	result.args = [latex.Group()]
	process_usr(tag, result.args[0], result)
	result.args[0] << tolatex(tag.content, result.args[0])
	return result

def _author(tag, parent):
	result = latex.Cmd("author")
	process_usr(tag, result, parent, True)
	result.args = [latex.Cmd("IEEEauthorblockA")]
	process_usr(tag, result.args[0], result, True)
	result.args[0].args = tolatex(tag.content, result.args[0])
	return result

def _authors(tag, parent):
	result = latex.Group([], "\n")
	process_usr(tag, result, parent)
	result << tolatex(tag.content, result)
	return result

def _abstract(tag, parent):
	result = latex.Group()
	process_usr(tag, result, parent)
	p = tag.get('p')
	if len(p) > 0:
		abst = latex.Env("abstract")
		process_usr(p[0], abst, result)
		abst << tolatex(p[0].content[1][1:], abst)
		result << abst

	if len(p) > 1:
		keys = latex.Env("IEEEkeywords")
		process_usr(p[1], keys, result)
		keys << tolatex(p[1].content[2:], result)
		result << keys
	return result

def _references(tag, parent):
	result = latex.Env("thebibliography", [len(tag.content)])
	process_usr(tag, result, parent)
	result << tolatex(tag.content, result)
	return result

def _bio(tag, parent):
	content = []
	img = None
	name = None
	for c in tag.content:
		if isinstance(c, html.STag) and c.name == "img" and not img:
			img = c
		elif isinstance(c, html.Tag) and c.name == "b":
			name = c.content[0]
		else:
			content.append(c)
	
	result = latex.Env("IEEEbiography")
	process_usr(tag, result, parent)
	result.args = [(latex.Group([tolatex(img, result)], "", "{", "}"),), tolatex(name, result)]
	result << tolatex(content, result)
	return result

idHandlers = {
	'title': _titleSection,
	'abstract': _abstract,
	'references': _references,
}

classHandlers = {
	'title': _title,
	'author': _author,
	'authors': _authors,
	'bio': _bio,
}

tagHandlers = {
}

def load(a, b):
	global tolatex
	global process_usr
	tolatex = a
	process_usr = b
	return {
		'section': 0,
	}

def setDocument():
	return "\\documentclass[journal]{IEEEtran}"

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

