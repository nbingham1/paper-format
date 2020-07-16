class Cmd:
	def __init__(self,
							 name,
							 args = None,
							 usr = None,
							 inline = False):
		self.name = name
		self.args = args if args else []
		self.usr = usr if usr else {}
		self.inline = inline

	def __str__(self):
		if self.inline:
			return self.emit()[0]
		else:
			return self.emit()[0] + u"\n"

	def emit(self, tab = u""):
		result = u"\\" + self.name
		for arg in self.args:
			if isinstance(arg, tuple):
				result += u"[" + str(arg[0]) + u"]"
			else:
				result += u"{" + str(arg) + u"}"
		return [result]

class Env:
	def __init__(self,
							 name,
							 args = None,
							 content = None,
							 usr = None,
							 inline = False):
		self.name = name
		self.args = args if args else []
		self.content = content if content else []
		self.usr = usr if usr else {}
		self.inline = inline

	def __str__(self):
		if self.inline:
			return u"".join(self.emit())
		else:
			return u"\n".join(self.emit()) + u"\n"

	def __lshift__(self, other):
		if isinstance(other, (list, tuple)):
			self.content += other
		else:
			self.content.append(other)
		return other

	def emit(self, tab = u""):
		result = u"\\begin{" + self.name + u"}"
		for arg in self.args:
			if isinstance(arg, tuple):
				result += u"[" + str(arg[0]) + u"]"
			else:
				result += u"{" + str(arg) + u"}"
		return [result] + [
			str(elem)
			for elem in self.content
		] + [
			u"\\end{" + self.name + u"}"
		]

class Group:
	def __init__(self,
							 content = None,
							 sep = "",
							 start = "",
							 end = "",
							 usr = None):
		self.content = content if content else []
		self.sep = sep
		self.start = start
		self.end = end
		self.usr = usr if usr else {}

	def __str__(self):
		return self.start + self.sep.join(self.emit()) + self.end

	def __lshift__(self, other):
		if isinstance(other, (list, tuple)):
			self.content += other
		else:
			self.content.append(other)
		return other

	def emit(self, tab = u""):
		return [
			str(elem)
			for elem in self.content
		]

class Section(Cmd):
	def __init__(self, title, level = 0, usr = None):
		Cmd.__init__(self,
			name = (u"sub"*level + u"section"),
			args = [title],
			usr = usr)

class Input(Cmd):
	def __init__(self, path, usr = None):
		Cmd.__init__(self,
			name = u"input",
			args = [path],
			usr = usr)


