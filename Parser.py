#!/usr/bin/python

import sys

s = ""
index = 0 # The index of the current char into |s|
vars = { }
exprs = []
lastExpr = 0
stack = []

verboseMode = False

# Read the file with the name specified by the second arg
#   (the first arg is the name of the executable)
if len(sys.argv) >= 2:
	s = open(sys.argv[1]).read()

name = ""
for arg in sys.argv[2:]:
	if (arg == "-v"): # Active verbose with the "-v" flag
		verboseMode = True
	else:
		name += ":$"
		try:
			vars[name] = int(arg)
		except:
			vars[name] = arg

def error(description, code = 1):
	print("@=== " + description + " ===*")
	print("Program exited on error.")
	exit(code)

def isskipable(c):
	return (c in [" ", "\n", "\t"]);

def isoperator(tok):
	return (tok in [":#", ":>", ":*", ":/", "%)", ":&", ":|"])

def opprecedence(op):
	if op == ":&" or op == ":|": return 30
	elif op == ":*" or op == ":/" or op == "%)": return 20
	elif op == ":#" or op == ":>": return 10
	return 0

def printop(tok): # DEBUG
	return ["+", "-", "*", "/", "%", "&&", "||"][[":#", ":>", ":*", ":/", "%)", ":&", ":|"].index(tok)]

def isstr(x):
	return isinstance(x, str)

def gettok():
	global s
	global index
	while 1:
		if index >= len(s): break
		
		c = s[index];
		if isskipable(c):
			index += 1
		else:
			if s[index:index+2] == "</": # End of program
				# set |index| out of bounds (to break the next call)
				index = len(s) + 1
				return "</3"
			else:
				tok = s[index:index+2]
				index += 2
				return tok
	return 0

def nexttok(skipSkipable = True):
	global s
	global index
	tmp_index = index
	while 1:
		if tmp_index >= len(s): break
		
		c = s[tmp_index];
		if skipSkipable and isskipable(c):
			tmp_index += 1
		else:
			if s[tmp_index:tmp_index+2] == "</": # End of program
				return "</3"
			else:
				tok = s[tmp_index:tmp_index+2]
				return tok
	return 0

class Expr:
	def description(self):
		return "*** expr ***"

class VarExpr(Expr):
	name = ""
	inversed = False
	def __init__(self, name, inversed):
		self.name = name
		self.inversed = inversed
		
	def description(self):
		return ("Inversed " if self.inversed else "") + "Var named \"" + self.name + "\""
		
	def execute(self):
		global vars
		if len(self.name) == 0:
			return 0
		elif self.inversed:
			return not(vars[self.name]) if (self.name in vars) else 0
		else: return vars[self.name] if (self.name in vars) else 0

class NamedVarExpr(Expr):
	expr = 0
	inversed = False
	def __init__(self, expr, inversed):
		self.expr = expr
		self.inversed = inversed
		
	def description(self):
		return ("Inversed " if self.inversed else "") + "Var from \"" + self.expr.description() + "\""
		
	def execute(self):
		global vars
		name = self.expr.execute()
		if len(name) == 0:
			return 0
		elif self.inversed:
			return not(vars[name]) if (name in vars) else name
		else: return vars[name] if (name in vars) else name

def parseVarExpr(inversed = False):
	if nexttok() == ":(":
		gettok() # Eat ":("
		expr = parseVarExpr(inversed)
		gettok() # Eat ":)"
		return NamedVarExpr(expr, inversed)
	else:
		name = ""
		while 1:
			if nexttok(False) == ":)":
				gettok() # Eat ":)"
				break
			else:
				global s
				global index
				name += s[index]
				index += 1
		return VarExpr(name, inversed)

class InitExpr(Expr):
	LHS = 0; RHS = 0
	def __init__(self, LHS, RHS):
		self.LHS = LHS
		self.RHS = RHS
		
	def description(self):
		return self.LHS.description() + " = " + self.RHS.description()
		
	def execute(self):
		global vars
		name = self.LHS.name if isinstance(self.LHS, VarExpr) else self.LHS.execute()
		vars[name] = self.RHS.execute()

