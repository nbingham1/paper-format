#!/usr/bin/python3

from pyhtml.parse import *
from pyhtml import html
import sys
import os.path
import re
import latex
from lxml import etree
from shutil import copyfile
import importlib

latex_figures = []
latex_citations = []
latex_tables = []

latex_files = []
latex_path = []
latex_unresolved = {}
latex_outpath = ""
latex_module = None

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

def escape_ref(content):
	return content.replace(u'\n', u'').replace(u'\r', u'').replace(u'$', u'\\$').replace(u'%', u'\\%').replace(u'&', u'\\&')	

def remove_linebreaks(content):
	return str(content).replace(u'\n', u' ').replace(u'\r', u'')

def expand(s, grps):
	for i, grp in enumerate(grps):
		s = s.replace('\\' + str(i+1), grp)
	s = s.replace('\\\\', '\\')
	return s

def convert(matches, src):
	result = ""
	i = 0
	while i < len(src):
		found = False
		for m in matches:
			g = re.match(m[0], src[i:], flags=re.MULTILINE)
			if g:
				grps = list(g.groups())
				for j in range(0, len(grps)):
					grps[j] = convert(matches, grps[j])
				app = expand(m[1], grps)
				#app = g.expand(m[1])
				if len(result) > 0 and result[-1] == '$' and app[0] == '$':
					result = result[0:-1] + app[1:]
				else:
					result += app
				i += g.end()
				found = True
				break

		if not found:
			result += src[i]
			i += 1
	return result

def convert_code(content, lang, caption=False):
	src = "".join([str(c) for c in content]).strip()
	if lang in ["prs"]:
		matches = [
			(r'\.{([^}]*)}', r'$_{\\text{\1}}$'),
			(r'->', r'$\\rightarrow$'),
			(r'~', r'$\\neg$'),
			(r'\&', r'$\\wedge$'),
			(r'\|', r'$\\vee$'),
			(r'<=', r'$\\leq$'),
			(r'>=', r'$\\geq$'),
			(r'!=', r'$\\neq$'),
			(r'==', r'='),
			(r'\.\.\.', r'$\\cdots$'),
			(r'\+(\s*(?:[\/\n]|$))', r'$\\uparrow$\1'),
			(r'-(\s*(?:[\/\n]|$))', r'$\\downarrow$\1'),
			(r'\.([a-zA-Z0-9_]+)', r'$_{\\text{\1}}$'),
		]
		result = convert(matches, src)
	elif lang in ["chp"]:
		matches = [
			(r'\.{([^}]*)}', r'$_{\\text{\1}}$'),
			(r'->', r'$\\rightarrow$'),
			(r'\|\|', r'$\\parallel$'),
			(r'\\par', r'$\\parallel$'),
			(r'\*\[', r'$*$['),
			(r'\\\[', r'['),
			(r'\[\]', r'$\\vrectangle$'),
			(r'\\\*', r'$\\bullet$'),
			(r'\\ring', r'$\\circ$'),
			(r'~', r'$\\neg$'),
			(r'\&', r'$\\wedge$'),
			(r'\|', r'$\\vee$'),
			(r'<=', r'$\\leq$'),
			(r'>=', r'$\\geq$'),
			(r'!=', r'$\\neq$'),
			(r'==', r'='),
			(r'\\:', r':'),
			(r':=', r':='),
			(r':', r'|'),
			(r'\.\.\.', r'$\\cdots$'),
			(r'\+(\s*(?:[\/;,:\]\)=\n!\?*]|$))', r'$\\uparrow$\1'),
			(r'-(\s*(?:[\/;,:\]\)=\n!\?*]|$))', r'$\\downarrow$\1'),
			(r'\.([a-zA-Z0-9_]+)', r'$_{\\text{\1}}$'),
			(r'#([a-zA-Z0-9_][a-zA-Z0-9_]*)', r'$\\overline{\\mbox{\1}}$'),
		]
		result = convert(matches, src)
	else:
		if not lang:
			print(src)
			print()
		result = src
	return result

def get_lang(tag, parent):
	lang = ""
	if "class" in tag.attrs:
		cls = tag.attrs["class"].split()
		for c in cls:
			if c.startswith("language-"):
				lang = c[9:]
	if not lang and parent and "lang" in parent.usr:
		lang = parent.usr["lang"]
	return lang

def process_usr(tag, result, parent, is_arg=False):
	if parent:
		result.usr = parent.usr.copy()

	if tag.name == "pre":
		result.usr["pre"] = True

	if tag.name == "figure":
		result.usr["figure"] = True

	if is_arg:
		result.usr["arg"] = True
	
	lang = get_lang(tag, parent)
	if lang:
		result.usr["lang"] = lang

