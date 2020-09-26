from pyhtml import html
import latex

"""
if "header" in parent.usr:
				result = latex.Cmd("title")
				process_usr(tag, result, parent, True)
				result.args = [latex.Group()]
				process_usr(tag, result.args[0], result)
				result.args[0] << tolatex([content], result.args[0])
				return result
"""

def _author(tag, tolatex, process_usr):
	result = latex.Cmd("author")
	process_usr(tag, result, parent, True)
	result.args = [latex.Cmd("IEEEauthorblockA")]
	process_usr(tag, result.args[0], result, True)
	result.args[0].args = tolatex(tag.content, result.args[0])
	return result

def _authors(tag, tolatex, process_usr):
	result = latex.Group([], "\n")
	process_usr(tag, result, parent)
	result << tolatex(tag.content, result)
	return result

def _abstract(tag, tolatex, process_usr):
	result = latex.Group()
	process_usr(tag, result, parent)
	result.usr["abstract"] = True
	result << tolatex(tag.content, result)
	return result

def _references(tag, tolatex, process_usr):
	result = latex.Env("thebibliography", [len(tag.content)])
	process_usr(tag, result, parent)
	result << tolatex(tag.content, result)
	return result

def _biography(tag, tolatex, process_usr):
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
	'abstract': _abstract,
	'references': _references,
	'biography': _biography,
}

classHandlers = {
	'author': _author,
	'authors': _authors,
}

def setDocument():
	return "\\documentclass[journal]{IEEEtran}"

def hasClass(name):
	return (name in classHandlers)

def hasId(name):
	return (name in idHandlers)

def setClass(name, *argv):
	return classHandlers[name](*argv)

def setId(name, *argv):
	return idHandlers[name](*argv)

