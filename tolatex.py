#!/usr/bin/python

from pyhtml.parse import *
import sys
import os.path
import latex

def escape(content):
	if isinstance(content, list):
		return [escape(item) for item in content]
	else:
		return str(content).replace('_', '\\_').replace('$', '\\$').replace('%', '\\%')

def process_usr(tag, result, parent):
	if parent:
		result.usr = parent.usr.copy()

	if tag.name == "pre":
		result.usr["pre"] = True

	if tag.name == "header":
		result.usr["header"] = True

	if "class" in tag.attrs:
		cls = tag.attrs["class"].split()
		for c in cls:
			if c[0:9] == "language-":
				result.usr["lang"] = c[9:]
				if result.usr["lang"] in ["chp", "hse", "prs"]:
					result.usr["lang"] = "hse"
			elif c == "author":
				result.usr["author"] = True

def default2latex(tag, parent):
	if tag.name not in ["section", "subsection", "document"]:
		print tag

	result = latex.Group([], "\n")
	process_usr(tag, result, parent)
	result << tolatex(tag.content, result)
	return result

def article2latex(tag, parent):
	result = latex.Env("document")
	process_usr(tag, result, parent)
	result << tolatex(tag.content, result)
	return result

def div2latex(tag, parent):
	if "class" in tag.attrs:
		cls = tag.attrs["class"].split()
	else:
		cls = []

	if "src" in tag.attrs:
		src = tag.attrs["src"]
		name = os.path.basename(src)
		splt = os.path.splitext(name)
		result = latex.Input(splt[0])	
		process_usr(tag, result, parent)
		return result
	elif "author" in cls:
		result = latex.Cmd("author")
		process_usr(tag, result, parent)
		result.args = [latex.Cmd("IEEEauthorblockA")]
		process_usr(tag, result.args[0], result)
		result.args[0].args = tolatex(tag.content, result.args[0])
		return result
	elif "authors" in cls:
		result = latex.Group([], "\n")
		process_usr(tag, result, parent)
		result << tolatex(tag.content, result)
		return result
	elif "author" in parent.usr:
		result = latex.Group(end="\\\\\n")
		process_usr(tag, result, parent)
		result << tolatex(tag.content, result)
		return result
	elif "references" in cls:
		result = latex.Env("thebibliography", [len(tag.content)])
		process_usr(tag, result, parent)
		result << tolatex(tag.content, result)
		return result
	elif "abstract" in cls:
		result = latex.Group()
		process_usr(tag, result, parent)
		result.usr["abstract"] = True
		result << tolatex(tag.content, result)
		return result
	else:
		return default2latex(tag, parent)

def header2latex(tag, parent):
	result = latex.Group([], "\n")
	process_usr(tag, result, parent)
	result << tolatex(tag.content, result)
	result << latex.Cmd("maketitle")
	return result

def hN2latex(tag, parent):
	for i in range(1, 7):
		if tag.name == "h" + str(i):
			if "header" in parent.usr:
				result = latex.Cmd("title")
				process_usr(tag, result, parent)
				result.args = [latex.Group()]
				process_usr(tag, result.args[0], result)
				result.args[0] << tolatex(tag.content, result.args[0])
				return result
			elif tag.content[0] != "References":
				result = latex.Section("", i-1)
				process_usr(tag, result, parent)
				result.args = [latex.Group()]
				process_usr(tag, result.args[0], result)
				result.args[0] << tolatex(tag.content, result.args[0])
				return result
	return None

def p2latex(tag, parent):
	if "abstract" in parent.usr:
		if tag.content[0].content[0] == "Abstract":
			result = latex.Env("abstract")
			process_usr(tag, result, parent)
			result << tolatex([tag.content[1][3:]] + tag.content[2:], result)
			return result
		elif tag.content[0].content[0] == "Keywords":
			result = latex.Env("IEEEkeywords")
			process_usr(tag, result, parent)
			result << tolatex(tag.content[2:], result)
			return result
	else:
		result = latex.Group([], " ", "\n")
		process_usr(tag, result, parent)
		result << tolatex(tag.content, result)
		return result;

