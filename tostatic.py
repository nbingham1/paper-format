#!/usr/bin/python3

from pyhtml.parse import *
from pyhtml import html
import sys
import os.path
import re
from lxml import etree
from shutil import copyfile
import importlib

languageChp = [
	('comment', [
		r'(^|[^\\])\/\*[\s\S]*?\*\/',
		r'(^|[^\\:])\/\/.*',
	]),
	('node_long', (r'\.{([^}]*)}', '\\1')),
	('', [
			(r'->',     '\u2192'),
			(r'\|\|',   '\u2225'),
			(r'\*\[',   '\u2217['),
			(r'\\\[',   '['     ),
			(r'\[\]',   '\u25AF'),
			(r'\\\*',   '\u2022'),
			(r'\\ring', '\u2E30'),
			(r'~',      '\u00AC'),
			(r'\&',     '\u2227'),
			(r'\|',     '\u2228'),
			(r'<=',     '\u2264'),
			(r'>=',     '\u2265'),
			(r'!=',     '\u2260'),
			(r'==',     '='     ),
			(r'([^\\]):([^=]|$)',    '\\1|\\2'),
			(r'\\:',    ':'),
			(r'\.\.\.', '\u2026'),
			(r'\+(\s*(?:[\/;,:\]\)\u2225\u2192\u25AF\u2022\u2026\u2227\u2228\u2264\u2265\u2260=\n!\?*]|$))', '\u21BE\\1'),
			(r'-(\s*(?:[\/;,:\]\)\u2225\u2192\u25AF\u2022\u2026\u2227\u2228\u2264\u2265\u2260=\n!\?*]|$))',  '\u21C2\\1')
	]),
	('node', (r'\.([a-zA-Z0-9_]+)', '\\1')),
	('probe', (r'#([a-zA-Z0-9_][a-zA-Z0-9_]*)', '\\1')),
	('logic', '\u00AC|\u2227|\u2228'),
	('arithmetic', r'\+|-|\*|\/'),
	('compare', '\u2264|\u2265|\u2260|=|<|>'),
	('assign', '\u21BE|\u21C2|:='),
	('channel', r'!|\?'),
	('compose', '\u2225|;|,'),
	('control', '\u2217\[|\[|\]|\||\u25AF|\u2192'),
	('string', r'(["\'])(\\(?:\r\n|[\s\S])|(?!\1)[^\\\r\n])*\1'),
	('keyword', r'\b(skip|null)\b'),
	('boolean', r'\b(true|false)\b'),
	('function', r'[a-z0-9_]+(?=\()'),
	('number', r'\b-?(?:0x[\da-f]+|\d*\.?\d+(?:e[+-]?\d+)?)\b'),
]

languagePrs = [
	('comment', [
		r'(^|[^\\])\/\*[\s\S]*?\*\/',
		r'(^|[^\\:])\/\/.*',
	]),
	('node_long', (r'\.{([^}]*)}', '\\1')),
	('', [
			(r'->', '\u2192'),
			(r'~',  '\u00AC'),
			(r'\&', '\u2227'),
			(r'\|', '\u2228'),
			(r'<=', '\u2264'),
			(r'>=', '\u2265'),
			(r'!=', '\u2260'),
			(r'==', '='     ),
			(r'\.\.\.', '\u2026'),
			(r'\+(\s*(?:[\/\n]|$))', '\u21BE\\1'),
			(r'-(\s*(?:[\/\n]|$))',  '\u21C2\\1'),
	]),
	('node', (r'\.([a-zA-Z0-9_]*)', '\\1')),
	('logic', '\u00AC|\u2227|\u2228'),
	('arithmetic', r'\+|-|\*|\/'),
	('compare', '\u2264|\u2265|\u2260|=|<|>'),
	('assign', '\u21BE|\u21C2|:='),
	('string', r'(["\'])(\\(?:\r\n|[\s\S])|(?!\1)[^\\\r\n])*\1'),
	('keyword', r'\b(skip|null)\b'),
	('boolean', r'\b(true|false)\b'),
	('number', r'\b-?(?:0x[\da-f]+|\d*\.?\d+(?:e[+-]?\d+)?)\b'),
]

