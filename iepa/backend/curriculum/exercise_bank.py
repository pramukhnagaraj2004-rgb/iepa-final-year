"""
Exercise Bank — hardcoded question sets for the IEPA Python curriculum.
No database needed; this dict is the source of truth for all
theory/coding/resource content per concept.
"""

EXERCISE_BANK = {

    # ------------------------------------------------------------------
    # 1. indentation_logic
    # ------------------------------------------------------------------
    "indentation_logic": {
        "theory": [
            {
                "id": "indentation_logic_t1",
                "question": "Why does Python use indentation instead of curly braces?",
                "options": [
                    "A) Python has no concept of code blocks",
                    "B) Indentation defines block structure — it is not just style, it's syntax",
                    "C) Indentation is optional and only affects readability",
                    "D) Python converts indentation to braces automatically before running"
                ],
                "correct": "B",
                "explanation": "In Python, indentation is how the interpreter knows which lines belong to a block (like inside an if, for, or function). Unlike languages such as C or Java where {} mark blocks and whitespace is cosmetic, in Python inconsistent indentation is a syntax error because the interpreter can't tell where a block starts or ends."
            },
            {
                "id": "indentation_logic_t2",
                "question": "What happens if you mix tabs and spaces for indentation in the same block in Python 3?",
                "options": [
                    "A) Python automatically converts tabs to 4 spaces",
                    "B) It always raises a TabError or IndentationError",
                    "C) It works fine as long as the code looks aligned in your editor",
                    "D) Python ignores whitespace differences entirely"
                ],
                "correct": "B",
                "explanation": "Python 3 explicitly disallows ambiguous mixing of tabs and spaces within the same block — it will raise a TabError or IndentationError rather than guess your intent, because a tab and a group of spaces can look identical in an editor but mean different things to the parser."
            }
        ],
        "coding": [
            {
                "id": "indentation_logic_c1",
                "description": "This function should print 'positive' only when x > 0, but the print statement is indented incorrectly so it always runs.",
                "buggy_code": "def check(x):\n    if x > 0:\n    print('positive')\n\ncheck(-5)",
                "hint": "The print statement needs to be indented one level deeper, inside the if block.",
                "solution_check": "no error and 'positive' is NOT printed when called with -5",
                "explanation": "The print('positive') line was at the same indentation level as the if statement, so Python treated it as unconditional code outside the if block. Indenting it one level further places it inside the if, so it only runs when the condition is true."
            },
            {
                "id": "indentation_logic_c2",
                "description": "This loop is supposed to print each number, then print 'done' once after the loop finishes. Fix the indentation so 'done' only prints once.",
                "buggy_code": "for i in range(3):\n    print(i)\n    print('done')",
                "hint": "Dedent the second print so it's outside the for loop, not inside it.",
                "solution_check": "output shows 0,1,2 then 'done' printed exactly once at the end",
                "explanation": "Because print('done') was indented to match print(i), it was considered part of the loop body and ran on every iteration. Moving it back to column 0 (same level as 'for') places it after the loop instead of inside it."
            },
            {
                "id": "indentation_logic_c3",
                "description": "This function should return 'even' or 'odd', but the else block's return is nested incorrectly under the if, causing the else path to never work.",
                "buggy_code": "def parity(n):\n    if n % 2 == 0:\n        return 'even'\n        else:\n            return 'odd'",
                "hint": "The else must align with the if, not be indented as if it's inside the if block.",
                "solution_check": "returns 'odd' for parity(3) and 'even' for parity(4) with no error",
                "explanation": "An else clause must be at the same indentation level as its matching if — here it was indented further, making Python think it was a new (invalid) statement inside the if block, causing a SyntaxError. Aligning else with if fixes the structure."
            }
        ],
        "resources": [
            {"title": "Python Docs — Compound statements (indentation)", "url": "https://docs.python.org/3/reference/compound_stmts.html", "description": "Official reference on how indentation defines blocks in if/for/def/etc."},
            {"title": "W3Schools — Python Indentation", "url": "https://www.w3schools.com/python/gloss_python_indentation.asp", "description": "Beginner-friendly walkthrough of indentation rules with examples."},
            {"title": "GeeksforGeeks — Indentation in Python", "url": "https://www.geeksforgeeks.org/python/indentation-in-python/", "description": "Explains why Python enforces indentation and common indentation errors."}
        ]
    },

    # ------------------------------------------------------------------
    # 2. uninitialized_variable
    # ------------------------------------------------------------------
    "uninitialized_variable": {
        "theory": [
            {
                "id": "uninitialized_variable_t1",
                "question": "What error does Python raise when you reference a variable before assigning it a value?",
                "options": [
                    "A) SyntaxError",
                    "B) TypeError",
                    "C) NameError",
                    "D) Python silently treats it as None"
                ],
                "correct": "C",
                "explanation": "Python raises a NameError with a message like \"name 'x' is not defined\" when you try to use a variable that has never been assigned in an accessible scope. Unlike some languages, Python does not auto-declare variables with a default value — they must be assigned before use."
            },
            {
                "id": "uninitialized_variable_t2",
                "question": "A variable is assigned only inside an if branch that doesn't execute. What happens when the code later tries to use it?",
                "options": [
                    "A) It uses the value from the last time the program ran",
                    "B) It defaults to 0 or empty string depending on expected type",
                    "C) NameError, because the assignment line never ran, so the name was never created",
                    "D) Python throws a warning but continues with value None"
                ],
                "correct": "C",
                "explanation": "A variable only exists after its assignment statement actually executes. If that assignment is inside a branch that is skipped, the name is never bound, so referencing it afterward raises a NameError — Python doesn't pre-scan branches to reserve names with defaults."
            }
        ],
        "coding": [
            {
                "id": "uninitialized_variable_c1",
                "description": "This function tries to accumulate a total but never initializes 'total' before the loop.",
                "buggy_code": "def sum_list(nums):\n    for n in nums:\n        total += n\n    return total\n\nprint(sum_list([1, 2, 3]))",
                "hint": "You need to set total = 0 before the loop starts.",
                "solution_check": "prints 6 with no error",
                "explanation": "total += n is shorthand for total = total + n, which requires total to already exist. Since it was never initialized, Python raised a NameError (or UnboundLocalError) on the first iteration. Adding total = 0 before the loop gives it a starting value to add to."
            },
            {
                "id": "uninitialized_variable_c2",
                "description": "This code only assigns 'result' inside the if branch, then tries to print it regardless of which branch ran.",
                "buggy_code": "def label(n):\n    if n > 0:\n        result = 'positive'\n    print(result)\n\nlabel(-3)",
                "hint": "Add an else branch that assigns result for the negative/zero case too.",
                "solution_check": "no error and correct label prints for both positive and negative n",
                "explanation": "When n is not greater than 0, the if body never runs, so result is never created — the print(result) line then fails with a NameError. Adding an else: result = 'non-positive' (or similar) guarantees result always has a value before it's used."
            },
            {
                "id": "uninitialized_variable_c3",
                "description": "This function tries to track the largest number seen, but 'largest' is referenced before it's ever assigned.",
                "buggy_code": "def find_max(nums):\n    for n in nums:\n        if n > largest:\n            largest = n\n    return largest\n\nprint(find_max([3, 7, 2]))",
                "hint": "Initialize largest before the loop, e.g. to the first element or a very small number.",
                "solution_check": "prints 7 with no error",
                "explanation": "The comparison n > largest needs largest to exist before the loop even runs once. Initializing largest = nums[0] (or float('-inf')) before the loop gives it a starting point to compare against."
            }
        ],
        "resources": [
            {"title": "Python Docs — Naming and binding", "url": "https://docs.python.org/3/reference/executionmodel.html#naming-and-binding", "description": "Official explanation of when a name becomes bound in Python's execution model."},
            {"title": "W3Schools — Python Variables", "url": "https://www.w3schools.com/python/python_variables.asp", "description": "Basics of variable creation and assignment in Python."},
            {"title": "GeeksforGeeks — NameError in Python", "url": "https://www.geeksforgeeks.org/python/nameerror-name-is-not-defined-in-python/", "description": "Common causes of NameError, including uninitialized variables."}
        ]
    },

    # ------------------------------------------------------------------
    # 3. type_mismatch
    # ------------------------------------------------------------------
    "type_mismatch": {
        "theory": [
            {
                "id": "type_mismatch_t1",
                "question": "What happens when you try to concatenate a string and an integer with + in Python?",
                "options": [
                    "A) Python auto-converts the integer to a string",
                    "B) TypeError: can only concatenate str (not \"int\") to str",
                    "C) It returns the integer's ASCII representation appended to the string",
                    "D) It silently returns None"
                ],
                "correct": "B",
                "explanation": "Python is strongly typed, meaning it does not implicitly convert between unrelated types like str and int for + operations. You must explicitly convert with str(number) to concatenate it with a string, otherwise Python raises a TypeError rather than guessing your intent."
            },
            {
                "id": "type_mismatch_t2",
                "question": "input() in Python always returns what type, regardless of what the user types?",
                "options": [
                    "A) int if the input looks like a number, else str",
                    "B) str — always, even for numeric-looking input",
                    "C) It depends on the variable's previous type",
                    "D) float"
                ],
                "correct": "B",
                "explanation": "input() always returns a string, no matter what the user types. If you need a number, you must explicitly convert it with int() or float() — forgetting this is a very common source of type mismatch bugs when doing arithmetic on user input."
            }
        ],
        "coding": [
            {
                "id": "type_mismatch_c1",
                "description": "This code tries to build a greeting message by adding an int directly to a string.",
                "buggy_code": "age = 20\nmessage = 'You are ' + age + ' years old'\nprint(message)",
                "hint": "Wrap age in str() before concatenating.",
                "solution_check": "prints 'You are 20 years old' with no error",
                "explanation": "+ between a str and an int is undefined in Python — they're incompatible types for that operator. Converting age with str(age) makes both operands strings, which + can then concatenate."
            },
            {
                "id": "type_mismatch_c2",
                "description": "This code reads a number from input() and tries to double it, but forgets input() returns a string.",
                "buggy_code": "num = input('Enter a number: ')\ndoubled = num * 2\nprint(doubled)",
                "hint": "Convert num to an int (or float) before multiplying.",
                "solution_check": "for input '5', prints 10 (not '55')",
                "explanation": "Since num is a string, num * 2 repeats the string twice (e.g. '5' * 2 = '55') instead of doing arithmetic. Wrapping with int(num) converts it to a number first so * performs multiplication."
            },
            {
                "id": "type_mismatch_c3",
                "description": "This function averages a list of number-strings but doesn't convert them before summing.",
                "buggy_code": "def average(items):\n    return sum(items) / len(items)\n\nprint(average(['1', '2', '3']))",
                "hint": "Convert each item to a number (e.g. with a list comprehension using int()) before summing.",
                "solution_check": "prints 2.0 with no error",
                "explanation": "sum() cannot add strings numerically — it raises a TypeError because it tries to use + on strings the way it would on numbers, and the initial accumulator is 0 (an int), causing a str/int mismatch. Converting each element with int(x) first fixes it."
            }
        ],
        "resources": [
            {"title": "Python Docs — Built-in Types", "url": "https://docs.python.org/3/library/stdtypes.html", "description": "Reference for how Python's core types behave and interact."},
            {"title": "W3Schools — Python Type Casting", "url": "https://www.w3schools.com/python/python_casting.asp", "description": "How to convert between str, int, and float explicitly."},
            {"title": "GeeksforGeeks — TypeError in Python", "url": "https://www.geeksforgeeks.org/python/type-conversion-in-python/", "description": "Covers implicit vs explicit type conversion and common mismatch errors."}
        ]
    },

    # ------------------------------------------------------------------
    # 4. logical_operator_confusion
    # ------------------------------------------------------------------
    "logical_operator_confusion": {
        "theory": [
            {
                "id": "logical_operator_confusion_t1",
                "question": "Why does 'if x = 5:' raise a SyntaxError in Python, while 'if x == 5:' works?",
                "options": [
                    "A) = is assignment, == is comparison; conditions require comparison",
                    "B) Python requires quotes around numbers in conditions",
                    "C) = is not allowed anywhere in Python",
                    "D) There is no difference; both should work"
                ],
                "correct": "A",
                "explanation": "= assigns a value to a variable; == checks whether two values are equal. An if statement needs an expression that evaluates to True/False, and a bare assignment isn't such an expression in Python, so using = inside a condition is a SyntaxError."
            },
            {
                "id": "logical_operator_confusion_t2",
                "question": "What does 'not a == b' evaluate to compared to 'a != b'?",
                "options": [
                    "A) They are never equivalent",
                    "B) They are logically equivalent — both check whether a and b are different",
                    "C) 'not a == b' compares types while '!=' compares values",
                    "D) 'not a == b' always raises an error"
                ],
                "correct": "B",
                "explanation": "not a == b first evaluates a == b (True/False), then negates it — so it means 'the opposite of equal', which is exactly what a != b means directly. They're equivalent, though a != b is the clearer, idiomatic way to write it."
            }
        ],
        "coding": [
            {
                "id": "logical_operator_confusion_c1",
                "description": "This condition uses = instead of == and won't even run.",
                "buggy_code": "x = 10\nif x = 10:\n    print('ten')",
                "hint": "Use == for comparison, not =.",
                "solution_check": "prints 'ten' with no error",
                "explanation": "= is the assignment operator, not comparison. Python disallows assignment inside an if condition to prevent this exact confusion, raising a SyntaxError. Changing it to == performs the intended equality check."
            },
            {
                "id": "logical_operator_confusion_c2",
                "description": "This function should check if a number is between 1 and 10, but uses 'and' incorrectly, always returning True.",
                "buggy_code": "def in_range(n):\n    if 1 or n <= 10:\n        return True\n    return False\n\nprint(in_range(500))",
                "hint": "You need to compare n on both sides: 'n >= 1 and n <= 10', not just '1'.",
                "solution_check": "in_range(500) returns False, in_range(5) returns True",
                "explanation": "'if 1 or n <= 10' checks if the literal number 1 is truthy (which it always is) OR the second condition — so it's always True regardless of n. The fix compares n against both bounds explicitly: n >= 1 and n <= 10."
            },
            {
                "id": "logical_operator_confusion_c3",
                "description": "This function should reject empty strings, but the condition uses 'or' where 'and' logic is needed, letting invalid input through.",
                "buggy_code": "def is_valid(s):\n    if s != '' or s is not None:\n        return True\n    return False\n\nprint(is_valid(''))",
                "hint": "Think about what should make it False: it needs to be checked with 'and', not 'or', since both conditions must hold to be valid.",
                "solution_check": "is_valid('') returns False, is_valid('hi') returns True",
                "explanation": "With 'or', if s is not None (true for '') the whole condition is already True, so empty strings incorrectly pass. Using 'and' requires both s != '' AND s is not None to hold, correctly rejecting empty strings."
            }
        ],
        "resources": [
            {"title": "Python Docs — Boolean operations", "url": "https://docs.python.org/3/reference/expressions.html#boolean-operations", "description": "Official reference on and/or/not short-circuit behavior."},
            {"title": "W3Schools — Python Operators", "url": "https://www.w3schools.com/python/python_operators.asp", "description": "Overview of comparison vs assignment vs logical operators."},
            {"title": "GeeksforGeeks — Logical Operators in Python", "url": "https://www.geeksforgeeks.org/python/python-logical-operators/", "description": "Explains and/or/not with truth tables and examples."}
        ]
    },

    # ------------------------------------------------------------------
    # 5. infinite_loop
    # ------------------------------------------------------------------
    "infinite_loop": {
        "theory": [
            {
                "id": "infinite_loop_t1",
                "question": "What is the most common cause of an accidental infinite while loop?",
                "options": [
                    "A) Using a for loop instead of while",
                    "B) The loop's condition variable is never updated inside the loop body",
                    "C) Using too many print statements",
                    "D) Python loops always run forever unless told to stop with return"
                ],
                "correct": "B",
                "explanation": "A while loop keeps running as long as its condition is True. If the variable the condition depends on is never changed inside the loop, the condition never becomes False, so the loop never terminates. This is by far the most common cause of accidental infinite loops."
            },
            {
                "id": "infinite_loop_t2",
                "question": "In a while loop meant to count down to zero, what bug would cause it to loop forever?",
                "options": [
                    "A) Incrementing the counter instead of decrementing it",
                    "B) Using a for loop syntax instead",
                    "C) Printing the counter each iteration",
                    "D) Starting the counter at 0 instead of 1"
                ],
                "correct": "A",
                "explanation": "If a countdown loop is supposed to decrease a counter toward zero but instead increments it (or forgets to update it), the counter moves away from — or never reaches — the stopping condition, so the loop never exits."
            }
        ],
        "coding": [
            {
                "id": "infinite_loop_c1",
                "description": "This countdown loop never decrements i, so it never reaches the stopping condition.",
                "buggy_code": "def countdown(n):\n    while n > 0:\n        print(n)\n    return 'done'",
                "hint": "Decrement n inside the loop, e.g. n -= 1.",
                "solution_check": "loop terminates and returns 'done' for countdown(3)",
                "explanation": "n was never changed inside the loop, so the condition n > 0 stayed True forever. Adding n -= 1 inside the loop body ensures n eventually reaches 0, ending the loop."
            },
            {
                "id": "infinite_loop_c2",
                "description": "This loop is meant to double a number until it exceeds 100, but the update happens with the wrong operator, keeping the value from growing.",
                "buggy_code": "def grow(x):\n    while x < 100:\n        x = x - 2\n    return x\n\nprint(grow(1))",
                "hint": "The loop should multiply or add, not subtract, if x needs to reach 100.",
                "solution_check": "terminates and returns a value >= 100 for grow(1)",
                "explanation": "Subtracting from x moves it further from the target of 100, so the condition x < 100 never becomes False. Changing the update to something like x *= 2 (or x += 2) lets x actually approach and pass 100."
            },
            {
                "id": "infinite_loop_c3",
                "description": "This loop searches a list for a target but the index is never incremented on a mismatch, looping forever if the target isn't at index 0.",
                "buggy_code": "def find(lst, target):\n    i = 0\n    while i < len(lst):\n        if lst[i] == target:\n            return i\n    return -1\n\nprint(find([1, 2, 3], 3))",
                "hint": "Increment i inside the loop when the current element doesn't match.",
                "solution_check": "returns 2 for find([1,2,3], 3) without hanging",
                "explanation": "i was never incremented, so if lst[0] didn't match the target, the loop kept checking the same index forever. Adding i += 1 (e.g. in an else branch, or after the if) lets the loop advance through the list."
            }
        ],
        "resources": [
            {"title": "Python Docs — while statement", "url": "https://docs.python.org/3/reference/compound_stmts.html#the-while-statement", "description": "Official reference on while loop semantics."},
            {"title": "W3Schools — Python While Loops", "url": "https://www.w3schools.com/python/python_while_loops.asp", "description": "Basics of while loops including break and common pitfalls."},
            {"title": "GeeksforGeeks — Infinite Loops in Python", "url": "https://www.geeksforgeeks.org/python/infinite-loops-in-python/", "description": "Explains causes of infinite loops and how to avoid them."}
        ]
    },

        # ------------------------------------------------------------------
    # 6. off_by_one
    # ------------------------------------------------------------------
    "off_by_one": {
        "theory": [
            {
                "id": "off_by_one_t1",
                "question": "What does range(5) actually produce?",
                "options": [
                    "A) 1, 2, 3, 4, 5",
                    "B) 0, 1, 2, 3, 4",
                    "C) 0, 1, 2, 3, 4, 5",
                    "D) 1, 2, 3, 4"
                ],
                "correct": "B",
                "explanation": "range(5) generates 5 numbers starting at 0 and stopping before 5: 0, 1, 2, 3, 4. The stop value is exclusive, which is a very common source of off-by-one bugs when people expect it to include 5 or start at 1."
            },
            {
                "id": "off_by_one_t2",
                "question": "For a list of length n, what is the valid index range?",
                "options": [
                    "A) 1 to n",
                    "B) 0 to n",
                    "C) 0 to n-1",
                    "D) 1 to n-1"
                ],
                "correct": "C",
                "explanation": "List indices are zero-based, so a list of length n has valid indices 0 through n-1. Using index n (or looping with <= n) goes one past the last valid element and raises an IndexError."
            }
        ],
        "coding": [
            {
                "id": "off_by_one_c1",
                "description": "This loop is meant to print indices 0 through len(lst)-1 but uses <= instead of <, going one too far.",
                "buggy_code": "def print_indices(lst):\n    for i in range(len(lst) + 1):\n        print(lst[i])\n\nprint_indices([10, 20, 30])",
                "hint": "Use range(len(lst)) instead of range(len(lst) + 1).",
                "solution_check": "prints 10, 20, 30 with no IndexError",
                "explanation": "range(len(lst) + 1) produces one extra index beyond the last valid one (e.g. for a 3-element list it includes index 3, which doesn't exist), causing an IndexError. range(len(lst)) generates exactly the valid indices 0..n-1."
            },
            {
                "id": "off_by_one_c2",
                "description": "This function is meant to sum numbers from 1 to n inclusive, but range excludes the upper bound, so it stops one short.",
                "buggy_code": "def sum_to_n(n):\n    total = 0\n    for i in range(1, n):\n        total += i\n    return total\n\nprint(sum_to_n(5))",
                "hint": "range's stop value is exclusive — use range(1, n + 1) to include n.",
                "solution_check": "sum_to_n(5) returns 15 (1+2+3+4+5)",
                "explanation": "range(1, n) stops before n, so it only sums 1 through n-1. Since the function needs to include n itself, the range must be range(1, n + 1)."
            },
            {
                "id": "off_by_one_c3",
                "description": "This function should return the last element of a list but uses len(lst) as the index instead of len(lst) - 1.",
                "buggy_code": "def last_element(lst):\n    return lst[len(lst)]\n\nprint(last_element([4, 5, 6]))",
                "hint": "The last valid index is len(lst) - 1, not len(lst).",
                "solution_check": "returns 6 for [4, 5, 6] with no error",
                "explanation": "For a 3-element list, len(lst) is 3, but the valid indices are 0, 1, 2 — index 3 is out of bounds. Using lst[len(lst) - 1] (or simply lst[-1]) correctly gets the last element."
            }
        ],
        "resources": [
            {"title": "Python Docs — range()", "url": "https://docs.python.org/3/library/stdtypes.html#range", "description": "Official reference on how range's start/stop/step work, including exclusivity of stop."},
            {"title": "W3Schools — Python range() Function", "url": "https://www.w3schools.com/python/ref_func_range.asp", "description": "Simple examples of range() behavior."},
            {"title": "GeeksforGeeks — Off-by-one error", "url": "https://www.geeksforgeeks.org/python/off-by-one-error-in-python/", "description": "Explains common off-by-one mistakes in loops and indexing."}
        ]
    },

    # ------------------------------------------------------------------
    # 7. array_out_of_bounds
    # ------------------------------------------------------------------
    "array_out_of_bounds": {
        "theory": [
            {
                "id": "array_out_of_bounds_t1",
                "question": "What exception does Python raise when you access a list index that doesn't exist?",
                "options": [
                    "A) KeyError",
                    "B) IndexError",
                    "C) ValueError",
                    "D) It returns None silently"
                ],
                "correct": "B",
                "explanation": "Accessing an index outside a list's valid range (e.g. lst[10] on a 3-element list) raises an IndexError with a message like 'list index out of range'. KeyError is for dictionaries, not sequence indexing."
            },
            {
                "id": "array_out_of_bounds_t2",
                "question": "What does lst[-1] refer to in a Python list?",
                "options": [
                    "A) An error, since negative indices aren't allowed",
                    "B) The first element",
                    "C) The last element",
                    "D) A random element"
                ],
                "correct": "C",
                "explanation": "Python supports negative indexing, where -1 refers to the last element, -2 the second-to-last, and so on. This is a deliberate feature, distinct from an out-of-bounds error, and is the idiomatic way to access elements from the end."
            }
        ],
        "coding": [
            {
                "id": "array_out_of_bounds_c1",
                "description": "This loop tries to compare each element with the next one, but on the last element it looks one past the end of the list.",
                "buggy_code": "def has_duplicate_neighbor(lst):\n    for i in range(len(lst)):\n        if lst[i] == lst[i + 1]:\n            return True\n    return False\n\nprint(has_duplicate_neighbor([1, 2, 2]))",
                "hint": "Loop only up to len(lst) - 1 since you're comparing i with i+1.",
                "solution_check": "returns True for [1, 2, 2] with no IndexError",
                "explanation": "When i is the last valid index, lst[i + 1] reaches one past the end of the list, raising an IndexError. Changing the loop to range(len(lst) - 1) stops one element early so i + 1 always stays in bounds."
            },
            {
                "id": "array_out_of_bounds_c2",
                "description": "This function tries to get the 3rd item from a list without checking the list is long enough.",
                "buggy_code": "def third_item(lst):\n    return lst[2]\n\nprint(third_item([1, 2]))",
                "hint": "Check len(lst) >= 3 before indexing, and handle the short case (e.g. return None).",
                "solution_check": "third_item([1, 2]) returns None instead of raising IndexError, third_item([1,2,3]) returns 3",
                "explanation": "A 2-element list has no index 2 (valid indices are 0 and 1), so lst[2] raises IndexError. Adding a length check before indexing lets the function handle short lists gracefully instead of crashing."
            },
            {
                "id": "array_out_of_bounds_c3",
                "description": "This function pops items from a list in a loop but doesn't account for the list shrinking, eventually indexing past the end.",
                "buggy_code": "def remove_all(lst):\n    for i in range(len(lst)):\n        lst.pop(i)\n    return lst\n\nprint(remove_all([1, 2, 3, 4]))",
                "hint": "Popping changes the list length mid-loop — iterate differently, e.g. pop(0) in a while loop, or use lst.clear().",
                "solution_check": "returns [] for [1,2,3,4] with no IndexError",
                "explanation": "range(len(lst)) is computed once at the start (4), but each pop() shrinks the list, so later iterations try to access indices that no longer exist. Using a while lst: lst.pop(0) loop (or lst.clear()) avoids relying on a fixed range while the list is changing size."
            }
        ],
        "resources": [
            {"title": "Python Docs — Sequence Types", "url": "https://docs.python.org/3/library/stdtypes.html#sequence-types-list-tuple-range", "description": "Reference on list indexing, including negative indices and bounds."},
            {"title": "W3Schools — Python Access List Items", "url": "https://www.w3schools.com/python/python_lists_access.asp", "description": "Covers positive/negative indexing and range checks."},
            {"title": "GeeksforGeeks — IndexError in Python", "url": "https://www.geeksforgeeks.org/python/indexerror-list-index-out-of-range-in-python/", "description": "Common causes and fixes for list index out of range."}
        ]
    },

    # ------------------------------------------------------------------
    # 8. missing_return
    # ------------------------------------------------------------------
    "missing_return": {
        "theory": [
            {
                "id": "missing_return_t1",
                "question": "What does a Python function return if it has no return statement at all?",
                "options": [
                    "A) 0",
                    "B) An empty string",
                    "C) None",
                    "D) It raises an error"
                ],
                "correct": "C",
                "explanation": "If a function body finishes without hitting a return statement, Python implicitly returns None. This is a frequent source of bugs when a function is expected to hand back a computed value but the return was forgotten on some code path."
            },
            {
                "id": "missing_return_t2",
                "question": "If a function has return only inside an if branch and no else, what happens when the if is False?",
                "options": [
                    "A) Python raises a SyntaxError at definition time",
                    "B) The function falls through and returns None",
                    "C) The function re-runs the if condition until True",
                    "D) The function returns the last evaluated expression regardless of branch"
                ],
                "correct": "B",
                "explanation": "If the if condition is False and there's no else or subsequent return, execution reaches the end of the function body naturally, which implicitly returns None — even if the function's other branch returns something meaningful."
            }
        ],
        "coding": [
            {
                "id": "missing_return_c1",
                "description": "This function computes a result but forgets to return it, so it always gives back None.",
                "buggy_code": "def square(n):\n    result = n * n\n\nprint(square(4))",
                "hint": "Add 'return result' at the end of the function.",
                "solution_check": "prints 16, not None",
                "explanation": "The function computed result but never returned it, so the function implicitly returned None. Adding return result sends the computed value back to the caller."
            },
            {
                "id": "missing_return_c2",
                "description": "This function only returns inside the if branch; when the condition is False, it silently returns None instead of a real value.",
                "buggy_code": "def abs_value(n):\n    if n < 0:\n        return -n",
                "hint": "Add an else (or a return after the if) covering the non-negative case.",
                "solution_check": "abs_value(-5) returns 5, abs_value(5) returns 5",
                "explanation": "There was no return for the case where n >= 0, so the function fell through and returned None. Adding 'return n' for that case (via else or after the if) ensures every path returns a proper value."
            },
            {
                "id": "missing_return_c3",
                "description": "This function loops through a list to find a match but returns inside the loop only when found — however the print/return is misplaced so it returns None on the first non-match instead of continuing to check.",
                "buggy_code": "def find_even(nums):\n    for n in nums:\n        if n % 2 == 0:\n            return n\n        return None\n\nprint(find_even([1, 3, 4]))",
                "hint": "The 'return None' should happen only after the loop finishes checking everything, not inside every iteration.",
                "solution_check": "returns 4 for [1, 3, 4]",
                "explanation": "return None was indented inside the loop, so it executed on the very first non-matching element, exiting before checking the rest of the list. Moving 'return None' to after the loop (dedented) lets the loop fully search before giving up."
            }
        ],
        "resources": [
            {"title": "Python Docs — return statement", "url": "https://docs.python.org/3/reference/simple_stmts.html#the-return-statement", "description": "Official reference on return semantics and implicit None."},
            {"title": "W3Schools — Python Functions", "url": "https://www.w3schools.com/python/python_functions.asp", "description": "Covers how functions return values, including the default None."},
            {"title": "GeeksforGeeks — Return statement in Python", "url": "https://www.geeksforgeeks.org/python/python-return-statement/", "description": "Explains what happens when return is missing or misplaced."}
        ]
    },

    # ------------------------------------------------------------------
    # 9. wrong_return_type
    # ------------------------------------------------------------------
    "wrong_return_type": {
        "theory": [
            {
                "id": "wrong_return_type_t1",
                "question": "Why might a function that's supposed to return a number sometimes cause errors downstream if it occasionally returns a string instead?",
                "options": [
                    "A) Python would auto-convert it, so there's no issue",
                    "B) Inconsistent return types can cause TypeErrors when the caller performs numeric operations on the result",
                    "C) Python functions can only ever return one fixed type, so this can't happen",
                    "D) It only matters if type hints are used"
                ],
                "correct": "B",
                "explanation": "Python doesn't enforce a single return type for a function — different code paths can return different types. If a caller assumes a consistent type (e.g. always doing arithmetic on the result) but the function sometimes returns a string, operations like + or comparisons can raise TypeErrors."
            },
            {
                "id": "wrong_return_type_t2",
                "question": "A function is supposed to return a list of matches but returns nothing found via 'return' with no value in one branch. What type mismatch issue can this cause?",
                "options": [
                    "A) None, since Python treats empty return the same as an empty list",
                    "B) The caller may crash trying to iterate/index into what is actually None instead of an empty list",
                    "C) It automatically converts to []",
                    "D) It raises a compile-time error"
                ],
                "correct": "B",
                "explanation": "'return' with no value returns None, not an empty list. If the caller expects a list back and tries to do something like len(result) or a for loop over it, calling that on None raises a TypeError, because None is not iterable/sized the way an empty list is."
            }
        ],
        "coding": [
            {
                "id": "wrong_return_type_c1",
                "description": "This function should return a number (the count) but returns it as a string.",
                "buggy_code": "def count_evens(nums):\n    count = 0\n    for n in nums:\n        if n % 2 == 0:\n            count += 1\n    return str(count)\n\nprint(count_evens([1, 2, 3, 4]) + 1)",
                "hint": "Return count directly as an int, not str(count).",
                "solution_check": "count_evens([1,2,3,4]) + 1 evaluates to 3 with no TypeError",
                "explanation": "Returning str(count) makes the function's output a string, so adding an int to it (result + 1) raises a TypeError since str and int can't be added directly. Returning count (the int itself) fixes the downstream arithmetic."
            },
            {
                "id": "wrong_return_type_c2",
                "description": "This function should return an empty list when nothing matches, but instead falls through and returns None, breaking the caller's loop.",
                "buggy_code": "def find_negatives(nums):\n    result = []\n    for n in nums:\n        if n < 0:\n            result.append(n)\n    if result:\n        return result\n\nfor x in find_negatives([1, 2, 3]):\n    print(x)",
                "hint": "Add 'return result' outside the if, so an empty list is returned instead of falling through to None.",
                "solution_check": "no TypeError when calling find_negatives([1,2,3]) (returns [] and loop just doesn't print anything)",
                "explanation": "When result is empty (falsy), 'if result: return result' is skipped, and the function falls through returning None. Iterating over None in the for loop raises a TypeError. Returning result unconditionally after the loop (not just inside the if) guarantees a list is always returned, even if empty."
            },
            {
                "id": "wrong_return_type_c3",
                "description": "This function is meant to return True/False but returns 1/0 in one branch and True/False in another, and the caller does an 'is True' check.",
                "buggy_code": "def is_adult(age):\n    if age >= 18:\n        return 1\n    else:\n        return False\n\nif is_adult(20) is True:\n    print('adult')\nelse:\n    print('not adult')",
                "hint": "Return actual booleans (True/False) consistently, not 1/0.",
                "solution_check": "prints 'adult' for is_adult(20)",
                "explanation": "1 is not the same object as True for an 'is True' identity check, even though 1 == True. Returning the literal boolean True instead of 1 keeps the return type consistent and makes strict identity checks behave as expected."
            }
        ],
        "resources": [
            {"title": "Python Docs — Data model (truth value testing)", "url": "https://docs.python.org/3/reference/datamodel.html#object.__bool__", "description": "Explains truthiness and how types like None, 0, and [] are evaluated."},
            {"title": "W3Schools — Python Booleans", "url": "https://www.w3schools.com/python/python_booleans.asp", "description": "Covers True/False vs truthy/falsy values."},
            {"title": "GeeksforGeeks — Python Return Type", "url": "https://www.geeksforgeeks.org/python/python-return-statement/", "description": "Discusses return value consistency and implicit None returns."}
        ]
    },

    # ------------------------------------------------------------------
    # 10. redundant_condition
    # ------------------------------------------------------------------
    "redundant_condition": {
        "theory": [
            {
                "id": "redundant_condition_t1",
                "question": "What's redundant about writing 'if is_valid == True:' instead of 'if is_valid:'?",
                "options": [
                    "A) Nothing — they behave completely differently",
                    "B) is_valid is already a boolean; comparing it to True is unnecessary since the value itself is truthy/falsy",
                    "C) == True always returns False for booleans",
                    "D) Python doesn't allow comparing booleans with =="
                ],
                "correct": "B",
                "explanation": "If is_valid is already True or False, 'if is_valid:' directly uses its truth value — comparing it to True with == is redundant and considered non-idiomatic (and can subtly misbehave with non-bool truthy values). The clean, Pythonic form is just 'if is_valid:'."
            },
            {
                "id": "redundant_condition_t2",
                "question": "Why is 'if not (x == 5):' considered redundant compared to 'if x != 5:'?",
                "options": [
                    "A) They are not equivalent at all",
                    "B) The longer form negates an equality check, which != expresses directly and more clearly",
                    "C) 'not' can't be used with parentheses",
                    "D) Only one of them is valid Python syntax"
                ],
                "correct": "B",
                "explanation": "not (x == 5) and x != 5 are logically identical, but the first wraps a negation around an equality check when Python already has a direct 'not equal' operator (!=). The redundant form adds unnecessary complexity without changing behavior."
            }
        ],
        "coding": [
            {
                "id": "redundant_condition_c1",
                "description": "This condition redundantly compares a boolean to True, which works but is a code smell — and here it actually causes a bug because is_ready is not a strict bool.",
                "buggy_code": "def check(is_ready):\n    if is_ready == True:\n        return 'go'\n    return 'wait'\n\nprint(check(1))",
                "hint": "Use 'if is_ready:' instead of 'if is_ready == True:'.",
                "solution_check": "check(1) returns 'go'",
                "explanation": "1 == True evaluates to True in Python, so this particular case works, but == True is fragile and unnecessary — using the value's own truthiness ('if is_ready:') is simpler, correct for any truthy value, and considered the correct style."
            },
            {
                "id": "redundant_condition_c2",
                "description": "This condition has a redundant double negative that makes the logic confusing and easy to get backwards.",
                "buggy_code": "def can_vote(age):\n    if not (age < 18):\n        return True\n    return False\n\nprint(can_vote(16))",
                "hint": "Simplify to 'if age >= 18:' — same meaning, much clearer.",
                "solution_check": "can_vote(16) returns False, can_vote(20) returns True",
                "explanation": "not (age < 18) is logically the same as age >= 18, but expressed indirectly through negation, which is harder to read and easier to get wrong. Rewriting it directly as age >= 18 keeps the same behavior with clearer intent."
            },
            {
                "id": "redundant_condition_c3",
                "description": "This condition redundantly checks the same thing twice with an 'or', where the second clause never adds anything new, hiding the fact that it's really always True.",
                "buggy_code": "def is_weekend(day):\n    if day == 'Saturday' or day == 'Saturday' or day == 'Sunday':\n        return True\n    return False\n\nprint(is_weekend('Monday'))",
                "hint": "Remove the duplicated 'day == Saturday' check — it doesn't affect logic here but is dead redundancy worth cleaning up; also double check the intended days list is complete.",
                "solution_check": "is_weekend('Monday') returns False, is_weekend('Saturday') returns True",
                "explanation": "The condition repeated 'day == Saturday' twice for no reason, which doesn't break correctness here but is redundant and can mask real logic bugs (e.g. someone might think two different days are being checked). Consolidating to 'day in (\"Saturday\", \"Sunday\")' is both cleaner and less error-prone."
            }
        ],
        "resources": [
            {"title": "Python Docs — Truth Value Testing", "url": "https://docs.python.org/3/library/stdtypes.html#truth-value-testing", "description": "Explains why comparing booleans to True/False directly is unnecessary."},
            {"title": "W3Schools — Python Comparison Operators", "url": "https://www.w3schools.com/python/gloss_python_comparison_operators.asp", "description": "Covers ==, !=, and how comparisons combine with not."},
            {"title": "GeeksforGeeks — Python Style — Redundant conditions", "url": "https://www.geeksforgeeks.org/python/python-comparing-boolean-values/", "description": "Covers idiomatic boolean checks vs redundant comparisons."}
        ]
    },

}