def pre2latex(tag, parent):
	result = latex.Group()
	process_usr(tag, result, parent)
	result << tolatex(tag.content, result)
	return result

def code2latex(tag, parent):
	if "pre" in parent.usr:
		if "lang" in parent.usr:
			result = latex.Env(parent.usr["lang"])
			process_usr(tag, result, parent)
			result << latex.Group(tolatex(tag.content, result))
			return result
		else:
			result = latex.Env("equation")
			process_usr(tag, result, parent)
			result << latex.Group(tolatex(tag.content, result))
			return result
	else:
		if "lang" in parent.usr and parent.usr["lang"] in ["prs", "hse", "chp"]:
			result = latex.Inline("", "@")
			process_usr(tag, result, parent)
			result.content = latex.Group()
			process_usr(tag, result.content, result)
			result.content << tolatex(tag.content, result.content)
			return result
		else:
			result = latex.Inline("", "$")
			process_usr(tag, result, parent)
			result.content = latex.Group()
			process_usr(tag, result.content, result)
			result.content << tolatex(tag.content, result.content)
			return result

def a2latex(tag, parent):
	if "href" in tag.attrs:
		href = tag.attrs["href"]
		if href[0] == "#":
			result = latex.Cmd("cite", [href[1:]], end="")
			process_usr(tag, result, parent)
			return result
		else:
			result = latex.Cmd("href", [href], end="")
			process_usr(tag, result, parent)
			result.args.append(latex.Group(tolatex(tag.content, parent), "", ""))
			return result
	return default2latex(tag, parent)

def cite2latex(tag, parent):
	result = latex.Group()
	process_usr(tag, result, parent)
	if "id" in tag.attrs:
		result << latex.Cmd("bibitem", [tag.attrs["id"]])
	result << tolatex(tag.content, result)
	return result

def q2latex(tag, parent):
	result = latex.Cmd("say", end="")
	process_usr(tag, result, parent)
	result.args = [latex.Group()]
	process_usr(tag, result.args[0], result)
	result.args[0] << tolatex(tag.content, result.args[0])
	return result

def b2latex(tag, parent):
	result = latex.Cmd("textbf", end="")
	process_usr(tag, result, parent)
	result.args = [latex.Group()]
	process_usr(tag, result.args[0], result)
	result.args[0] << tolatex(tag.content, result.args[0])
	return result

def ul2latex(tag, parent):
	result = latex.Env("itemize")
	process_usr(tag, result, parent)
	result << tolatex(tag.content, result)
	return result

def ol2latex(tag, parent):
	result = latex.Env("enumerate")
	process_usr(tag, result, parent)
	result << tolatex(tag.content, result)
	return result

def li2latex(tag, parent):
	result = latex.Group(sep=" ")
	process_usr(tag, result, parent)
	result << latex.Cmd("item", end="")
	result << tolatex(tag.content, result)
	return result

def em2latex(tag, parent):
	if "abstract" in parent.usr:
		result = latex.Group()
		process_usr(tag, result, parent)
		result << tolatex(tag.content, result)
		return result
	else:
		result = latex.Cmd("textit", end="")
		process_usr(tag, result, parent)
		result.args = [latex.Group()]
		process_usr(tag, result.args[0], result)
		result.args[0] << tolatex(tag.content, result.args[0])
		return result

def center2latex(tag, parent):
	result = latex.Env("center")
	process_usr(tag, result, parent)
	result << tolatex(tag.content, result)
	return result

def table2latex(tag, parent):
	result = latex.Env("table", args=[("ht",)])
	process_usr(tag, result, parent)
	table = latex.Env("tabular")
	tr = tag["tr"]
	table.args = [" | ".join(["c" for _ in range(0, len(tr[0].content))])]
	process_usr(tag, table, result)
	table << tolatex(tag.content, table)
	result << latex.Cmd("centering")
	result << table
	return result