def doSub(code, label, exp):
	i = len(code[0].content)-1
	while i >= 0:
		if isinstance(code[0].content[i], html.Tag):
			doSub([code[0].content[i]], label, exp)
		elif isinstance(exp, tuple):
			rep = exp[1]
			matches = re.finditer(exp[0], code[0].content[i], flags=re.MULTILINE | re.UNICODE)
			if matches:
				for m in reversed(list(matches)):
					if label:
						code[0].content = code[0].content[0:i] + [code[0].content[i][0:m.start()], html.Tag("span", [m.expand(rep)], {"class":"token " + label}, inline=True), code[0].content[i][m.end():]] + code[0].content[i+1:]
					else:
						code[0].content[i] = code[0].content[i][0:m.start()] + m.expand(rep) + code[0].content[i][m.end():]
		elif label:
			matches = re.finditer(exp, code[0].content[i], flags=re.MULTILINE | re.UNICODE)
			if matches:
				for m in reversed(list(matches)):
					code[0].content = code[0].content[0:i] + [code[0].content[i][0:m.start()], html.Tag("span", [code[0].content[i][m.start():m.end()]], {"class":"token " + label}, inline=True), code[0].content[i][m.end():]] + code[0].content[i+1:]
		i -= 1

def unescape(elem):
	for i in range(0, len(elem[0].content)):
		if isinstance(elem[0].content[i], html.Tag):
			unescape([elem[0].content[i]])
		elif not isinstance(elem[0].content[i], html.STag):
			elem[0].content[i] = elem[0].content[i].replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&")

def escape(elem):
	for i in range(0, len(elem[0].content)):
		if isinstance(elem[0].content[i], html.Tag):
			escape([elem[0].content[i]])
		elif not isinstance(elem[0].content[i], html.STag):
			elem[0].content[i] = elem[0].content[i].replace("&", "&amp;").replace(">", "&gt;").replace("<", "&lt;")

def convert(code, lang):
	if code[0].content[0][0] == '\n':
		code[0].content[0] = code[0].content[0][1:]
	unescape(code);
	for label, exp in lang:
		if isinstance(exp, list):
			for e in exp:
				doSub(code, label, e)
		else:
			doSub(code, label, exp)
	escape(code)

figure_map = {}
ref_map = {}
table_map = {}
abbr_map = {}
unresolved = {}

section_titles = []
figure_caps = []
table_caps = []
abbr_defs = {}

static_outpath = ""

toc_section = []
lof_section = []
lot_section = []
loa_section = []

def load_file(path):
	eparser = etree.HTMLParser(target = Parser())
	with open(path, 'r') as fptr:
		data = fptr.read()
		eparser.feed(data)
	parser = eparser.close()
	return parser.syntax

def getFlags(parent, idx, flags):
	f = flags.copy()
	newcls = []
	if "class" in parent[0].content[idx].attrs:
		cls = parent[0].content[idx].attrs["class"].split(" ")
		for c in cls:
			if c.startswith("language-"):
				f["lang"] = c[9:]
			else:
				newcls.append(c)
	if "lang" in f:
		newcls.append("language-" + f["lang"])
	if newcls:
		parent[0].content[idx].attrs["class"] = " ".join(newcls)

	return f

def div2static(parent, idx, flags):
	if len(parent) > 0 and idx < len(parent[0].content):
		if "src" in parent[0].content[idx].attrs:
			load = load_file(parent[0].content[idx].attrs["src"]).content[0].content[0]
			tostatic([load], getFlags(parent, idx, flags))
			parent[0].content[idx:idx+1] = load.content
			return len(load.content)
		else:
			tostatic([parent[0].content[idx]], flags)
	return 1

