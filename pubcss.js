// https://stackoverflow.com/questions/30008114/how-do-i-promisify-native-xhr
function request(opts) {
  return new Promise(function (resolve, reject) {
    var xhr = new XMLHttpRequest();
    xhr.open(opts.method, opts.url, true);
    xhr.onload = function () {
      if (this.status >= 200 && this.status < 300) {
        resolve({
					obj: xhr.response,
					text: xhr.responseText,
					pass: opts.pass
				});
      } else {
        reject({
          status: this.status,
          text: xhr.statusText,
					pass: opts.pass
        });
      }
    };
    xhr.onerror = function () {
      reject({
        status: this.status,
        text: xhr.statusText,
				pass: opts.pass
      });
    };
    if (opts.headers) {
      Object.keys(opts.headers).forEach(function (key) {
        xhr.setRequestHeader(key, opts.headers[key]);
      });
    }
    var params = opts.params;
    // We'll need to stringify if we've been given an object
    // If we have a string, this is skipped.
    if (params && typeof params === 'object') {
      params = Object.keys(params).map(function (key) {
        return encodeURIComponent(key) + '=' + encodeURIComponent(params[key]);
      }).join('&');
    }
    xhr.send(params);
  });
}

includeHTML = function(elem) {
	var promises = [];
	var includes = elem.getElementsByTagName("div");
	for (var i = 0; i < includes.length; i++) {
		var file = includes[i].getAttribute("src");
		if (file) {
			promises.push(request({
				method: "GET",
				url: file,
				pass: includes[i]
			}).then(function (response) {
				response.pass.innerHTML = response.text;
				content = response.pass.childNodes;
				var result = []
				if (response.pass.parentNode != null) {
					for (var j = 0; j < content.length; j++) {
						var node = response.pass.parentNode.insertBefore(content[j], response.pass);
						result.push(includeHTML(node));
					}
					response.pass.parentNode.removeChild(response.pass);
				}

				return Promise.allSettled(result);
			}));
		}
	}

	return Promise.allSettled(promises);
};

formatSection = function(section, id, type) {
	elems = section.getElementsByTagName(type);
	for (var i = 0; i < elems.length; i++) {
		elems[i].setAttribute("ref-num", id + "." + (i+1));
		formatSection(elems[i], id + "." + (i+1), "sub" + type);
	}
}

formatAnchors = function() {
	return new Promise(function(resolve, reject) {
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

		elems = document.getElementsByTagName("section");
		for (var i = 0; i < elems.length; i++) {
			elems[i].setAttribute("ref-num", i+1);
			formatSection(elems[i], (i+1), "subsection");
		}

		resolve();
	});
};

formatLinks = function() {
	return new Promise(function(resolve, reject) {
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

				if (ref[0]) {
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
						links[i].innerHTML += id;
					}
				} else if (links[i].innerHTML.length == 0) {
					links[i].innerHTML += "[??]"
				}
			}
		}

		resolve();
	});
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
var pageHeight = 11 - 2*0.5;
var pageWidth = 8.5 - 2*0.62;
var pageBreakTags = ["figure", "pre", "table", "img"];
var flowBranchTags = ["subsection", "subsubsection", "subsubsubsection", "div", "ul", "ol", "dl", "li", "dd"];
var flowLeafTags = ["p", "h1", "h2", "h3", "h4", "h5", "h6", "figcaption", "caption", "cite", "dt", "b", "code", "abbr", "a"];
var titlePerPage = .8125/pageHeight;
var codesPerPage = 2.0/(9*pageHeight);
var hasCanvasAccess = true;

textHeight = function(elem) {
	if (hasCanvasAccess) {
		var text = elem.textContent ? elem.textContent : elem.innerText;
		const cvs = textHeight.cvs || document.getElementById("mycanvas");
		const myctx = cvs.getContext("2d");
		myctx.font = "12pt Times New Roman";
		var mt = myctx.measureText(text);
		if (mt != false) {
			return (1.5*14.0*Math.ceil(mt.width/(ppi*pageWidth)) + 3)/(ppi*pageHeight);
		} else {
			hasCanvasAccess = false;
			return elems[i].offsetHeight/(ppi*pageHeight);
		}
	} else {
		return elems[i].offsetHeight/(ppi*pageHeight);
	}
}

