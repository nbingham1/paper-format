#!/usr/bin/python3

from pyhtml.parse import *
from pyhtml import html
import sys
import os.path
import re
from lxml import etree
from shutil import copyfile
import importlib

static_figures = {}
static_citations = {}
static_tables = {}
static_abbr = {}
static_unresolved = {}

static_outpath = ""

def load_file(path):
	eparser = etree.HTMLParser(target = Parser())
	with open(path, 'r') as fptr:
		data = fptr.read()
		eparser.feed(data)
	parser = eparser.close()
	return parser.syntax

def div2static(parent, idx):
	if len(parent) > 0 and idx < len(parent[0].content):
		if "src" in parent[0].content[idx].attrs:
			load = load_file(parent[0].content[idx].attrs["src"]).content[0].content[0]
			tostatic([load])
			parent[0].content[idx:idx+1] = load.content
			return len(load.content)
		else:
			tostatic([parent[0].content[idx]])
	return 1

def figure2static(parent, idx):
	if len(parent) > 0 and idx < len(parent[0].content):
		tostatic([parent[0].content[idx]])
		if "id" in parent[0].content[idx].attrs:
			fig_id = parent[0].content[idx].attrs["id"]
			fig_num = len(static_figures)+1
			static_figures[fig_id] = fig_num
			if fig_id in static_unresolved:
				lst = static_unresolved[fig_id]
				del static_unresolved[fig_id]
				for i in range(0, len(lst)):
					lst[i] << ("Fig. " + str(fig_num))
	return 1

def table2static(parent, idx):
	if len(parent) > 0 and idx < len(parent[0].content):
		tostatic([parent[0].content[idx]])
		if "id" in parent[0].content[idx].attrs:
			tab_id = parent[0].content[idx].attrs["id"]
			tab_num = len(static_tables)+1
			static_tables[tab_id] = tab_num
			if tab_id in static_unresolved:
				lst = static_unresolved[tab_id]
				del static_unresolved[tab_id]
				for i in range(0, len(lst)):
					lst[i] << ("Table " + str(tab_num))
	return 1

def cite2static(parent, idx):
	if len(parent) > 0 and idx < len(parent[0].content):
		tostatic([parent[0].content[idx]])
		if "id" in parent[0].content[idx].attrs:
			ref_id = parent[0].content[idx].attrs["id"]
			ref_num = len(static_citations)+1
			static_citations[ref_id] = ref_num
			if ref_id in static_unresolved:
				lst = static_unresolved[ref_id]
				del static_unresolved[ref_id]
				for i in range(0, len(lst)):
					if '#' in lst[i].attrs["href"][1:]:
						href = lst[i].attrs["href"][1:].split('-#')
						print(href)
						lst[i].attrs["href"] = '#' + href[0]
						lst[i] << ("[" + str(static_citations[href[0]]) + "-" + str(ref_num) + "]")
					else:
						lst[i] << ("[" + str(ref_num) + "]")
	return 1

def a2static(parent, idx):
	if len(parent) > 0 and idx < len(parent[0].content):
		tostatic([parent[0].content[idx]])
		if "href" in parent[0].content[idx].attrs:
			href = parent[0].content[idx].attrs["href"]
			if len(href) > 0 and href[0] == '#' and len(parent[0].content[idx].content) == 0:
				if '#' in href[1:]:
					href = href[1:].split('-#')
					print(href)
					print(static_unresolved.keys())
					if href[0] in static_citations and href[1] in static_citations:
						parent[0].content[idx] << ("[" + str(static_citations[href[0]]) + "-" + str(static_citations[href[1]]) + "]")
					elif href[1] in static_unresolved:
						static_unresolved[href[1]].append(parent[0].content[idx])
					else:
						static_unresolved[href[1]] = [parent[0].content[idx]]
				else:
					if href[1:] in static_figures:
						parent[0].content[idx] << ("Fig. " + str(static_figures[href[1:]]))
					elif href[1:] in static_tables:
						parent[0].content[idx] << ("Table " + str(static_tables[href[1:]]))
					elif href[1:] in static_citations:
						parent[0].content[idx] << ("[" + str(static_citations[href[1:]]) + "]")
					elif href[1:] in static_unresolved:
						static_unresolved[href[1:]].append(parent[0].content[idx])
					else:
						static_unresolved[href[1:]] = [parent[0].content[idx]]
	return 1

def default2static(parent, idx):
	if len(parent) > 0 and idx < len(parent[0].content):
		tostatic([parent[0].content[idx]])
	return 1

handlers = {
	'div': div2static,
	#'h1': hN2static,
	#'h2': hN2static,
	#'h3': hN2static,
	#'h4': hN2static,
	#'h5': hN2static,
	#'h6': hN2static,
	#'h7': hN2static,
	#'pre': pre2static,
	#'code': code2static,
	'a': a2static,
	'cite': cite2static,
	'table': table2static,
	'figure': figure2static,
}

def tostatic(parent):
	if len(parent) > 0:
		i = 0
		while i < len(parent[0].content):
			if isinstance(parent[0].content[i], html.Tag):
				if parent[0].content[i].name in handlers:
					i += handlers[parent[0].content[i].name](parent, i)
				else:
					i += default2static(parent, i)
			elif isinstance(parent[0].content[i], html.STag):
				if parent[0].content[i].name in handlers:
					i += handlers[parent[0].content[i].name](parent, i)
				else:
					i += 1
			elif isinstance(parent[0].content[i], str):
				if 'text' in handlers:
					i += handlers['text'](parent, i)
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
	tostatic([syntax.content[0]])
	print("<!DOCTYPE html>", file=fptr)
	print("".join(syntax.content[0].emit()), file=fptr)

