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
			return self.emit()[0] + "\n"

	def emit(self, tab = ""):
		result = "\\" + self.name
		for arg in self.args:
			if isinstance(arg, tuple):
				result += "[" + str(arg[0]) + "]"
			else:
				result += "{" + str(arg) + "}"
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
			return "".join(self.emit())
		else:
			return "\n".join(self.emit()) + "\n"

	def __lshift__(self, other):
		if isinstance(other, (list, tuple)):
			self.content += other
		else:
			self.content.append(other)
		return other

	def emit(self, tab = ""):
		result = "\\begin{" + self.name + "}"
		for arg in self.args:
			if isinstance(arg, tuple):
				result += "[" + str(arg[0]) + "]"
			else:
				result += "{" + str(arg) + "}"
		return [result] + [
			str(elem)
			for elem in self.content
		] + [
			"\\end{" + self.name + "}"
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

	def emit(self, tab = ""):
		return [
			str(elem)
			for elem in self.content
		]

class Section(Cmd):
	def __init__(self, title, level = 0, usr = None):
		Cmd.__init__(self,
			name = ("sub"*level + "section"),
			args = [title],
			usr = usr)

class Input(Cmd):
	def __init__(self, path, usr = None):
		Cmd.__init__(self,
			name = "input",
			args = [path],
			usr = usr)