def figure2static(parent, idx, flags):
	if len(parent) > 0 and idx < len(parent[0].content):
		tostatic([parent[0].content[idx]], getFlags(parent, idx, flags))
		if "id" in parent[0].content[idx].attrs:
			fig_id = parent[0].content[idx].attrs["id"]
			fig_num = len(figure_map)+1
			caption = parent[0].content[idx].get("figcaption")

			figure_map[fig_id] = fig_num
			figure_caps.append((fig_id, caption))
			if fig_id in unresolved:
				lst = unresolved[fig_id]
				del unresolved[fig_id]
				for i in range(0, len(lst)):
					lst[i] << ("Fig. " + str(fig_num))
	return 1

def table2static(parent, idx, flags):
	if len(parent) > 0 and idx < len(parent[0].content):
		tostatic([parent[0].content[idx]], getFlags(parent, idx, flags))
		if "id" in parent[0].content[idx].attrs:
			tab_id = parent[0].content[idx].attrs["id"]
			tab_num = len(table_map)+1
			caption = parent[0].content[idx].get("caption")

			table_map[tab_id] = tab_num
			table_caps.append((tab_id, caption))
			if tab_id in unresolved:
				lst = unresolved[tab_id]
				del unresolved[tab_id]
				for i in range(0, len(lst)):
					lst[i] << ("Table " + str(tab_num))
	return 1

def cite2static(parent, idx, flags):
	if len(parent) > 0 and idx < len(parent[0].content):
		tostatic([parent[0].content[idx]], getFlags(parent, idx, flags))
		if "id" in parent[0].content[idx].attrs:
			ref_id = parent[0].content[idx].attrs["id"]
			ref_num = len(ref_map)+1
			ref_map[ref_id] = ref_num
			parent[0].content[idx].content
			ref = html.Div(Class="cite-ref")
			ref << ("[" + str(ref_num) + "]")
			txt = html.Div(Class="cite-txt")
			txt.content = parent[0].content[idx].content
			parent[0].content[idx].content = [ref, txt]

			if ref_id in unresolved:
				lst = unresolved[ref_id]
				del unresolved[ref_id]
				for i in range(0, len(lst)):
					if '#' in lst[i].attrs["href"][1:]:
						href = lst[i].attrs["href"][1:].split('-#')
						lst[i].attrs["href"] = '#' + href[0]
						lst[i] << ("[" + str(ref_map[href[0]]) + "-" + str(ref_num) + "]")
					else:
						lst[i] << ("[" + str(ref_num) + "]")
	return 1

def a2static(parent, idx, flags):
	if len(parent) > 0 and idx < len(parent[0].content):
		tostatic([parent[0].content[idx]], getFlags(parent, idx, flags))
		if "href" in parent[0].content[idx].attrs:
			href = parent[0].content[idx].attrs["href"]
			if len(href) > 0 and href[0] == '#' and len(parent[0].content[idx].content) == 0:
				if '#' in href[1:]:
					href = href[1:].split('-#')
					if href[0] in ref_map and href[1] in ref_map:
						parent[0].content[idx] << ("[" + str(ref_map[href[0]]) + "-" + str(ref_map[href[1]]) + "]")
					elif href[1] in unresolved:
						unresolved[href[1]].append(parent[0].content[idx])
					else:
						unresolved[href[1]] = [parent[0].content[idx]]
				else:
					if href[1:] in figure_map:
						parent[0].content[idx] << ("Fig. " + str(figure_map[href[1:]]))
					elif href[1:] in table_map:
						parent[0].content[idx] << ("Table " + str(table_map[href[1:]]))
					elif href[1:] in ref_map:
						parent[0].content[idx] << ("[" + str(ref_map[href[1:]]) + "]")
					elif href[1:] in unresolved:
						unresolved[href[1:]].append(parent[0].content[idx])
					else:
						unresolved[href[1:]] = [parent[0].content[idx]]
	return 1

