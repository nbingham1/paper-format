#!/usr/bin/python3

from pyhtml.parse import *
import sys
import os.path
import re
import latex
from lxml import etree

latex_figures = []
latex_citations = []
latex_tables = []

latex_files = []
latex_path = []
latex_unresolved = {}
latex_outpath = ""

def escape(content, space=True):
	if isinstance(content, list):
		return [escape(item, space) for item in content]
	else:
		content = str(content)
		if content.strip():
			return content.replace(u'_', u'\\_').replace(u'$', u'\\$').replace(u'%', u'\\%').replace(u'&', u'\\&')
		elif space:
			return content.replace(u'\n', u'').replace(u'\r', u'')
		else:
			return ""

def convert_code(content, lang, caption=False):
	result = "".join([str(c) for c in content]).strip()
	if lang in ["prs"]:
		if not caption:
			result = re.sub(r'->', r'$\\rightarrow$', result, flags=re.MULTILINE)
			result = re.sub(r'~', r'$\\neg$', result, flags=re.MULTILINE)
			result = re.sub(r'\&', r'$\\wedge$', result, flags=re.MULTILINE)
			result = re.sub(r'\|', r'$\\vee$', result, flags=re.MULTILINE)
			result = re.sub(r'<=', r'$\\leq$', result, flags=re.MULTILINE)
			result = re.sub(r'>=', r'$\\geq$', result, flags=re.MULTILINE)
			result = re.sub(r'!=', r'$\\neq$', result, flags=re.MULTILINE)
			result = re.sub(r'==', r'$=$', result, flags=re.MULTILINE)
			result = re.sub(r'\+(\s*(?:\n|$))', r'$\\uparrow$\1', result, flags=re.MULTILINE)
			result = re.sub(r'-(\s*(?:\n|$))', r'$\\downarrow$\1', result, flags=re.MULTILINE)
			result = re.sub(r'\.\.\.', r'$\\cdots$', result, flags=re.MULTILINE)
			result = re.sub(r'([a-zA-Z_][a-zA-Z0-9_]*)\.([a-zA-Z0-9_]*)', r'\1$_{\\text{\2}}$', result, flags=re.MULTILINE)
			result = re.sub(r'_([a-zA-Z0-9_][a-zA-Z0-9_]*)', r'$\\overline{\\mbox{\1}}$', result, flags=re.MULTILINE)
		else:
			result = re.sub(r'([a-zA-Z_][a-zA-Z0-9_]*)\.([a-zA-Z_][a-zA-Z0-9_]*)', r'\1\2', result, flags=re.MULTILINE)
		result = re.sub(r'\{\$', r'{', result, flags=re.MULTILINE)
		result = re.sub(r'\$\}', r'}', result, flags=re.MULTILINE)
	else:
		if not caption:
			result = re.sub(r'->', r'$\\rightarrow$', result, flags=re.MULTILINE)
			result = re.sub(r'\\ring', r'$\\circ$', result, flags=re.MULTILINE)
			result = re.sub(r'\\par', r'$\\parallel$', result, flags=re.MULTILINE)
			result = re.sub(r'\|\|', r'$\\parallel$', result, flags=re.MULTILINE)
			result = re.sub(r'\*\[', r'$*[$', result, flags=re.MULTILINE)
			result = re.sub(r'~', r'$\\neg$', result, flags=re.MULTILINE)
			result = re.sub(r'\&', r'$\\wedge$', result, flags=re.MULTILINE)
			result = re.sub(r'\|', r'$\\vee$', result, flags=re.MULTILINE)
			result = re.sub(r'<=', r'$\\leq$', result, flags=re.MULTILINE)
			result = re.sub(r'>=', r'$\\geq$', result, flags=re.MULTILINE)
			result = re.sub(r'!=', r'$\\neq$', result, flags=re.MULTILINE)
			result = re.sub(r'==', r'$=$', result, flags=re.MULTILINE)
			result = re.sub(r'\+(\s*(?:[;,:\]\)\$\n]|$))', r'$\\uparrow$\1', result, flags=re.MULTILINE)
			result = re.sub(r'-(\s*(?:[;,:\]\)\$\n]|$))', r'$\\downarrow$\1', result, flags=re.MULTILINE)
			result = re.sub(r'\[\]', r'$\\vrectangle$', result, flags=re.MULTILINE)
			result = re.sub(r':([^=])', r'$|$\1', result, flags=re.MULTILINE)
			result = re.sub(r'\.\.\.', r'$\\cdots$', result, flags=re.MULTILINE)
			result = re.sub(r'([a-zA-Z_][a-zA-Z0-9_]*)\.([a-zA-Z0-9_]*)', r'\1$_{\\text{\2}}$', result, flags=re.MULTILINE)
			result = re.sub(r'#([a-zA-Z0-9_][a-zA-Z0-9_]*)', r'$\\overline{\\mbox{\1}}$', result, flags=re.MULTILINE)	
		else:
			result = re.sub(r'\\par', r'||', result, flags=re.MULTILINE)
			result = re.sub(r'([a-zA-Z_][a-zA-Z0-9_]*)\.([a-zA-Z_][a-zA-Z0-9_]*)', r'\1\2', result, flags=re.MULTILINE)
		result = re.sub(r'([^\*])\[', r'\1$[$', result, flags=re.MULTILINE)
		result = re.sub(r'\]', r'$]$', result, flags=re.MULTILINE)
		#result = re.sub(r'\{\$', r'{', result, flags=re.MULTILINE)
		#result = re.sub(r'\$\}', r'}', result, flags=re.MULTILINE)
	return result