def default2latex(tag, parent):
	if tag.name not in ["section", "subsection", "subsubsection", "div", "document", "html", "body"]:
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
	if "src" in tag.attrs:
		src = tag.attrs["src"]
		splt = os.path.splitext(src)
		result = latex.Input(splt[0])	
		process_usr(tag, result, parent)
		convert_file(src)
		return result

	return default2latex(tag, parent)

def header2latex(tag, parent):
	result = latex.Group([], "\n")
	process_usr(tag, result, parent)
	result << tolatex(tag.content, result)
	result << latex.Cmd("maketitle")
	return result

def hN2latex(tag, parent):
	index = int(tag.name[1:])
	result = latex.Group()

	section = latex.Section("", index-1)
	process_usr(tag, section, parent)
	if 'pass' in section.usr:
		section.usr['pass'].append('a')
	else:
		section.usr['pass'] = ['a']
	section.args = [latex.Group()]
	process_usr(tag, section.args[0], section)
	section.args[0] << tolatex([tag.content[0]], section.args[0])

	result << section
	if isinstance(tag.content[0], html.Tag) and tag.content[0].name == "a" and "name" in tag.content[0].attrs:
		result << latex.Cmd("label", [tag.content[0].attrs["name"]])
	return result

def p2latex(tag, parent):
	if "abstract" in parent.usr and len(tag.content) > 0 and isinstance(tag.content[0], html.Tag) and len(tag.content[0].content) > 0:
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
	result << "\n\n"
	return result

def code2latex(tag, parent):
	lang = get_lang(tag, parent)

	if "pre" in parent.usr:
		page = latex.Env("minipage", args=[latex.Group(["0.95", latex.Cmd("linewidth", inline=True)])], inline=False)
		process_usr(tag, page, parent)
		result = latex.Env("lstlisting", args=[("mathescape",)])
		process_usr(tag, result, parent)
		result << convert_code(tag.content, lang, "arg" in parent.usr)
		page << latex.Cmd("singlespacing")
		page << result
		pre = latex.Group()
		pre << latex.Cmd("newbox", ["\\mybox"])
		box = latex.Env("lrbox", ["\\mybox"])
		box << latex.Cmd("noindent")
		box << page
		pre << box
		pre << latex.Cmd("colorbox", ["code_bg", latex.Cmd("usebox", [latex.Cmd("mybox")])])
		return pre
	else:
		#color = latex.Cmd("colorbox", ["code_bg"], inline=True)
		result = latex.Cmd("protect\\lstinline", args=[("mathescape, columns=fixed",)], inline=True, d_open=u'!', d_close=u'!')
		process_usr(tag, result, parent)
		group = latex.Group()
		process_usr(tag, group, result)
		group << convert_code(tag.content, lang, "arg" in parent.usr).replace('\n', ' ')
		result.args.append(group)
		#color.args.append(result)
		return result #color

citation = re.compile("^#[a-z]*[0-9]{4}")
def a2latex(tag, parent):
	if "href" in tag.attrs:
		href = tag.attrs["href"]
		if len(href) > 0 and href[0] == "#":
			if "#" in href[1:]:
				result = latex.Cmd("cite", [], inline=True)
				process_usr(tag, result, parent, True)
				rng = href[1:].split('-#')
				if rng[0] in latex_citations and rng[1] in latex_citations:
					result.args = [','.join(latex_citations[latex_citations.index(rng[0]):latex_citations.index(rng[1])+1])]
			elif href[1:] in latex_citations:
				result = latex.Cmd("cite", [escape_ref(href[1:])], inline=True)
				process_usr(tag, result, parent, True)
			elif href[1:] in latex_figures:
				result = latex.Cmd("hyperref", [(escape_ref(href[1:]),)], inline=True)
				process_usr(tag, result, parent, True)
				result.args.append("Fig. " + str(latex_figures.index(href[1:])+1))
			elif tag.content:
				result = latex.Cmd("hyperref", [(escape_ref(href[1:]),)], inline=True)
				process_usr(tag, result, parent, True)
				result.args.append(latex.Group(tolatex(tag.content, parent)))
			elif href[1:] not in latex_unresolved:
				result = latex.Cmd("hyperref", [(escape_ref(href[1:]),)], inline=True)
				process_usr(tag, result, parent, True)
				latex_unresolved[href[1:]] = [result]
			else:
				result = latex.Cmd("hyperref", [(escape_ref(href[1:]),)], inline=True)
				process_usr(tag, result, parent, True)
				latex_unresolved[href[1:]].append(result)
			return result
		else:
			result = latex.Cmd("href", [escape_ref(href)], inline=True)
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
	result << "\n"
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