def parseInitExpr():
	global lastExpr
	return InitExpr(lastExpr, parseExpr())

class InputExpr(Expr):
	input = 0
	def __init__(self, input):
		self.input = input
		
	def description(self):
		return "Input " + str(self.input)
		
	def execute(self):
		global vars
		name = ":$" * self.input
		return vars[name]

def parseInputExpr():
	i = 1 # The first ":$" has been already found (because this function is called)
	while 1:
		tok = nexttok(skipSkipable = False) # Don't skip skipable characters, ":$" must be concatened to count as only one input
		if tok == ":$":
			i += 1
			gettok() # Eat the ":$" found
		else: break
	return InputExpr(i)

class PrintExpr(Expr):
	exprs = []
	def __init__(self, exprs):
		self.exprs = exprs
		
	def description(self):
		desc = ""
		for expr in self.exprs:
			desc += expr.description() + ("" if expr == self.exprs[-1] else ", ")
		return "Print: (" + desc + ")"
		
	def execute(self):
		s = ""
		for expr in self.exprs:
			value = expr.execute()
			s += value if isstr(value) else str(value)
			s += " "
		print(s)

def parsePrintExpr():
	exprs = []
	while 1:
		expr = parseExpr()
		exprs.append(expr)
		if nexttok() == "@)":
			gettok() # Eat "@)"
			return PrintExpr(exprs)

class HelloPrintExpr(Expr):
	def description(self):
		return "Print: \"Hello, World!\"" 
		
	def execute(self):
		global vars
		input = 0
		if vars[":$"]:
			input = vars[":$"] if isstr(vars[":$"]) else str(vars[":$"])
		print("Hello, " + (input if input else "World!"))

def parseHelloPrintExpr():
	return HelloPrintExpr()

class BinOpExpr(Expr):
	LHS = 0; RHS = 0
	op = 0
	def __init__(self, LHS, op, RHS):
		self.LHS = LHS
		self.op = op
		self.RHS = RHS
		
	def description(self):
		return "(" + self.LHS.description() + " " + printop(self.op) + " " + self.RHS.description() + ")"
		
	def execute(self):
		# ----------------------------------- #
		#     | + | - | * | / | % | && | || | #
		# ----------------------------------- #
		# n,n | x | x | x | x | x | x  | x  | #
		# s,n | x | x | x | x | x |    |    | #
		# s,s | x | x |   |   |   |    |    | #
		# ----------------------------------- #
		# "abc" + 3 = "abc3"; 3 + "abc" = "3abc"
		# "abc" + "def" = "abcdef"
		# "abcd" - 2 = "ab"
		# "abcd" - "bc" = "ad"
		# "abc" * 2 = "abcabc"
		# "abc" / 2 = "a"
		# "abc" % 2 = "bca"
		
		op = self.op
		LHS = self.LHS.execute()
		RHS = self.RHS.execute()
		
		if op == ":/" and not(isstr(RHS)) and int(RHS) == 0:
			print("@=== " + self.LHS.description() + " divised by zero: unexpected behaviour activated ===*")
			print("PrO6raw 3x1t3d.")
			exit(1)
		
		print( LHS,RHS )
		if not(isstr(LHS)) and not(isstr(RHS)): # n,n
			if   op == ":#": return LHS + RHS
			elif op == ":>": return LHS - RHS
			elif op == ":*": return LHS * RHS
			elif op == ":/": return LHS / RHS
			elif op == "%)": return LHS % RHS
			elif op == ":&": return LHS and RHS
			elif op == ":|": return LHS or RHS
		elif isstr(LHS) ^ isstr(RHS): # s,n
			if   op == ":#": return LHS + str(RHS) if isstr(LHS) else str(LHS) + RHS
			elif op == ":>": return LHS[:-RHS] if isstr(LHS) else RHS[:-LHS]
			elif op == ":*": return LHS*RHS
			elif op == ":/": return LHS[:int(RHS*len(LHS))] if isstr(LHS) else RHS[:int(LHS*len(RHS))]
			elif op == "%)":
				return LHS[len(LHS)-RHS:]+LHS[:len(LHS)-RHS] if isstr(LHS) else RHS[len(RHS)-LHS:]+RHS[:len(RHS)-LHS]
		else: # s,s
			if   op == ":#": return LHS + RHS
			elif op == ":>": return LHS.replace(RHS, "")
		# Show an assertion: no valid operation
		error("No valid operation for '" + self.LHS.description() + " " + op + " " + self.RHS.description() + "'")
		return

