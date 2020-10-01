formatSection = function(section, id, type) {
	elems = section.getElementsByTagName(type);
	for (var i = 0; i < elems.length; i++) {
		elems[i].setAttribute("ref-num", id + "." + (i+1));
		formatSection(elems[i], id + "." + (i+1), "sub" + type);
	}
}

formatAnchors = function() {
	var elems = document.getElementsByTagName("cite");
	for (var i = 0; i < elems.length; i++) {
		elems[i].innerHTML = "<div class=\"cite-ref\">[" + (i+1) + "]</div><div class=\"cite-txt\">" + elems[i].innerHTML + "</div>";
		elems[i].setAttribute("ref-num", i+1);
	}

	elems = document.getElementsByClassName("equation");
	for (var i = 0; i < elems.length; i++) {	
		elems[i].setAttribute("ref-num", i+1);
	}

	elems = document.getElementsByTagName("figure");
	var j = 1;
	for (var i = 0; i < elems.length; i++) {
		var text = elems[i].getElementsByTagName("figcaption");
		if (text.length > 0) {
			elems[i].setAttribute("ref-num", j);
			j++;
		}
	}

	elems = document.getElementsByTagName("table");
	for (var i = 0; i < elems.length; i++) {
		elems[i].setAttribute("ref-num", i+1);
	}

	/*elems = document.getElementsByTagName("section");
	for (var i = 0; i < elems.length; i++) {
		elems[i].setAttribute("ref-num", i+1);
		formatSection(elems[i], (i+1), "subsection");
	}*/
};

formatLinks = function() {
	var links = document.getElementsByTagName("a");
	for (var i = 0; i < links.length; i++) {
		raw = links[i].getAttribute("href");

		if (raw && raw.charAt(0) == '#') {
			urls = raw.split('-#');
			var ref = [null, null];
			if (urls[0])
				ref[0] = document.querySelector(urls[0]);
			if (urls[1]) {
				ref[1] = document.querySelector('#' + urls[1]);
				links[i].setAttribute("href", urls[0]);
			}

			if (ref[0] && links[i].innerHTML.length == 0) {
				var tag = ref[0].tagName.toLowerCase();
				var cls = ref[0].className.toLowerCase();
				var id = ref[0].getAttribute('ref-num');
				
				if (ref[1]) {
					id += "-" + ref[1].getAttribute('ref-num');
				}

				if (tag == "cite") {
					links[i].innerHTML += "["+id+"]";
				}
				else if (cls == "equation") {
					links[i].innerHTML += "("+id+")";
				}
				else if (tag == "figure") {
					links[i].innerHTML += "Fig. "+id;
				}
				else if (tag == "table") {
					links[i].innerHTML += "Table "+id;
				}
				else {
					links[i].innerHTML += "[??]";
				}
			}
		}
	}
};

pixelsPerInch = function(elem) {
	var test = document.createElement("div");
	test.style.height="1in";
	elem.appendChild(test);
	var ppi = test.clientHeight;
	elem.removeChild(test);
	return ppi;
}

var ppi = 96;//pixelsPerInch(toc[0]);
var pageHeight = 11 - 2*1.0;
var pageWidth = 8.5 - 2*1.0;
var pageBreakTags = ["figure", "pre", "table", "img"];
var flowBranchTags = ["subsection", "subsubsection", "subsubsubsection", "div", "ul", "ol", "dl", "li", "dd", "thead", "tbody"];
var flowLeafTags = ["p", "h1", "h2", "h3", "h4", "h5", "h6", "figcaption", "caption", "cite", "dt", "b", "code", "abbr", "a", "tr"];
var titlePerPage = 1.625/pageHeight;
var codeHeight = 2.0/9.0;
var hasCanvasAccess = true;
var lineHeight = 24.0/ppi;