pageFlowNodes = function(elems, off) {
	var offset = off;
	for (var i = 0; i < elems.length; i++) {
		var name = elems[i].tagName;
		if (name != null) {
			name = name.toLowerCase();
		}

		if (elems[i].tagName == null) {
			//offset += elems[i].offsetHeight/(pageHeight*ppi);
		} else if (flowLeafTags.includes(name)) {
			elems[i].setAttribute("page", offset);

			var height = 0;
			if (name == "h1") {
				height = titlePerPage;
			} else if (["p", "caption", "figcaption", "cite", "a"].includes(name)) {
				height = textHeight(elems[i]);
			} else {
				height = elems[i].offsetHeight/(pageHeight*ppi);
			}

			elems[i].setAttribute("debug_height", height*ppi*pageHeight);
			offset += height;
		} else if (pageBreakTags.includes(name)) {
			var height;
			if (name == "figure") {
				height = pageFlowNodes(elems[i].childNodes, 0);
			} else if (name == "img") {
				height = elems[i].naturalHeight/(pageHeight*ppi);
				var width = elems[i].naturalWidth/ppi;
				if (width > pageWidth) {
					height *= pageWidth/width;
				}
			} else if (name == "pre") {
				var text = elems[i].textContent ? elems[i].textContent : elems[i].innerText;
				lines = (text.match(/\n/g) || '').length + 1;
				height = lines*codesPerPage + 0.5/(ppi*pageHeight);
			} else {
				height = elems[i].offsetHeight/(pageHeight*ppi);
			}
			if (Math.ceil(offset) - offset < height) {
				offset = Math.ceil(offset);
			}

			elems[i].setAttribute("page", offset);
			if (name == "figure") {
				offset = pageFlowNodes(elems[i].childNodes, offset);
			} else {
				offset += height;
				elems[i].setAttribute("debug_height", height*ppi*pageHeight);
			}
		} else if (!elems[i].classList.contains("toc-page") && flowBranchTags.includes(name)) {
			elems[i].setAttribute("page", offset);

			offset = pageFlowNodes(elems[i].childNodes, offset);
		} else if (name == "br") {
			offset += 1.5*12.0/(ppi*pageHeight);
		} else {
			console.log(elems[i]);
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
	return Math.ceil(pageFlowNodes(el.childNodes, off));
}

pageFlow = function() {
	return new Promise(function(resolve, reject) {
		var sections = document.getElementsByTagName("section");
		var offset = 1;
		for (var i = 0; i < sections.length; i++) {
			offset = pageFlowSection(sections[i], offset);
		}

		resolve();
	});
}

pageTableOfContents = function() {
	return new Promise(function(resolve, reject) {
		var toc = document.getElementsByClassName("table-of-contents");
		if (toc.length > 0) {
			var items = toc[0].getElementsByClassName("toc-elem");
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

		resolve();
	});
}

pageListOfFigures = function() {
	return new Promise(function(resolve, reject) {
		var toc = document.getElementsByClassName("list-of-figures");
		if (toc.length > 0) {
			var items = toc[0].getElementsByClassName("toc-elem");
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

		resolve();
	});
}

pageListOfTables = function() {
	return new Promise(function(resolve, reject) {
		var toc = document.getElementsByClassName("list-of-tables");
		if (toc.length > 0) {
			var items = toc[0].getElementsByClassName("toc-elem");
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

		resolve();
	});
}

contentsOfSection = function(level, elem, ins, ppi) {
	var h1 = elem.getElementsByTagName("h" + level);
	if (h1.length > 0) {
		var ol = document.createElement("ol");
		var value = 1;
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
	return new Promise(function(resolve, reject) {
		var toc = document.getElementsByClassName("table-of-contents");
		if (toc.length > 0) {
			contentsOfSection(1, document, toc[0], ppi);
		}

		resolve();
	});
}

listOfFigures = function() {
	return new Promise(function(resolve, reject) {
		var toc = document.getElementsByClassName("list-of-figures");
		if (toc.length > 0) {
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
				
				toc[0].appendChild(ol);
			}
		}

		resolve();
	});
}

listOfTables = function() {
	return new Promise(function(resolve, reject) {
		var toc = document.getElementsByClassName("list-of-tables");
		if (toc.length > 0) {
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
			
				toc[0].appendChild(ol);
			}
		}

		resolve();
	});
}

listOfAbbreviations = function() {
	return new Promise(function(resolve, reject) {
		var toc = document.getElementsByClassName("list-of-abbreviations");
		if (toc.length > 0) {
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
				for (const key of keys) {
					var li = document.createElement("li");
					var cont = document.createElement("div");
					cont.setAttribute("class", "toc-elem");
					var chap = document.createElement("div");
					var textNode;
					if (text != null) {
						textNode = document.createTextNode(key);
					} else {
						textNode = document.createTextNode("Anonymous");
					}
					chap.appendChild(textNode);
					cont.appendChild(chap);
					var pagenum = document.createElement("div");
					pagenum.setAttribute("class", "toc-page");
					pagenum.appendChild(document.createTextNode(abbrs.get(key)));
					cont.appendChild(pagenum);
					li.appendChild(cont); 
					ol.appendChild(li);
				}
			
				toc[0].appendChild(ol);
			}
		}

		resolve();
	});
}

