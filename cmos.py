import itertools

# Accept the input string
print("Enter the Boolean Expression")
expr = input().strip()

SYMBOLS = ['(',')','+','.','~', ' ']
PRECEDENCE = {'~':3,'.':2,'+':1,'(':0,')':0}

# Get the list of operands and opearations from the expression string
substr_start = 0
tokens = []
for index in range(len(expr)):

	if expr[index] in SYMBOLS:

		if substr_start < index:
			tokens.append(expr[substr_start:index])

		if expr[index] != ' ':
			tokens.append(expr[index])

		substr_start = index + 1

if(substr_start < len(expr)):
	tokens.append(expr[substr_start:len(expr)])

print(tokens)

# Now let us convert the infix expression to postfix expression
token_postfix = []
stack = []

for item in tokens:

	# Directly Pass an oparand.
	if item not in SYMBOLS:
		token_postfix.append(item)

	# In case open bracket, pass as well.
	elif ((item == "(")):
		stack.append(item)

	# In case of close brakcet - pop until close open bracket
	elif item == ')':
		while(stack[-1]!='('):
			pop = stack.pop()
			token_postfix.append(pop)
		stack.pop()

	# In case of operator - check conditions
	else:
		while((len(stack)!=0) and (PRECEDENCE.get(stack[-1]) >= PRECEDENCE.get(item))):
			token_postfix.append(stack.pop())
		stack.append(item)

while(len(stack)!=0):
	token_postfix.append(stack.pop())

print(token_postfix)


# Helper function - unpack the list of list to single list
def unpack_list(lst):
	new_lst = []
	for i in range(len(lst)):
		if(type(lst[i]) == list):
			new_lst = new_lst + unpack_list(lst[i])
		else:
			new_lst.append(lst[i])
	return new_lst


# NOT cannot be accomadated in a single PMOS or NMOS tree. So to reduce complexity, let us assume we are given NOT of all inputs and let us remove NOTS from the expression.
# Let us build a function to find the depth of NOT. Recursively get the effect of an opertor on operands. List the pos of the operands affected by that operator. Recursive Sols
REDUCED_SYMBOLS = ['+','.','~']
def depth_operator(operator,pos):
	
	depth_list = [pos+1]
	required_len = 2
	if(operator == '+' or operator == '.'):
		required_len = 3

	while(pos>=0):
		if((token_postfix[pos] not in REDUCED_SYMBOLS)):
			depth_list.append(pos)

		elif(token_postfix[pos] in REDUCED_SYMBOLS):
			return_val = depth_operator(token_postfix[pos],pos-1)
			required_len = required_len + return_val[1] - 1
			# if(token_postfix[pos] == '~'):
			# 	required_len = required_len - 1
			depth_list.append(unpack_list(return_val[0]))

		if(len(depth_list) == required_len):
			break

		pos = pos - 1;

	return [depth_list,required_len]


# Case - if last token is a '~', then ignore it in the process. if not add a '~' and consider that. Because CMOS is built for a complementary function.
if(token_postfix[-1] == '~'):
	token_postfix.pop()
else:
	token_postfix.append('~')

# Go through all NOTs in the list and find the depth_list. Eliminate common elements in each iterations as the affect of NOTs cancel each other
affected_list = []
for index in range(len(token_postfix)):
	if token_postfix[index] == '~':
		depth_list = depth_operator('~',index-1)[0]
		depth_list_flattened = unpack_list(depth_list)
		if(len(affected_list) == 0):
			affected_list = depth_list_flattened
		else:
			affected_list = list(set(affected_list).union(set(depth_list_flattened)).difference(set(affected_list).intersection(set(depth_list_flattened))))

print(token_postfix)
print(affected_list)

# Eliminate the NOTs. That is invert the operators and operands affected overall by the NOTs.
token_postfix_without_nots = []
for index in range(len(token_postfix)):
	if((token_postfix[index] in REDUCED_SYMBOLS) and (index in affected_list)):
		if(token_postfix[index] == '+'):
			token_postfix_without_nots.append('.')
		elif(token_postfix[index] == '.'):
			token_postfix_without_nots.append('+')

	elif((token_postfix[index] not in REDUCED_SYMBOLS) and (index in affected_list)):
		token_postfix_without_nots.append('-'+token_postfix[index])

	elif(token_postfix[index]!='~'):
		token_postfix_without_nots.append(token_postfix[index])