def thead2latex(tag, parent):
	result = latex.Group([], "\n")
	process_usr(tag, result, parent)
	result.usr["thead"] = True
	result << tolatex(tag.content, result)
	result << latex.Cmd("hline")
	return result

def tbody2latex(tag, parent):
	result = latex.Group([], "\n")
	process_usr(tag, result, parent)
	result.usr["tbody"] = True
	result << tolatex(tag.content, result)
	return result

def tr2latex(tag, parent):
	result = latex.Group([], " & ", " \\\\\n")
	process_usr(tag, result, parent)
	result << tolatex(tag.content, result)
	return result

def td2latex(tag, parent):
	result = latex.Group()
	process_usr(tag, result, parent)
	result << tolatex(tag.content, result)
	return result

def th2latex(tag, parent):
	result = latex.Group()
	process_usr(tag, result, parent)
	result << tolatex(tag.content, result)
	return result

def figure2latex(tag, parent):
	result = latex.Env("figure", args=[("ht",)])
	process_usr(tag, result, parent)
	result << latex.Cmd("centering")
	result << tolatex(tag.content, result)
	return result

handlers = {
	'article': article2latex,
	'div': div2latex,
	'header': header2latex,
	'h1': hN2latex,
	'h2': hN2latex,
	'h3': hN2latex,
	'h4': hN2latex,
	'h5': hN2latex,
	'h6': hN2latex,
	'h7': hN2latex,
	'p': p2latex,
	'pre': pre2latex,
	'code': code2latex,
	'a': a2latex,
	'cite': cite2latex,
	'q': q2latex,
	'b': b2latex,
	'em': em2latex,
	'ul': ul2latex,
	'ol': ol2latex,
	'li': li2latex,
	'center': center2latex,
	'table': table2latex,
	'thead': thead2latex,
	'tbody': tbody2latex,
	'tr': tr2latex,
	'td': td2latex,
	'th': th2latex,
	'figure': figure2latex,
}

def tolatex(tag, parent):
	if isinstance(tag, (list, tuple)):
		result = []
		for elem in tag:
			item = tolatex(elem, parent)
			if item:
				result.append(item)
		return result
	if isinstance(tag, html.Tag):
		if tag.name in handlers:
			return handlers[tag.name](tag, parent)
		else:
			return default2latex(tag, parent)
	elif isinstance(tag, html.STag):
		print tag
		return ""
	else:
		return escape(tag)

flag = None
out_path = ""
paths = []
for arg in sys.argv[1:]:
	if arg[0] == "-":
		flag = arg
	elif flag:
		if flag == "-o" or flag == "--output":
			out_path = arg
		flag = None
	else:
		paths.append(arg)

for path in paths:
	name = os.path.splitext(os.path.basename(path))[0]

	parser = Parser()
	with open(path, 'r') as fptr:
		parser.feed(fptr.read())

	with open(os.path.join(out_path, name + ".tex"), 'w') as fptr:
		article = parser.syntax["article"]
		if article:
			print >>fptr, "\n".join([
				"\\documentclass[journal]{IEEEtran}",
				"\\usepackage{ifpdf}",
				"\\usepackage{cite}",
				"\\usepackage[pdftex]{graphicx}",
				"\\usepackage{alltt}",
				"\\usepackage{amsmath}",
				"\\usepackage{algorithmic}",
				"\\usepackage{array}",
				"\\usepackage[caption=false,font=normalsize,labelfont=sf,textfont=sf]{subfig}",
				"\\usepackage{fixltx2e}",
				"\\usepackage{stfloats}",
				"\\usepackage{url}",
				"\\usepackage{prs}",
				"\\usepackage{siunitx}",
				"\\usepackage{dirtytalk}",
				"\\usepackage{hyperref}",
				"\\hypersetup{",
				"		colorlinks=true,",
				"		linkcolor=blue,",
				"		filecolor=blue,",
				"		urlcolor=blue,",
				"}",
				"\\urlstyle{same}",
				"\\noiosubscripts",
			])

			print >>fptr, tolatex(article[0], None)
		else:
			print >>fptr, tolatex(parser.syntax, None)