def parseOperand(): # VarExpr, NamedExpr, InputExpr, LengthFuncExpr
	expr = 0
	tok = gettok()
	if tok == ":(" or tok == "x(":
		expr = parseVarExpr(inversed = (tok == "x("))
	elif tok == ":$":
		expr = parseInputExpr()
	elif tok == "L)":
		expr = parseLengthFuncExpr()
	return expr

def parseBinOpExpr(LHS, op):
	
	ops = [op]
	outputRPN = [LHS]
	
	while 1:
		RHS = parseOperand()
		op = nexttok()
		if not(RHS) or not(isoperator(op)):
			break
		
		gettok() # Eat operator
		outputRPN.append(RHS)
		
		lastOp = ops[-1]
		if opprecedence(lastOp) >= opprecedence(op):
			rops = ops[::-1] # Reverse |ops|
			for rop in rops:
				if opprecedence(op) > opprecedence(rop):
					break
				outputRPN.append(rop)
				ops = ops[:-1]
		ops.append(op)
	
	outputRPN.append(RHS)
	
	rops = ops[::-1]
	outputRPN.extend(rops)
	
	binops = []
	for output in outputRPN:
		if isoperator(output):
			LHS = binops.pop()
			RHS = binops.pop()
			expr = BinOpExpr(RHS, output, LHS)
			binops.append(expr)
		else:
			binops.append(output)
	return binops[0]

class CommentExpr(Expr):
	comment = 0
	def __init__(self, comment):
		self.comment = comment
		
	def description(self):
		return "Comment: \"" + self.comment + "\""

def parseCommentExpr():
	comment = ""
	global s
	global index
	while s[index] != "\n":
		if index > len(s): break
		comment += s[index]
		index += 1
	return CommentExpr(comment)

class NopExpr(Expr):
	def description(self):
		return "Paku paku"

def parseNopExpr():
	return NopExpr()

class ExitExpr(Expr):
	code = 0
	def __init__(self, code = 0):
		self.code = code
	
	def description(self):
		return "Exit(" + str(self.code) + ")"
	
	def execute(self):
		exit(self.code)

def parseExitExpr():
	return ExitExpr(0)

class LoopExpr(Expr):
	condition = 0
	thenExprs = []
	thelseExprs = []
	def __init__(self, condition, thenExprs, thelseExprs):
		self.condition = condition
		self.thenExprs = thenExprs
		self.thelseExprs = thelseExprs
		
	def description(self):
		str = "Loop: " + self.condition.description() + " | "
		for expr in self.thenExprs:
			if canExecute(expr):
				str += expr.description() + ("" if expr == self.thenExprs[-1] else ", ")
		str += " | "
		for expr in self.thelseExprs:
			if canExecute(expr):
				str += expr.description() + ("" if expr == self.thelseExprs[-1] else ", ")
		return str + " |"
		
	def execute(self):
		cond = self.condition.execute()
		if not(len(cond) > 0 if isstr(cond) else cond > 0):
			# Thelse block
			for expr in self.thelseExprs:
				if canExecute(expr): expr.execute()
		else:
			# Then block
			while 1:
				cond = self.condition.execute()
				if not(len(cond) > 0 if isstr(cond) else cond > 0):
					return
				for expr in self.thenExprs:
					if canExecute(expr): expr.execute()

