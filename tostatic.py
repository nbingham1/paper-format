#!/usr/bin/python3

from pyhtml.parse import *
from pyhtml import html
import sys
import os.path
import re
from lxml import etree
from shutil import copyfile
import importlib

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

def div2static(parent, idx, flags):
	if len(parent) > 0 and idx < len(parent[0].content):
		if "src" in parent[0].content[idx].attrs:
			load = load_file(parent[0].content[idx].attrs["src"]).content[0].content[0]
			tostatic([load], flags)
			parent[0].content[idx:idx+1] = load.content
			return len(load.content)
		else:
			tostatic([parent[0].content[idx]], flags)
	return 1

def figure2static(parent, idx, flags):
	if len(parent) > 0 and idx < len(parent[0].content):
		tostatic([parent[0].content[idx]], flags)
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
		tostatic([parent[0].content[idx]], flags)
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
		tostatic([parent[0].content[idx]], flags)
		if "id" in parent[0].content[idx].attrs:
			ref_id = parent[0].content[idx].attrs["id"]
			ref_num = len(ref_map)+1
			ref_map[ref_id] = ref_num
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
		tostatic([parent[0].content[idx]], flags)
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
		tostatic([parent[0].content[idx]], flags)
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
		tostatic([parent[0].content[idx]], flags)
		f = flags.copy()
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

def default2static(parent, idx, flags):
	if len(parent) > 0 and idx < len(parent[0].content):
		tostatic([parent[0].content[idx]], flags)
	return 1

def abbr2static(parent, idx, flags):
	if len(parent) > 0 and idx < len(parent[0].content):
		tostatic([parent[0].content[idx]], flags)
		abbr = parent[0].content[idx].text()
		title = ""
		if "title" in parent[0].content[idx].attrs:
			title = parent[0].content[idx].attrs["title"]
		abbr_defs[abbr] = title
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
	#'pre': pre2static,
	#'code': code2static,
	'a': a2static,
	'cite': cite2static,
	'table': table2static,
	'figure': figure2static,
}

def listOfAbbrev():
	if len(loa_section) > 0:
		lst = html.Ul()
		for abbr, title in sorted(abbr_defs.items()):
			item = html.Li()
			elem = html.Div(Class="toc-elem")
			elem << (html.Div() << abbr)
			elem << (html.Div(Class="toc-page") << title)
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
			elem << html.Div(Class="toc-page")
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
			elem << html.Div(Class="toc-page")
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
			elem << html.Div(Class="toc-page")
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