def process_usr(tag, result, parent, is_arg=False):
	if parent:
		result.usr = parent.usr.copy()

	if tag.name == "pre":
		result.usr["pre"] = True

	if tag.name == "header":
		result.usr["header"] = True

	if tag.name == "figure":
		result.usr["figure"] = True

	if is_arg:
		result.usr["arg"] = True
		
	if "class" in tag.attrs:
		cls = tag.attrs["class"].split()
		for c in cls:
			if c[0:9] == "language-":
				result.usr["lang"] = c[9:]
			elif c == "author":
				result.usr["author"] = True

def default2latex(tag, parent):
	if tag.name not in ["section", "subsection", "document"]:
		print(tag.name)

	result = latex.Group()
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
		convert_file(src)
		return result
	elif "author" in cls:
		result = latex.Cmd("author")
		process_usr(tag, result, parent, True)
		result.args = [latex.Cmd("IEEEauthorblockA")]
		process_usr(tag, result.args[0], result, True)
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
	elif "bio" in cls:
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
				process_usr(tag, result, parent, True)
				result.args = [latex.Group()]
				process_usr(tag, result.args[0], result)
				result.args[0] << tolatex(tag.content, result.args[0])
				return result
			elif tag.content[0] == "Appendix":
				result = latex.Cmd("appendix")
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
		result = latex.Group(end="\n\n")
		process_usr(tag, result, parent)
		result << tolatex(tag.content, result)
		return result;

def pre2latex(tag, parent):
	result = latex.Group()
	process_usr(tag, result, parent)
	result << tolatex(tag.content, result)
	return result

def code2latex(tag, parent):
	if "lang" in parent.usr:
		lang = parent.usr["lang"]
	else:
		lang = ""

	if "pre" in parent.usr:
		page = latex.Env("minipage", args=[latex.Group(["0.95", latex.Cmd("linewidth", inline=True)])], inline=False)
		process_usr(tag, page, parent)
		result = latex.Env("lstlisting", args=[("mathescape",)])
		process_usr(tag, result, parent)
		result << convert_code(tag.content, lang, "arg" in parent.usr)
		page << result
		pre = latex.Group()
		pre << latex.Cmd("noindent")
		pre << page
		return pre
	else:
		result = latex.Cmd("protect\\lstinline", args=[("mathescape, columns=fixed",)], inline=True)
		process_usr(tag, result, parent)
		group = latex.Group()
		process_usr(tag, group, result)
		group << convert_code(tag.content, lang, "arg" in parent.usr).replace('\n', ' ')
		result.args.append(group)
		return result

