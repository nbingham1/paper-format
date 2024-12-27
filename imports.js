imgLoad = function(elem) {
	var promises = [];
	var imgs = elem.getElementsByTagName("img");
	for (var i = 0; i < imgs.length; i++) {
		promises.push(new Promise(function(resolve, reject) {
			imgs[i].onload = function() { resolve(); }
		}));
	}
	return Promise.allSettled(promises);	
}

includeHTML = function(elem) {
	var includes = elem.getElementsByTagName("div");
	promises = [];
	for (var i = 0; i < includes.length; i++) {
		var file = includes[i].getAttribute("src");
		if (file) {
			const pass = includes[i];
			promises.push(fetch(file)
				.then(response => {
					return response.text()
				}).then(text => {
					pass.innerHTML = text;
					result = [];
					if (pass.parentNode != null) {
						for (var j = 0; j < pass.childNodes.length; j++) {
							result.push(imgLoad(pass.childNodes[j]));
							var node = pass.parentNode.insertBefore(pass.childNodes[j], pass);
							result.push(includeHTML(node));
						}
						pass.parentNode.removeChild(pass);
					}
					return Promise.allSettled(result);
				}));
		}
	}
	return Promise.allSettled(promises);
};