def section2static(parent, idx, flags):
	global toc_section
	global lof_section
	global lot_section
	global loa_section

	if len(parent) > 0 and idx < len(parent[0].content):
		tostatic([parent[0].content[idx]], getFlags(parent, idx, flags))
		if "id" in parent[0].content[idx].attrs:
			sid = parent[0].content[idx].attrs["id"]
			if sid == "table-of-contents":
				toc_section = [parent[0].content[idx]]
			elif sid == "list-of-figures":
				lof_section = [parent[0].content[idx]]
			elif sid == "list-of-tables":
				lot_section = [parent[0].content[idx]]
			elif sid == "list-of-abbreviations":
				loa_section = [parent[0].content[idx]]
	return 1

def hN2static(parent, idx, flags):
	if len(parent) > 0 and idx < len(parent[0].content):
		f = getFlags(parent, idx, flags)
		tostatic([parent[0].content[idx]], f)
		if "class" in parent[0].attrs:
			cls = parent[0].attrs["class"].split(" ")
			if "page-skip" in cls:
				f["page-skip"] = True
			if "counter-skip" in cls:
				f["counter-skip"] = True
			if "appendix" in cls:
				f["appendix"] = True

		section_titles.append([parent[0].content[idx], f])
	return 1

def abbr2static(parent, idx, flags):
	if len(parent) > 0 and idx < len(parent[0].content):
		tostatic([parent[0].content[idx]], getFlags(parent, idx, flags))
		abbr = parent[0].content[idx].text()
		title = ""
		if "title" in parent[0].content[idx].attrs:
			title = parent[0].content[idx].attrs["title"]
		abbr_defs[abbr] = title
	return 1

def code2static(parent, idx, flags):
	if len(parent) > 0 and idx < len(parent[0].content):
		f = getFlags(parent, idx, flags)
		if "lang" in f:
			if f["lang"] == "prs":
				convert([parent[0].content[idx]], languagePrs)
			elif f["lang"] == "chp":
				convert([parent[0].content[idx]], languageChp)
			else:
				tostatic([parent[0].content[idx]], f)
		else:
			tostatic([parent[0].content[idx]], f)
	return 1

def script2static(parent, idx, flags):
	print(parent[0].content[idx])
	del parent[0].content[idx]
	return 0

def default2static(parent, idx, flags):
	if len(parent) > 0 and idx < len(parent[0].content):
		tostatic([parent[0].content[idx]], getFlags(parent, idx, flags))
	return 1

handlers = {
	'div': div2static,
	'section': section2static,
	'h1': hN2static,
	'h2': hN2static,
	'h3': hN2static,
	'h4': hN2static,
	'h5': hN2static,
	'h6': hN2static,
	'h7': hN2static,
	'abbr': abbr2static,
	'code': code2static,
	'a': a2static,
	'cite': cite2static,
	'table': table2static,
	'figure': figure2static,
	'script': script2static,
}

def listOfAbbrev():
	if len(loa_section) > 0:
		lst = html.Ul()
		for abbr, title in sorted(abbr_defs.items()):
			item = html.Li()
			elem = html.Div(Class="toc-elem")
			elem << (html.Div() << abbr)
			elem << (html.Div(Class="toc-def") << title)
			item << elem
			lst << item
		loa_section[0] << lst

def listOfFigures():
	if len(lof_section) > 0:
		lst = html.Ol()
		for ref_id, caption in figure_caps:
			caption_string = ""
			if len(caption) > 0:
				caption_string = caption[0].text()

			item = html.Li()
			elem = html.Div(Class="toc-elem")
			elem << (html.Div() << (html.A(Class="xref", Href="#" + ref_id) << caption_string))
			elem << html.Div(Class="toc-page", Xref="#" + ref_id)
			item << elem
			lst << item
		lof_section[0] << lst

