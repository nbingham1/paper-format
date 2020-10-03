function waitFor(f) {
	return new Promise(function(resolve, reject) {
		f.call();
		resolve();
	});
}

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
						result.push(imgLoad(content[j]));
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