textWidth = function(elem) {
	if (hasCanvasAccess) {
		var text = "";
		if (typeof elem === "string") {
			text = elem;
		} else {
			text = elem.textContent ? elem.textContent : elem.innerText;
		}
		var cvs = textWidth.cvs || document.getElementById("mycanvas");
		var myctx = cvs.getContext("2d");
		if (elem.tagName != null && elem.tagName.toLowerCase() == "cite") {
			myctx.font = "10pt Times New Roman";
		} else {
			myctx.font = "12pt Times New Roman";
		}
		var mt = myctx.measureText(text);
		if (mt != false) {
			return mt.width/ppi;
		} else {
			hasCanvasAccess = false;
		}
	}

	if (elem.tagName == null) {
		return 0.079545455*elem.length;
	} else {
		return elem.offsetWidth/ppi;
	}
}

tableWidth = function(elem) {
	var rows = elem.getElementsByTagName("tr");
	var widths = [];
	for (var i = 0; i < rows.length; i++) {
		for (var j = 0; j < rows[i].childNodes.length; j++) {
			while (j >= widths.length) {
				widths.push(0);
			}
			widths[j] = Math.max(widths[j], textWidth(rows[i].childNodes[j]));
		}
	}
	var width = 0;
	for (var i = 0; i < widths.length; i++)
		width += widths[i];
	return width;
}

textLines = function(elem, width) {
	/*var text = [];
	if (typeof elem === "string") {
		text = elem.split(' ');
	} else {
		text = (elem.textContent ? elem.textContent : elem.innerText).split(' ');
	}

	var lines = 1;
	var line = "";
	for (var i = 0; i < text.length; i++) {
		if (i == 0) {
			line += "\t"
		} else {
			line += " "
		}
		line += text[i];
		var lineWidth = textWidth(line);
		if (textWidth(line) > width) {
			lines += 1;
			line = text[i];
		}
	}
	return lines;*/
	return Math.ceil((textWidth(elem) + 0.25)/width);
}

textSize = function(elem, bound, line, offset) {
	remainder = (Math.ceil(offset) - offset)*pageHeight/line;
	if (remainder == 0) {
		remainder = pageHeight/line;
	}

	if (remainder < 1) {
		offset = Math.ceil(offset);
		remainder = pageHeight/line;
	}
	lines = textLines(elem, bound);
	var height = lines*line + 3.0/ppi;
	if (lines > remainder) {
		height += (remainder - Math.floor(remainder))*line;
	}
	elem.setAttribute("debug_lines", lines);
	elem.setAttribute("debug_bound", bound);
	elem.setAttribute("debug_height", height);
	return [bound, height];
}

imgSize = function(elem, bound) {
	var imgwidth = elem.naturalWidth;
	var imgheight = elem.naturalHeight;
	if (imgwidth == 0 || imgheight == 0) {
		imgwidth = elem.clientWidth;
		imgheight = elem.clientHeight;
	}

	var width = 0;
	var height = 0;
	if (elem.style.width != "") {
		width = parseInt(elem.style.width, 10)*bound/100;
		height = width*(imgheight/imgwidth);
	} else if (elem.style.maxWidth != "") {
		width = parseInt(elem.style.maxWidth, 10)*bound/100;
		if (imgwidth/ppi < width) {
			width = imgwidth/ppi;
			height = imgheight/ppi;
		} else {
			height = width*(imgheight/imgwidth);
		}
	} else {
		if (imgwidth/ppi < bound) {
			height = imgheight/ppi;
			width = imgwidth/ppi;
		} else {
			width = bound;
			height = bound*(imgheight/imgwidth);
		}
	}
	height += 3.0/ppi;
	elem.setAttribute("debug_width", width);
	elem.setAttribute("debug_height", height);
	return [width, height];
}

preSize = function(elem, bound) {
	var width = bound;
	if (elem.style.width != "") {
		width *= parseInt(elem.style.width, 10)/100;
	}

	var text = elem.textContent ? elem.textContent : elem.innerText;
	var height = 0;
	lines = text.split('\n');
	for (var j = 0; j < lines.length; j++) {
		height += textLines(lines[j], width)*codeHeight;
	}
	elem.setAttribute("debug_width", width);
	elem.setAttribute("debug_height", height);
	return [width, height];
}