print(token_postfix_without_nots)
REDUCED_SYMBOLS = ['+','.']
# rename duplicates in token_postfix_without_nots
rename_lst = []
for i in range(len(token_postfix_without_nots)):
	item = token_postfix_without_nots[i]
	if item not in REDUCED_SYMBOLS:
		if(item in token_postfix_without_nots[:i]) :
			cnt = token_postfix_without_nots[:i].count(item)
			if(cnt > 0):
				rename_lst.append([i,cnt])

for item in rename_lst:
	token_postfix_without_nots[item[0]] = token_postfix_without_nots[item[0]] + "_dupl_"+str(item[1])

# Now that we have a reduced set of expressions, let us build the PMOS and NMOS tree.
# PMOS Tree

# The number of transistors in the PMOS network = # of inputs. Let us build a N*3 matrix to store transistor information. First lets find n.
n = 0
pure_tokens = []
for elem in token_postfix_without_nots:
	if elem not in REDUCED_SYMBOLS:
		n = n +1
		pure_tokens.append(elem)

print(pure_tokens)
pmos_netlist = [[-1,-1,-1]]*n

pmos_indx = 0
pst_stack = []

# ----Helper Function ------
def propagate_change(old_node,new_node,array):
	
	for index in range(len(array)):
		if(array[index][0] == old_node):
			array[index][0] = new_node

		if(array[index][2] == old_node):
			array[index][2] = new_node

# Do a postfix Eval - to get the info
for item in token_postfix_without_nots:
	
	if item not in REDUCED_SYMBOLS:
		pmos_netlist[pure_tokens.index(item)] = [pmos_indx,item,pmos_indx+1]
		pmos_indx = pmos_indx + 2
		pst_stack.append(item)

	elif item == '+':
		opnd_1 = pst_stack.pop()
		opnd_2 = pst_stack.pop()
		new_list = []

		# opnd_1 and opnd_2 have to be serially connected
		if(type(opnd_2) == list):
			new_src = pure_tokens.index(opnd_2[-1])
			opnd_2 = unpack_list(opnd_2)
			new_list.extend(opnd_2)
		else:
			new_src = pure_tokens.index(opnd_2)
			new_list.append(opnd_2)

		if(type(opnd_1) == list):
			old_src = pure_tokens.index(opnd_1[0])
			opnd_1 = unpack_list(opnd_1)
			new_list.extend(opnd_1)
		else:
			old_src = pure_tokens.index(opnd_1)
			new_list.append(opnd_1)

		propagate_change(pmos_netlist[old_src][0],pmos_netlist[new_src][2],pmos_netlist);
		pst_stack.append(new_list)


	elif item == '.':

		opnd_1 = pst_stack.pop()
		opnd_2 = pst_stack.pop()
		new_list = []

		if(type(opnd_2) == list):
			new_src = pure_tokens.index(opnd_2[0])
			new_drain = pure_tokens.index(opnd_2[-1])
			opnd_2 = unpack_list(opnd_2)
			new_list.extend(opnd_2)
		else:
			new_src = pure_tokens.index(opnd_2)
			new_drain = pure_tokens.index(opnd_2)
			new_list.append(opnd_2)

		if(type(opnd_1) == list):
			old_src = pure_tokens.index(opnd_1[0])
			old_drain = pure_tokens.index(opnd_1[-1])
			opnd_1 = unpack_list(opnd_1)
			new_list.extend(opnd_1)
		else:
			old_src = pure_tokens.index(opnd_1)
			old_drain = pure_tokens.index(opnd_1)
			new_list.append(opnd_1)

		propagate_change(pmos_netlist[old_src][0],pmos_netlist[new_src][0],pmos_netlist);
		propagate_change(pmos_netlist[old_drain][2],pmos_netlist[new_drain][2],pmos_netlist);
		pst_stack.append(new_list)

# Revert back the duplicates
for item in pmos_netlist:
	item_split = item[1].split("_")
	if(len(item_split) > 1 and item_split[1] == "dupl"):
		item[1] = item_split[0]

# Print PMOS Netlist
print("PMOS Network is:")
for item in pmos_netlist:
	print(item)

# Build NOT circuits if any in the PMOS ckt - same can be used in NMOS branch
not_lst = []
for item in pmos_netlist:
	if(item[1][0] == "-"):
		not_lst.append(item[1][1:])
		item[1] = "not_"+item[1][1:]

# Find vdd and out in pmos netlist
src = [i[0] for i in pmos_netlist]
drain = [i[2] for i in pmos_netlist]

for item in pmos_netlist:
	if(item[0] not in drain):
		item[0] = "vdd"

	if(item[2] not in src):
		item[2] = "out"