citation = re.compile("^#[a-z]*[0-9]{4}")
def a2latex(tag, parent):
	if "href" in tag.attrs:
		href = tag.attrs["href"]
		if len(href) > 0 and href[0] == "#":
			if href[1:] in latex_citations:
				result = latex.Cmd("cite", [href[1:]], inline=True)
				process_usr(tag, result, parent, True)
			elif href[1:] in latex_figures:
				result = latex.Cmd("hyperref", [(href[1:],)], inline=True)
				process_usr(tag, result, parent, True)
				result.args.append("Fig. " + str(latex_figures.index(href[1:])+1))
			elif tag.content:
				result = latex.Cmd("hyperref", [(href[1:],)], inline=True)
				process_usr(tag, result, parent, True)
				result.args.append(latex.Group(tolatex(tag.content, parent)))
			elif href[1:] not in latex_unresolved:
				result = latex.Cmd("hyperref", [(href[1:],)], inline=True)
				process_usr(tag, result, parent, True)
				latex_unresolved[href[1:]] = [result]
			else:
				result = latex.Cmd("hyperref", [(href[1:],)], inline=True)
				process_usr(tag, result, parent, True)
				latex_unresolved[href[1:]].append(result)
			return result
		else:
			result = latex.Cmd("href", [href], inline=True)
			process_usr(tag, result, parent, True)
			result.args.append(latex.Group(tolatex(tag.content, parent)))
			return result
	elif "name" in tag.attrs:
		name = tag.attrs["name"]
		result = latex.Group()
		process_usr(tag, result, parent)
		result << tolatex(tag.content, parent)
		result << latex.Cmd("label", args=[name], inline=True)
		return result
	return latex.Group(tolatex(tag.content, parent))

def cite2latex(tag, parent):
	result = latex.Group()
	process_usr(tag, result, parent)
	if "id" in tag.attrs:
		latex_citations.append(tag.attrs["id"])
		result << latex.Cmd("bibitem", [tag.attrs["id"]])
	result << tolatex(tag.content, result)
	return result

def q2latex(tag, parent):
	result = latex.Cmd("say", inline=True)
	process_usr(tag, result, parent, True)
	result.args = [latex.Group()]
	process_usr(tag, result.args[0], result)
	result.args[0] << tolatex(tag.content, result.args[0])
	return result

def b2latex(tag, parent):
	result = latex.Cmd("textbf", inline=True)
	process_usr(tag, result, parent, True)
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
	result = latex.Group()
	process_usr(tag, result, parent)
	result << latex.Cmd("item ", inline=True)
	result << tolatex(tag.content, result)
	return result

def em2latex(tag, parent):
	if "abstract" in parent.usr:
		result = latex.Group()
		process_usr(tag, result, parent)
		result << tolatex(tag.content, result)
		return result
	else:
		result = latex.Cmd("textit", inline=True)
		process_usr(tag, result, parent, True)
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
	if "id" in tag.attrs:
		latex_tables.append(tag.attrs["id"])
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
	result = latex.Group([], " & ", "", " \\\\\n")
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
	figure = latex.Env("figure", args=[("ht",)])
	process_usr(tag, figure, parent)
	figure << latex.Cmd("centering")
	figure << tolatex(tag.content, figure)
	result = figure
	if 'id' in tag.attrs:
		result = latex.Group()
		result << latex.Cmd("label", args=[tag.attrs['id']], inline=True)
		result << figure
		latex_figures.append(tag.attrs['id'])
		if tag.attrs['id'] in latex_unresolved:
			for elem in latex_unresolved[tag.attrs['id']]:
				elem.args.append("Fig. " + str(len(latex_figures)))
			del latex_unresolved[tag.attrs['id']]
	else:
		latex_figures.append('')
	return result

def figcaption2latex(tag, parent):
	result = latex.Cmd("caption")
	process_usr(tag, result, parent, True)
	result.args = [latex.Group(tolatex(tag.content, result))]
	return result