def listOfTables():
	if len(lot_section) > 0:
		lst = html.Ol()
		for ref_id, caption in table_caps:
			caption_string = ""
			if len(caption) > 0:
				caption_string = caption[0].text()
				
			item = html.Li()
			elem = html.Div(Class="toc-elem")
			elem << (html.Div() << (html.A(Class="xref", Href="#" + ref_id) << caption_string))
			elem << html.Div(Class="toc-page", Xref="#" + ref_id)
			item << elem
			lst << item
		lot_section[0] << lst

def subTableOfContents(titles, idx, level, top):
	lst = html.Ol()
	item = None
	value = 1
	app = 1

	if idx[0] < len(titles):
		cur = int(titles[idx[0]][0].name[1:])-1
	while idx[0] < len(titles) and cur >= level:
		if cur >= top or "page-skip" in titles[idx[0]][1]:
			idx[0] += 1
		elif cur > level:
			if item is None:
				item = html.Li()
			item << subTableOfContents(titles, idx, level+1, top)
		else:
			title_id = ""
			title_string = ""
			if len(titles[idx[0]]) > 0:
				if len(titles[idx[0]][0].content) > 0 and isinstance(titles[idx[0]][0].content[0], html.Tag) and titles[idx[0]][0].content[0].name == "a" and "name" in titles[idx[0]][0].content[0].attrs:
					title_id = titles[idx[0]][0].content[0].attrs["name"]
				title_string = titles[idx[0]][0].text()

			item = html.Li()
			if "counter-skip" in titles[idx[0]][1]:
				item.attrs["class"] = "skip"
			elif "appendix" in titles[idx[0]][1]:
				item.attrs["value"] = app
				item.attrs["class"] = "appendix"
				app += 1
			else:
				item.attrs["value"] = value
				value += 1

			elem = html.Div(Class="toc-elem")
			elem << (html.Div() << (html.A(Class="xref", Href="#" + title_id) << title_string))
			elem << html.Div(Class="toc-page", Xref="#" + title_id)
			item << elem
			lst << item
			idx[0] += 1
		if idx[0] < len(titles):
			cur = int(titles[idx[0]][0].name[1:])-1
	return lst

def tableOfContents():
	if len(toc_section) > 0:
		i = 0
		toc_section[0] << subTableOfContents(section_titles, [i], 0, 2)

def tostatic(parent, flags):
	if len(parent) > 0:
		i = 0
		while i < len(parent[0].content):
			if isinstance(parent[0].content[i], html.Tag):
				if parent[0].content[i].name in handlers:
					i += handlers[parent[0].content[i].name](parent, i, flags)
				else:
					i += default2static(parent, i, flags)
			elif isinstance(parent[0].content[i], html.STag):
				if parent[0].content[i].name in handlers:
					i += handlers[parent[0].content[i].name](parent, i, flags)
				else:
					i += 1
			elif isinstance(parent[0].content[i], str):
				if 'text' in handlers:
					i += handlers['text'](parent, i, flags)
				else:
					i += 1
			else:
				i += 1

flag = None
paths = []
for arg in sys.argv[1:]:
	if arg[0] == "-":
		flag = arg
	elif flag:
		if flag == "-o" or flag == "--output":
			static_outpath = arg
		flag = None
	elif "ref" in arg:
		paths.insert(0, arg)
	else:
		paths.append(arg)

name = os.path.join(static_outpath, os.path.splitext(paths[0])[0])
if not os.path.exists(os.path.dirname(name)):
	try:
		os.makedirs(os.path.dirname(name))
	except OSError as exc: # Guard against race condition
		if exc.errno != errno.EEXIST:
			raise

with open(name + "_static.html", 'w') as fptr:
	syntax = load_file(paths[0])
	tostatic([syntax.content[0]], dict())
	tableOfContents()
	listOfFigures()
	listOfTables()
	listOfAbbrev()
	print("<!DOCTYPE html>", file=fptr)
	print("".join(syntax.content[0].emit()), file=fptr)