# Print PMOS Netlist
print("PMOS Network is:")
for item in pmos_netlist:
	print(item)

# Generate NMOS netlist - just opposite of pmos
nmos_netlist = [[-1,-1,-1]]*n
nmos_indx = 0
pst_stack = []

for item in token_postfix_without_nots:
	
	if item not in REDUCED_SYMBOLS:
		nmos_netlist[pure_tokens.index(item)] = [nmos_indx,item,nmos_indx+1]
		nmos_indx = nmos_indx + 2
		pst_stack.append(item)

	elif item == '.':
		opnd_1 = pst_stack.pop()
		opnd_2 = pst_stack.pop()
		new_list = []

		# opnd_1 and opnd_2 have to be serially connected
		if(type(opnd_2) == list):
			new_src = pure_tokens.index(opnd_2[-1])
			opnd_2 = unpack_list(opnd_2)
			new_list.extend(opnd_2)
		else:
			new_src = pure_tokens.index(opnd_2)
			new_list.append(opnd_2)

		if(type(opnd_1) == list):
			old_src = pure_tokens.index(opnd_1[0])
			opnd_1 = unpack_list(opnd_1)
			new_list.extend(opnd_1)
		else:
			old_src = pure_tokens.index(opnd_1)
			new_list.append(opnd_1)

		propagate_change(nmos_netlist[old_src][0],nmos_netlist[new_src][2],nmos_netlist);
		pst_stack.append(new_list)


	elif item == '+':
		opnd_1 = pst_stack.pop()
		opnd_2 = pst_stack.pop()
		new_list = []

		if(type(opnd_2) == list):
			new_src = pure_tokens.index(opnd_2[0])
			new_drain = pure_tokens.index(opnd_2[-1])
			opnd_2 = unpack_list(opnd_2)
			new_list.extend(opnd_2)
		else:
			new_src = pure_tokens.index(opnd_2)
			new_drain = pure_tokens.index(opnd_2)
			new_list.append(opnd_2)

		if(type(opnd_1) == list):
			old_src = pure_tokens.index(opnd_1[0])
			old_drain = pure_tokens.index(opnd_1[-1])
			opnd_1 = unpack_list(opnd_1)
			new_list.extend(opnd_1)
		else:
			old_src = pure_tokens.index(opnd_1)
			old_drain = pure_tokens.index(opnd_1)
			new_list.append(opnd_1)

		propagate_change(nmos_netlist[old_src][0],nmos_netlist[new_src][0],nmos_netlist);
		propagate_change(nmos_netlist[old_drain][2],nmos_netlist[new_drain][2],nmos_netlist);
		pst_stack.append(new_list)

# Revert back the duplicates
for item in nmos_netlist:
	item_split = item[1].split("_")
	if(len(item_split) > 1 and item_split[1] == "dupl"):
		item[1] = item_split[0]

# Elimiate Nots
for item in nmos_netlist:
	if(item[1][0] == "-"):
		item[1] = "not_"+item[1][1:]

# Find vdd and out in nmos netlist
src = [i[0] for i in nmos_netlist]
drain = [i[2] for i in nmos_netlist]

for item in nmos_netlist:
	if(item[0] not in drain):
		item[0] = "out"

	if(item[2] not in src):
		item[2] = "gnd"

# Print NMOS Netlist
print("NMOS Network is:")
for item in nmos_netlist:
	print(item)

# Write to file
file = open("output.sim","w")
# First lets us write header
file.write("| units: 100 tech: scmos format: MIT\n|type gate source drain length width\n|---- ---- ------ ----- ------ -----\n")

# Now let us write the NOTS if any.
for item in not_lst:
	file.write("p "+item+" vdd not_"+item+" 2 4\n")
	file.write("n "+item+" not_"+item+" gnd 2 4\n\n")

# Now let us write the PMOS netlist
for item in pmos_netlist:
	if(item[0]!="vdd"):
		item[0] = "pnode_"+str(item[0])
	if(item[2]!="out"):
		item[2] = "pnode_"+str(item[2])
	file.write("p "+item[1]+" "+item[0]+" "+item[2]+" 2 4\n")
file.write("\n")

# Let us write the NMOS netlist
for item in nmos_netlist:
	if(item[0]!="out"):
		item[0] = "nnode_"+str(item[0])
	if(item[2]!="gnd"):
		item[2] = "nnode_"+str(item[2])
	file.write("n "+item[1]+" "+item[0]+" "+item[2]+" 2 4\n")

# Close File
file.close()