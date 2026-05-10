from jinja2 import Template

class FeedbackGenerator:
    def __init__(self):
        # Hardcoded TEMPLATE_BANK (10 concepts * 3 tiers)
        self.TEMPLATE_BANK = {
            "off_by_one": {
                "hint": "Your loop boundary might be off by one. Check whether your range should end at n or n-1.",
                "explain": "An off-by-one error happens when a loop runs one iteration too many or too few. In Python, `range(n)` gives 0 to n-1. If you wrote `range(1, n+1)` when you meant `range(n)`, you'll access an index that doesn't exist.",
                "exercise": "Try this: write a loop that prints exactly the elements at indices 0 to `len(arr)-1` without using `len()` inside `range()`. What boundary condition do you need?"
            },
            "uninitialized_variable": {
                "hint": "Check if you declared or assigned a value to the variable before using it.",
                "explain": "In Python, variables must be created by assigning a value (e.g., `x = 5`) before they can be read. If you try to print or do math with a variable that hasn't been assigned yet, Python raises a NameError.",
                "exercise": "Try declaring the variable with a default value (like `0` or `None`) at the top of your function before your loop or if-statement begins."
            },
            "wrong_return_type": {
                "hint": "Your function is returning a different data type than expected.",
                "explain": "Type errors happen when a function is expected to return one type (like a boolean) but returns another (like a string). This often causes issues when the caller tries to do math or logic with the result.",
                "exercise": "Review the `return` statement in your function. Use `print(type(result))` to debug what is actually being returned before it crashes."
            },
            "array_out_of_bounds": {
                "hint": "You are trying to access an index that is larger than the size of your list.",
                "explain": "List indices start at 0. If a list has 3 items, the valid indices are 0, 1, and 2. Accessing index 3 or higher will cause an IndexError. This often happens if you try to access `arr[len(arr)]`.",
                "exercise": "Print the `len(your_list)` right before the error happens. Ensure your index access is strictly less than the length."
            },
            "infinite_loop": {
                "hint": "Your code might be stuck in a loop that never ends or recursively calling itself infinitely.",
                "explain": "A `while` loop continues as long as its condition is True. If you forget to update the loop variable (like `i += 1`), the loop runs forever. Similarly, recursion without a proper base case exceeds Python's recursion limit.",
                "exercise": "Add a `print` statement inside your loop or recursive function to see if the terminating condition is ever being reached or updated."
            },
            "indentation_logic": {
                "hint": "Check the spacing at the start of your lines. Python relies on indentation to define blocks of code.",
                "explain": "Unlike other languages that use curly braces `{}`, Python uses indentation (spaces or tabs). All code inside a function, loop, or if-statement must be indented equally. Mixing tabs and spaces will crash the program.",
                "exercise": "Select all your code in your editor and re-indent it using only spaces (usually 4 spaces per level)."
            },
            "type_mismatch": {
                "hint": "You are trying to combine or perform operations on two incompatible data types.",
                "explain": "You cannot add a string and an integer together directly (e.g., `'Age: ' + 25`). Python doesn't automatically convert the integer to a string. You must explicitly cast it.",
                "exercise": "Find the operation causing the error and wrap the non-string variable in `str()` or the string in `int()` as needed."
            },
            "logical_operator_confusion": {
                "hint": "Check your syntax for logical operators or assignments. Remember `=` is for assignment, `==` is for comparison.",
                "explain": "Syntax errors often occur when you mix up `and`/`or` syntax, or use a single `=` inside an `if` statement condition. Python expects `==` to compare two values.",
                "exercise": "Review the line raising the error. Are you assigning a value when you meant to compare? Are your parentheses balanced?"
            },
            "missing_return": {
                "hint": "Your function might be missing a return statement, causing it to return `None` by default.",
                "explain": "In Python, if a function ends without a `return` statement, it implicitly returns `None`. If you try to do math on the result or access it like a list, you will get a TypeError about 'NoneType'.",
                "exercise": "Trace your function's logic. Is there a logical path (like an `if` condition) that finishes without hitting a `return`?"
            },
            "redundant_condition": {
                "hint": "You have an `if` or `elif` condition that is repeating logic or is unnecessary.",
                "explain": "If you check `if x > 5:` and then later `elif x > 5:`, the second block is unreachable. Redundant conditions can also occur if you duplicate keyword arguments in a function call.",
                "exercise": "Carefully read through your conditional branches. Can any of them be removed or simplified without changing the program's behavior?"
            }
        }

    def generate(self, concept: str, tier: str, error_raw: str) -> dict:
        # Default to generic feedback if concept is missing or unknown
        bank = self.TEMPLATE_BANK.get(concept, {
            "hint": "Double check your code logic near the error.",
            "explain": "An unexpected error occurred. Review the raw error trace carefully.",
            "exercise": "Try commenting out lines to isolate exactly where the code crashes."
        })
        
        # We render via Jinja2 just in case we add {{ variables }} to templates later
        template_str = bank.get(tier, bank["hint"])
        feedback = Template(template_str).render(error=error_raw)
        
        exercise_str = bank.get("exercise", "")
        exercise_rendered = Template(exercise_str).render(error=error_raw)
        
        return {
            "learner_id": None,
            "concept": concept,
            "tier": tier,
            "error_shown": error_raw,
            "feedback": feedback,
            "follow_up_exercise": exercise_rendered if tier == "exercise" else ""
        }