figSize = function(elems, bound) {
	var offset_h = 0;
	var offset_v = 0;
	var maxHeight = 0;
	for (var i = 0; i < elems.length; i++) {
		var name = elems[i].tagName;
		if (name != null) {
			name = name.toLowerCase();
		}

		var size = [0,0];
		if (name == "figcaption") {
			size = textSize(elems[i], bound, 24.0/ppi, offset_v);
		} else if (name == "img") {
			size = imgSize(elems[i], bound);
		} else if (name == "pre") {
			size = preSize(elems[i], bound);
		}

		if (name != null) {
			elems[i].setAttribute("debug_offset_h", offset_h);
		}

		offset_h += size[0];
		if (offset_h > bound) {
			offset_h = size[0];
			offset_v += maxHeight;
			maxHeight = size[1];
		} else {
			if (size[1] > maxHeight) {
				maxHeight = size[1];
			}
		}

		if (name != null) {
			elems[i].setAttribute("debug_offset_v", offset_v);
		}
	}

	offset_v += maxHeight;
	return [bound, offset_v];
}

pageFlowNodes = function(elems, width, off) {
	var offset = off;
	for (var i = 0; i < elems.length; i++) {
		var name = elems[i].tagName;
		if (name != null) {
			name = name.toLowerCase();
		}

		if (elems[i].tagName == null) {
		} else if (flowLeafTags.includes(name)) {
			var height = 0;
			var lines = 0;
			if (name == "h1") {
				height = titlePerPage;
			} else if (["p", "caption", "figcaption", "cite", "a"].includes(name)) {
				var line = 24.0/ppi;
				if (["cite"].includes(name)) {
					line = 20.0/ppi;
				}
				height = textSize(elems[i], width, line, offset)[1]/pageHeight;
			} else if (["tr"].includes(name)) {
				height = lineHeight*1.25/pageHeight;
			} else if (["dt", "h2", "h3", "h4"].includes(name)) {
				height = lineHeight*2.5/pageHeight;
			} else {
				height = elems[i].offsetHeight/(pageHeight*ppi);
			}
			
			elems[i].setAttribute("page", offset);
			offset += height;
		} else if (pageBreakTags.includes(name)) {
			var height;
			if (name == "figure") {
				height = figSize(elems[i].childNodes, width)[1]/pageHeight;
			} else if (name == "img") {
				height = imgSize(elems[i], width)[1]/pageHeight;
			} else if (name == "pre") {
				height = preSize(elems[i], width)[1]/pageHeight;
			} else if (name == "table") {
				height = pageFlowNodes(elems[i].childNodes, Math.min(tableWidth(elems[i]), width), 0);
			} else {
				height = elems[i].offsetHeight/(pageHeight*ppi);
			}
			if (Math.ceil(offset) - offset < height) {
				offset = Math.ceil(offset);
			}

			elems[i].setAttribute("page", offset);
			offset += height;
		} else if (!elems[i].classList.contains("toc-page") && flowBranchTags.includes(name)) {
			if (elems[i].hasAttribute("page") && elems[i].getAttribute("page") != "") {
				offset = parseInt(elems[i].getAttribute("page"), 10);
			} else {
				elems[i].setAttribute("page", offset);
			}
			var subwidth = width;
			if (name == "dd")
				subwidth -= 0.5;

			offset = pageFlowNodes(elems[i].childNodes, subwidth, offset);
		} else if (name == "br") {
			offset += lineHeight/pageHeight;
		} else {
			//console.log(elems[i]);
		}
	}
	return offset;
}

pageFlowSection = function(el, off) {
	if (el.hasAttribute("page")) {
		off = parseInt(el.getAttribute("page"), 10);
	} else {
		el.setAttribute("page", off);
	}

	el.setAttribute("page", off);
	return Math.ceil(pageFlowNodes(el.childNodes, pageWidth, off));
}

pageFlow = function() {
	var sections = document.getElementsByTagName("section");
	var offset = 1;
	for (var i = 0; i < sections.length; i++) {
		offset = pageFlowSection(sections[i], offset);
	}
}