def dl2latex(tag, parent):
	result = latex.Env("description")
	process_usr(tag, result, parent)
	result << tolatex(tag.content, result)
	return result

def dt2latex(tag, parent):
	result = latex.Group()
	process_usr(tag, result, parent)
	result << latex.Cmd("item", [(latex.Group(tolatex(tag.content, result)),)], inline=True)
	result << latex.Cmd("hfill", inline=True)
	result << latex.Cmd("\\", inline=True)
	return result

def dd2latex(tag, parent):
	result = latex.Group()
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

	cnt = []
	cap = None
	for elem in tag.content:
		if isinstance(elem, html.Tag) and elem.name == "caption":
			cap = elem
		else:
			cnt.append(elem)

	result = latex.Env("table", args=[("ht!",)])
	process_usr(tag, result, parent)
	table = latex.Env("tabular")
	cols = 0
	for td in tag["tr"][0].content:
		if isinstance(td, html.Tag):
			if "colspan" in td.attrs:
				cols += int(td.attrs["colspan"])
			else:
				cols += 1

	table.args = [" | ".join(["c" for _ in range(0, cols)])]
	process_usr(tag, table, result)
	table << tolatex(cnt, table)
	result << latex.Cmd("small")	
	result << latex.Cmd("centering")	
	result << table
	if cap is not None:
		result << tolatex(cap, result)
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
	result << tolatex([elem for elem in tag.content if isinstance(elem, html.Tag)], result)
	return result

def td2latex(tag, parent):
	result = None
	if "colspan" in tag.attrs:
		result = latex.Cmd("multicolumn", [int(tag.attrs["colspan"]), "c"], inline=True)

	cell = latex.Cmd("makecell", inline=True)
	process_usr(tag, cell, parent)
	cell.args = [latex.Group(tolatex(tag.content, cell))]

	if result is not None:
		result.args.append(cell)
		return result
	else:
		return cell

def figure2latex(tag, parent):
	figure = latex.Env("figure", args=[("ht!",)])
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

def caption2latex(tag, parent):
	result = latex.Cmd("caption")
	process_usr(tag, result, parent, True)
	result.args = [latex.Group(tolatex(tag.content, result))]
	return result

def abbr2latex(tag, parent):
	result = latex.Group()
	if "title" in tag.attrs and tag.attrs["title"]:
		nom = latex.Cmd("nomenclature")
		process_usr(tag, nom, parent, True)
		nom.args = [latex.Group(tolatex(tag.content, nom)), remove_linebreaks(tag.attrs["title"])]
		result << nom
	result << tolatex(tag.content, parent)
	return result
	

def img2latex(tag, parent):
	if "src" in tag.attrs:
		src = tag.attrs["src"]
		path = os.path.dirname(src)

		
		outsrc = os.path.join(latex_outpath, src)
		if not os.path.exists(os.path.dirname(outsrc)):
			try:
				os.makedirs(os.path.dirname(outsrc))
			except OSError as exc: # Guard against race condition
				if exc.errno != errno.EEXIST:
					raise

		if ".svg" in src:
			width = None
			if "style" in tag.attrs and tag.attrs["style"]:
				width = tag.attrs["style"].get("width")
				if not width:
					width = tag.attrs["style"].get("max-width")
				if "%" in width:
					width = float(width[0:-1])/100.0
				else:
					width = None

			outsrc = outsrc.replace(".svg", ".pdf")
			intime = os.path.getmtime(src)
			outtime = os.path.getmtime(outsrc)

			if intime > outtime:
				print("inkscape -D -z --file=\"" + src + "\" --export-pdf=\"" + outsrc + "\" --export-latex")
				os.system("inkscape -D -z --file=\"" + src + "\" --export-pdf=\"" + outsrc + "\" --export-latex")
			src = src.replace(".svg", ".pdf_tex")
			result = latex.Group()
			result << latex.Cmd("graphicspath", [path+'/'], d_open='{{', d_close='}}')
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
			copyfile(src, outsrc)
			result = latex.Cmd("includegraphics")
			process_usr(tag, result, parent, True)
			result.args = [("width=1.0\\columnwidth",), src]
			return result
	else:
		return default2latex(tag, parent)