def parseLoopExpr():
	global lastExpr
	
	condition = 0
	while nexttok() != "|)":
		condition = parseExpr()
		if isinstance(condition, Expr):
			lastExpr = condition
	gettok() # Eat "|)"
	
	thenExprs = []
	while nexttok() != "8)":
		expr = parseExpr()
		thenExprs.append(expr)
		if isinstance(expr, Expr):
			lastExpr = expr
	gettok() # Eat "8)"
	
	thelseExprs = []
	while nexttok() != "8}":
		expr = parseExpr()
		thelseExprs.append(expr)
		if isinstance(expr, Expr):
			lastExpr = expr
	gettok() # Eat "8}"
	
	return LoopExpr(condition, thenExprs, thelseExprs)

class LengthFuncExpr(Expr):
	expr = 0
	def __init__(self, expr):
		self.expr = expr
		
	def description(self):
		return "Length of: \"" + self.expr.description() + "\""
		
	def execute(self):
		v = self.expr.execute()
		return len(v) if isstr(v) else 0

def parseLengthFuncExpr():
	return LengthFuncExpr(parseExpr())

### Stack management ###
class PushExpr(Expr):
	expr = 0
	def __init__(self, expr):
		self.expr = expr
		
	def description(self):
		return "Push: \"" + self.expr.description() + "\""
		
	def execute(self):
		global stack
		stack.append(self.expr.execute())

def parsePushExpr():
	return PushExpr(parseExpr())

class PopExpr(Expr):
	expr = 0
	def __init__(self, expr):
		self.expr = expr
		
	def description(self):
		return "Pop to: \"" + self.expr.description() + "\""
		
	def execute(self):
		global stack
		global vars
		name = self.expr.name if isinstance(self.expr, VarExpr) else self.expr.execute()
		vars[name] = stack.pop()

def parsePopExpr():
	return PopExpr(parseExpr())

class ClearExpr(Expr):
	def description(self):
		return "Clear stack"
		
	def execute(self):
		global stack
		stack = []
		
def parseClearExpr():
	return ClearExpr()

class UnknownExpr(Expr):
	tok = 0
	def __init__(self, tok):
		self.tok = tok
		
	def description(self):
		return "Unknown expr: \"" + self.tok + "\""

def parseUnknownExpr():
	global s
	global index
	tok = s[index-2:index]
	return UnknownExpr(tok)

def canExecute(e):
	for c in [InitExpr, PrintExpr, HelloPrintExpr,  ExitExpr, LoopExpr,  PushExpr, PopExpr, ClearExpr]:
		if isinstance(e, c): return True
	return False

def parseExpr():
	expr = 0
	
	tok = gettok()
	if not(tok): return
	
	elif tok == ":(" or tok == "x(":
		expr = parseVarExpr(inversed = (tok == "x("))
	elif tok == "=;":
		expr = parseInitExpr()
	elif tok == ":$":
		expr = parseInputExpr()
	elif tok == ":@":
		expr = parsePrintExpr()
	elif tok == ":B":
		expr = parseHelloPrintExpr()
	elif tok == ";)":
		expr = parseCommentExpr()
	elif tok == "L)":
		expr = parseLengthFuncExpr()
	elif tok == ":P":
		expr = parsePushExpr()
	elif tok == ":O":
		expr = parsePopExpr()
	elif tok == ":D":
		expr = parseClearExpr()
	elif tok == ":v":
		expr = parseNopExpr()
	elif tok == "8|":
		expr = parseLoopExpr()
	elif tok == "#0":
		expr = parseExitExpr()
	elif tok == "<3":
		return "-start-"
	elif tok == "</3":
		return "-end-"
	else:
		expr = parseUnknownExpr()
	
	# If the next token is an operator
	if isoperator(nexttok()):
		expr = parseBinOpExpr(expr, gettok())
	
	return expr

def parse():
	global exprs
	global lastExpr
	while 1:
		expr = parseExpr()
		if expr:
			if isinstance(expr, UnknownExpr):
				error(expr.description())
			exprs.append(expr)
			if isinstance(expr, Expr):
				lastExpr = expr
		else: break
	
	for expr in exprs:
		if canExecute(expr):
			if verboseMode:
				print("- " + expr.description())
			expr.execute()
parse()