pageTableOfContents = function() {
	var toc = document.getElementById("table-of-contents");
	if (toc != null) {
		var items = toc.getElementsByClassName("toc-elem");
		for (var i = 0; i < items.length; i++) {
			var linkElems = items[i].getElementsByTagName("a");
			var pageElems = items[i].getElementsByClassName("toc-page");
			if (linkElems.length > 0 && pageElems.length > 0) {
				var name = linkElems[0].getAttribute('href');
				var h1 = document.getElementsByName(name.substr(1));
				if (h1.length > 0) {
					var page = h1[0].parentNode.getAttribute("page");
					pageElems[0].appendChild(document.createTextNode(Math.floor(page)));
				}
			}
		}
	}
}

pageListOfFigures = function() {
	var toc = document.getElementById("list-of-figures");
	if (toc != null) {
		var items = toc.getElementsByClassName("toc-elem");
		for (var i = 0; i < items.length; i++) {
			var linkElems = items[i].getElementsByTagName("a");
			var pageElems = items[i].getElementsByClassName("toc-page");
			if (linkElems.length > 0 && pageElems.length > 0) {
				var name = linkElems[0].getAttribute('href');
				var fig = document.getElementById(name.substr(1));
				if (fig != null) {
					var page = fig.getAttribute("page");
					pageElems[0].appendChild(document.createTextNode(Math.floor(page)));
				}
			}
		}
	}
}

pageListOfTables = function() {
	var toc = document.getElementById("list-of-tables");
	if (toc != null) {
		var items = toc.getElementsByClassName("toc-elem");
		for (var i = 0; i < items.length; i++) {
			var linkElems = items[i].getElementsByTagName("a");
			var pageElems = items[i].getElementsByClassName("toc-page");
			if (linkElems.length > 0 && pageElems.length > 0) {
				var name = linkElems[0].getAttribute('href');
				var fig = document.getElementById(name.substr(1));
				if (fig != null) {
					var page = fig.getAttribute("page");
					pageElems[0].appendChild(document.createTextNode(Math.floor(page)));
				}
			}
		}
	}
}

contentsOfSection = function(level, elem, ins, ppi) {
	var h1 = elem.getElementsByTagName("h" + level);
	if (h1.length > 0) {
		var ol = document.createElement("ol");
		var value = 1;
		var app = 1;
		for (var i = 0; i < h1.length; i++) {
			if (!h1[i].parentNode.classList.contains("page-skip")) {
				var text = h1[i].childNodes;
				var id = null;
				if (text.length > 0) {
					if (text[0].nodeType == Node.TEXT_NODE) {
						id = null;
						text = text[0];
					} else if (text[0].tagName.toLowerCase() == "a") {
						id = text[0].getAttribute('name');
						text = text[0].childNodes[0];
					}
				}
				var li = document.createElement("li");
				var cont = document.createElement("div");
				cont.setAttribute("class", "toc-elem");
				var chap = document.createElement("div");
				var textNode = document.createTextNode(text.nodeValue);
				if (h1[i].parentNode.classList.contains("counter-skip")) {
					li.setAttribute("class", "skip");
				} else if (h1[i].parentNode.classList.contains("appendix")) {
					li.setAttribute("value", app);
					li.classList.add("appendix");
					app += 1;
				} else {
					li.setAttribute("value", value);
					value += 1;
				}

				if (id != null) {
					var link = document.createElement("a");
					link.appendChild(textNode);
					
					link.setAttribute("href", "#" + id);
					link.setAttribute("class", "xref");
					chap.appendChild(link);
				} else {
					chap.appendChild(textNode);
				}
				cont.appendChild(chap);
				var pagenum = document.createElement("div");
				pagenum.setAttribute("class", "toc-page");
				cont.appendChild(pagenum);
				li.appendChild(cont); 

				var sec = h1[i].parentNode;
				if (sec.nodeType != Node.TEXT_NODE && level < 2) {
					contentsOfSection(level+1, sec, li, ppi);
				}
				ol.appendChild(li);
			}
		}

		ins.appendChild(ol);
	}
}


tableOfContents = function() {
	var toc = document.getElementById("table-of-contents");
	if (toc != null) {
		contentsOfSection(1, document, toc, ppi);
	}
}