def br2latex(tag, parent):
	return " \\\\ "
	#latex.Cmd("\\", inline=True)

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
	'dl': dl2latex,
	'li': li2latex,
	'dt': dt2latex,
	'dd': dd2latex,
	'center': center2latex,
	'table': table2latex,
	'thead': thead2latex,
	'tbody': tbody2latex,
	'tr': tr2latex,
	'td': td2latex,
	'th': td2latex,
	'figure': figure2latex,
	'figcaption': caption2latex,
	'caption': caption2latex,
	'img': img2latex,
	'br': br2latex,
	'mark': mark2latex,
	'i': i2latex,
	'abbr': abbr2latex,
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
		if "class" in tag.attrs and "web-only" in tag.attrs["class"]:
			return ""
		elif parent and parent.usr and 'skip' in parent.usr and tag.name in parent.usr['skip']:
			return ""
		elif parent and parent.usr and 'pass' in parent.usr and tag.name in parent.usr['pass']:
			result = latex.Group()
			process_usr(tag, result, parent)
			result << tolatex(tag.content, result)
			return result
		elif latex_module is not None and latex_module.has(tag):
			return latex_module.set(tag, parent)
		elif tag.name in handlers:
			return handlers[tag.name](tag, parent)
		else:
			return default2latex(tag, parent)
	elif isinstance(tag, html.STag):
		if "class" in tag.attrs and "web-only" in tag.attrs["class"]:
			return ""
		elif parent and parent.usr and 'skip' in parent.usr and tag.name in parent.usr['skip']:
			return ""
		elif parent and parent.usr and 'pass' in parent.usr and tag.name in parent.usr['pass']:
			return ""
		elif latex_module is not None and latex_module.has(tag):
			return latex_module.set(tag, parent)
		elif tag.name in handlers:
			return handlers[tag.name](tag, parent)
		else:
			print(tag)
			return ""
	else:
		return escape(tag, "figure" not in parent.usr)

def convert_file(path):
	name = os.path.join(latex_outpath, os.path.splitext(path)[0])

	#if len(latex_path) > 0:
	#	path = os.path.join(latex_path[-1], path)
	
	#latex_path.append(os.path.dirname(path))

	print(path)
	eparser = etree.HTMLParser(target = Parser())
	with open(path, 'r') as fptr:
		data = fptr.read()
		eparser.feed(data)
	parser = eparser.close()

	if not os.path.exists(os.path.dirname(name)):
		try:
			os.makedirs(os.path.dirname(name))
		except OSError as exc: # Guard against race condition
			if exc.errno != errno.EEXIST:
				raise
	
	with open(name + ".tex", 'w') as fptr:
		article = parser.syntax["article"]
		if article:
			print("\n".join([
				latex_module.setDocument() if latex_module is not None else "\\documentclass[12pt,a4paper]{report}",
				"\\nonstopmode",
				"\\usepackage[utf8]{inputenc}",
				"\\usepackage[pdftex]{graphicx}",
				"\\usepackage{amsmath}",
				"\\usepackage{dirtytalk}",
				"\\usepackage{hyperref}",
				"\\usepackage{listings}",
				"\\usepackage{stix}",
				#"\\usepackage{xcolor}",
				"\\usepackage{color,soul}",
				"\\usepackage[nocfg,norefpage,noprefix]{nomencl}",
				"\\usepackage{cite}",
				"\\usepackage{makecell}",
				"\\usepackage{multirow}",
				"\\usepackage{setspace}",
				"\\soulregister\\cite7",
				"\\soulregister\\ref7",
				"\\soulregister\\pageref7",
				"\\soulregister{\\protect}{0}",
				"\\soulregister{\\lstinline}{1}",
				"\\soulregister{\\bibitem}{1}",
				"\\soulregister{\\say}{1}",
				"\\definecolor{code_bg}{RGB}{245,242,240}",
				"\\setlength\\tabcolsep{1.5pt}",
				"\\hypersetup{",
				"		colorlinks=true,",
				"		linkcolor=blue,",
				"		filecolor=blue,",
				"		urlcolor=blue,",
				"}",
				"\\lstset{",
				"    xleftmargin=2mm,",
				"    xrightmargin=2mm,",
				"    tabsize=2,",
				"    keepspaces=true,",
				"}",
				"\\urlstyle{same}",
				"\input{chp}",
			]), file=fptr)

			result = tolatex(article[0], None)
		else:
			result = tolatex(parser.syntax, None)
		print(result, file=fptr)

	#del latex_path[-1]

flag = None
paths = []
for arg in sys.argv[1:]:
	if arg[0] == "-":
		flag = arg
	elif flag:
		if flag == "-o" or flag == "--output":
			latex_outpath = arg
		if flag == "-f" or flag == "--format":
			latex_module = importlib.import_module(arg)
			latex_module.load(tolatex, process_usr)
		flag = None
	elif "ref" in arg:
		paths.insert(0, arg)
	else:
		paths.append(arg)

for path in paths:
	convert_file(path)

