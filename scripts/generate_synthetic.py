import os
from pathlib import Path

files = {
    "off_by_one_1.py": """def get_last_element(lst):
    return lst[len(lst)] # Off by one

get_last_element([1, 2, 3])
""",
    "off_by_one_2.py": """def loop_array():
    arr = [10, 20, 30]
    for i in range(4): # Off by one
        print(arr[i])

loop_array()
""",
    "uninitialized_variable_1.py": """def calc_sum():
    for i in range(5):
        total += i # total uninitialized
    return total

calc_sum()
""",
    "uninitialized_variable_2.py": """def print_name():
    if False:
        name = "Bob"
    print(name) # name uninitialized

print_name()
""",
    "wrong_return_type_1.py": """def add_numbers(a, b):
    return str(a + b) # Returns string instead of int

result = add_numbers(5, 5)
if result > 0: # TypeError
    print("Positive")
""",
    "wrong_return_type_2.py": """def is_even(n):
    if n % 2 == 0:
        return "yes" # returns str instead of bool
    return "no"

if is_even(4) == True: # logic fails or type error elsewhere
    pass
else:
    raise TypeError("Expected boolean, got string") # force an error for the parser
""",
    "array_out_of_bounds_1.py": """def get_item():
    my_list = [1, 2, 3]
    return my_list[5] # out of bounds

get_item()
""",
    "array_out_of_bounds_2.py": """def traverse_matrix():
    matrix = [[1, 2], [3, 4]]
    return matrix[2][0] # out of bounds

traverse_matrix()
""",
    "infinite_loop_1.py": """def count_down(n):
    while n > 0:
        print(n)
        # Missing n -= 1
        if n == 5:
            raise RecursionError("infinite loop simulated") # forcefully raise so timeout doesn't just silence it as unknown
count_down(5)
""",
    "infinite_loop_2.py": """def find_item():
    i = 0
    while True:
        if i == -1:
            break
        i += 1
        if i > 1000:
            raise RecursionError("infinite loop simulated")
find_item()
""",
    "indentation_logic_1.py": """def greet():
print("Hello") # IndentationError

greet()
""",
    "indentation_logic_2.py": """def do_something():
    x = 1
     y = 2 # IndentationError
    return x + y

do_something()
""",
    "type_mismatch_1.py": """def combine(a, b):
    return a + b

combine("Hello", 5) # TypeError
""",
    "type_mismatch_2.py": """def multiply(text, times):
    return text * str(times) # TypeError

multiply("A", "3")
""",
    "logical_operator_confusion_1.py": """def check_val(x):
    if x = 5: # SyntaxError
        pass

check_val(5)
""",
    "logical_operator_confusion_2.py": """def check_both(a, b):
    if a == 1 and or b == 2: # SyntaxError
        pass

check_both(1, 2)
""",
    "missing_return_1.py": """def calculate_area(w, h):
    area = w * h
    # Missing return

result = calculate_area(5, 5)
if result > 20: # TypeError because result is None
    print("Big")
""",
    "missing_return_2.py": """def get_config():
    # missing return
    pass

conf = get_config()
print(conf["host"]) # TypeError: 'NoneType' object is not subscriptable
""",
    "redundant_condition_1.py": """def check_age(age):
    if age > 18:
        return True
    elif age > 18: # Redundant
        return False

# Forcing an error for the parser to catch
raise ValueError("Redundant Condition")
""",
    "redundant_condition_2.py": """def check_status(status):
    if status == "active" and status == "active": # Redundant
        pass

raise ValueError("Redundant Condition")
"""
}

def generate():
    out_dir = Path(r"c:\Users\Pramukh\Music\final_yr_project\data\synthetic\python")
    out_dir.mkdir(parents=True, exist_ok=True)
    
    for filename, content in files.items():
        filepath = out_dir / filename
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Generated {filepath}")

if __name__ == "__main__":
    generate()
