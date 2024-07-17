import re


class Calculator:
	def parse_input(self, raw_input: str) -> list:
		valid_characters = re.compile(r"([+/*\-\(\)\^])")
		input_with_spaces = re.sub(valid_characters, r" \1 ", raw_input)

		input_list = input_with_spaces.split()

		def is_floatable(n):
			n = n.replace(".", "", 1)
			return n.isnumeric()

		converted_list = [float(value) if is_floatable(value) else value for value in input_list]

		for value in converted_list:
			try:
				if not (isinstance(value, float) or re.search(valid_characters, value)):
					raise ValueError
			except ValueError:
				print(f"Better calc attempted with: {converted_list}")
				return []

		return converted_list

	def arith(self, parsed_list):
		calculation_map = {
			"^": (lambda a, b: a ** b),
			"*": (lambda a, b: a * b),
			"/": (lambda a, b: a / b),
			"+": (lambda a, b: a + b),
			"-": (lambda a, b: a - b),
		}

		for operator, func in calculation_map.items():
			while operator in parsed_list:
				op_index = parsed_list.index(operator)

				a = parsed_list[op_index - 1]
				b = parsed_list[op_index + 1]

				if operator == "/" and b == 0:
					raise ZeroDivisionError

				try:
					new_value = func(a, b)
				except OverflowError:
					return []

				parsed_list[op_index - 1] = new_value
				del parsed_list[op_index:op_index + 2]

		return parsed_list

	def handle_parenthesis(self, parsed_list: list):
		open_loc = 0
		close_loc = 0
		for i in range(len(parsed_list)):
			curr = parsed_list[i]
			if curr == "(":
				open_loc = i
			elif curr == ")":
				close_loc = i
				break

		rec_list = self.calculate(parsed_list[open_loc + 1:close_loc])
		new_list = parsed_list[:open_loc] + rec_list + parsed_list[close_loc + 1:]
		if len(new_list) == 1:
			return new_list[0]
		else:
			return self.calculate(new_list)

	def calculate(self, input_value):
		if isinstance(input_value, str):
			parsed_list = self.parse_input(input_value)
		else:
			parsed_list = input_value

		if len(parsed_list) % 2 == 0:
			raise ValueError

		if len(parsed_list) == 1:
			return parsed_list

		if "(" not in parsed_list and ")" not in parsed_list:
			return self.calculate(self.arith(parsed_list))
		else:
			return self.handle_parenthesis(parsed_list)

	def calc(self, input_value):
		try:
			return self.calculate(input_value)[0]
		except ValueError or ZeroDivisionError or OverflowError:
			return "Invalid input"