listOfFigures = function() {
	var toc = document.getElementById("list-of-figures");
	if (toc != null) {
		var figures = document.getElementsByTagName("figure");
		if (figures.length > 0) {
			var ol = document.createElement("ol");
			for (var i = 0; i < figures.length; i++) {
				var text = figures[i].getElementsByTagName("figcaption");
				if (text.length > 0) {
					text = text[0].textContent ? text[0].textContent : text[0].innerText;
					var id = figures[i].getAttribute('id');

					var li = document.createElement("li");
					var cont = document.createElement("div");
					cont.setAttribute("class", "toc-elem");
					var chap = document.createElement("div");
					var textNode;
					if (text != null) {
						textNode = document.createTextNode(text);
					} else {
						textNode = document.createTextNode("Anonymous");
					}
					if (id != null) {
						var link = document.createElement("a");
						link.appendChild(textNode);
						
						link.setAttribute("href", "#" + id);
						link.setAttribute("class", "xref");
						chap.appendChild(link);
					} else {
						chap.appendChild(textNode);
					}
					cont.appendChild(chap);
					var pagenum = document.createElement("div");
					pagenum.setAttribute("class", "toc-page");
					cont.appendChild(pagenum);
					li.appendChild(cont); 
					ol.appendChild(li);
				}
			}
			
			toc.appendChild(ol);
		}
	}
}

listOfTables = function() {
	var toc = document.getElementById("list-of-tables");
	if (toc != null) {
		var tables = document.getElementsByTagName("table");
		if (tables.length > 0) {
			var ol = document.createElement("ol");
			for (var i = 0; i < tables.length; i++) {
				var text = tables[i].getElementsByTagName("caption");
				if (text.length > 0) {
					text = text[0].textContent ? text[0].textContent : text[0].innerText;
					var id = tables[i].getAttribute('id');

					var li = document.createElement("li");
					var cont = document.createElement("div");
					cont.setAttribute("class", "toc-elem");
					var chap = document.createElement("div");
					var textNode;
					if (text != null) {
						textNode = document.createTextNode(text);
					} else {
						textNode = document.createTextNode("Anonymous");
					}
					if (id != null) {
						var link = document.createElement("a");
						link.appendChild(textNode);
						
						link.setAttribute("href", "#" + id);
						link.setAttribute("class", "xref");
						chap.appendChild(link);
					} else {
						chap.appendChild(textNode);
					}
					cont.appendChild(chap);
					var pagenum = document.createElement("div");
					pagenum.setAttribute("class", "toc-page");
					cont.appendChild(pagenum);
					li.appendChild(cont); 
					ol.appendChild(li);
				}
			}
		
			toc.appendChild(ol);
		}
	}
}

listOfAbbreviations = function() {
	var toc = document.getElementById("list-of-abbreviations");
	if (toc != null) {
		var abbr_elems = document.getElementsByTagName("abbr");
		if (abbr_elems.length > 0) {
			var abbrs = new Map;
			for (var i = 0; i < abbr_elems.length; i++) {
				var page = abbr_elems[i].getAttribute("title");
				var text = abbr_elems[i].textContent ? abbr_elems[i].textContent : abbr_elems[i].innerText;
				abbrs.set(text, page);
			}

			keys = Array.from(abbrs.keys());
			keys.sort();
			var ol = document.createElement("ul");
			for (var i = 0; i < keys.length; i++) {
				var li = document.createElement("li");
				var cont = document.createElement("div");
				cont.setAttribute("class", "toc-elem");
				var chap = document.createElement("div");
				var textNode;
				if (text != null) {
					textNode = document.createTextNode(keys[i]);
				} else {
					textNode = document.createTextNode("Anonymous");
				}
				chap.appendChild(textNode);
				cont.appendChild(chap);
				var pagenum = document.createElement("div");
				pagenum.setAttribute("class", "toc-def");
				pagenum.appendChild(document.createTextNode(abbrs.get(keys[i])));
				cont.appendChild(pagenum);
				li.appendChild(cont); 
				ol.appendChild(li);
			}
		
			toc.appendChild(ol);
		}
	}
}