def img2latex(tag, parent):
	if "src" in tag.attrs:
		src = tag.attrs["src"]
		if ".svg" in src:
			width = None
			if "style" in tag.attrs and tag.attrs["style"]:
				width = tag.attrs["style"].get("max-width")
				if "min" in width:
					width = width[4:-1].split(',')
					width = width[0] if '%' in width[0] else width[1]
				if "%" in width:
					width = float(width[0:-1])/100.0
				else:
					width = None
			src = src.replace(".svg", ".pdf_tex")
			result = latex.Group()
			process_usr(tag, result, parent, True)
			if width:
				page = latex.Env("minipage", args=[latex.Group([str(width), latex.Cmd("columnwidth", inline=True)])], inline=True)
				process_usr(tag, page, parent)

				page << latex.Cmd("centering", inline=False)
				page << latex.Cmd("def", inline=True)
				page << latex.Cmd("svgwidth", args=["\\columnwidth"], inline=False)
				page << latex.Cmd("input", args=[src])
				
				result << page
			else:
				result << latex.Cmd("def", inline=True)
				result << latex.Cmd("svgwidth", args=["\\columnwidth"], inline=False)
				result << latex.Cmd("input", args=[src], inline=False)
			return result
		else:
			result = latex.Cmd("includegraphics")
			process_usr(tag, result, parent, True)
			result.args = [("width=1.0\\columnwidth",), src]
			return result
	else:
		return default2latex(tag, parent)

def br2latex(tag, parent):
	return latex.Cmd("\\\\")

def mark2latex(tag, parent):
	result = latex.Cmd("hl", inline=True)
	process_usr(tag, result, parent, True)
	result.args = [latex.Group()]
	process_usr(tag, result.args[0], result)
	result.args[0] << tolatex(tag.content, result.args[0])
	return result

def i2latex(tag, parent):
	result = latex.Cmd("emph", inline=True)
	process_usr(tag, result, parent, True)
	result.args = [latex.Group()]
	process_usr(tag, result.args[0], result)
	result.args[0] << tolatex(tag.content, result.args[0])
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
	'figcaption': figcaption2latex,
	'img': img2latex,
	'br': br2latex,
	'mark': mark2latex,
	'i': i2latex,
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
		if "class" not in tag.attrs or "web-only" not in tag.attrs["class"]:
			if tag.name in handlers:
				return handlers[tag.name](tag, parent)
			else:
				return default2latex(tag, parent)
		else:
			return ""
	elif isinstance(tag, html.STag):
		if "class" not in tag.attrs or "web-only" not in tag.attrs["class"]:
			if tag.name in handlers:
				return handlers[tag.name](tag, parent)
			else:
				print(tag)
				return ""
		else:
			return ""
	else:
		return escape(tag, "figure" not in parent.usr)

def convert_file(path):
	name = os.path.splitext(os.path.basename(path))[0]

	if len(latex_path) > 0:
		path = os.path.join(latex_path[-1], path)
	
	latex_path.append(os.path.dirname(path))

	eparser = etree.HTMLParser(target = Parser())
	with open(path, 'r') as fptr:
		data = fptr.read()
		eparser.feed(data)
	parser = eparser.close()
	
	with open(os.path.join(latex_outpath, name + ".tex"), 'w') as fptr:
		article = parser.syntax["article"]
		if article:
			print("\n".join([
				"\\documentclass[journal]{IEEEtran}",
				"\\usepackage[pdftex]{graphicx}",
				"\\usepackage{amsmath}",
				"\\usepackage{dirtytalk}",
				"\\usepackage{hyperref}",
				"\\usepackage{listings}",
				"\\usepackage{stix}",
				#"\\usepackage{xcolor}",
				"\\usepackage{color,soul}",
				"\\soulregister\\cite7",
				"\\soulregister\\ref7",
				"\\soulregister\\pageref7",
				"\\soulregister{\\protect}{0}",
				"\\soulregister{\\lstinline}{1}",
				"\\soulregister{\\bibitem}{1}",
				"\\soulregister{\\say}{1}",
				"\\hypersetup{",
				"		colorlinks=true,",
				"		linkcolor=blue,",
				"		filecolor=blue,",
				"		urlcolor=blue,",
				"}",
				"\\urlstyle{same}",
				"\input{chp}",
			]), file=fptr)

			result = tolatex(article[0], None)
		else:
			result = tolatex(parser.syntax, None)
		print(result, file=fptr)

	del latex_path[-1]

flag = None
paths = []
for arg in sys.argv[1:]:
	if arg[0] == "-":
		flag = arg
	elif flag:
		if flag == "-o" or flag == "--output":
			latex_outpath = arg
		flag = None
	elif "ref" in arg:
		paths.insert(0, arg)
	else:
		paths.append(arg)

for path in paths:
	convert_file(path)

