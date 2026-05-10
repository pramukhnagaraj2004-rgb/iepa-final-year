import os
import json
from pathlib import Path
from collections import Counter

# 12-15 variations for each of the 10 concepts
AUGMENTATION_DATA = {
    "off_by_one": [
        "IndexError: list index out of range",
        "IndexError: tuple index out of range",
        "IndexError: string index out of range",
        "IndexError: range object index out of range",
        "IndexError: pop index out of range",
        "IndexError: pop from empty list",
        "IndexError: list assignment index out of range",
        "IndexError: bytearray index out of range",
        "ValueError: substring not found", # Sometimes off-by-one in slicing leads to this
        "IndexError: string index out of bounds",
        "IndexError: array index out of range",
        "IndexError: deque index out of range",
        "IndexError: list index out of bounds"
    ],
    "uninitialized_variable": [
        "NameError: name 'x' is not defined",
        "NameError: name 'total' is not defined",
        "NameError: name 'count' is not defined",
        "NameError: name 'result' is not defined",
        "NameError: name 'i' is not defined",
        "NameError: name 'data' is not defined",
        "NameError: name 'value' is not defined",
        "NameError: name 'temp' is not defined",
        "UnboundLocalError: local variable 'x' referenced before assignment",
        "UnboundLocalError: local variable 'total' referenced before assignment",
        "UnboundLocalError: local variable 'count' referenced before assignment",
        "UnboundLocalError: local variable 'result' referenced before assignment",
        "UnboundLocalError: cannot access local variable 'val' where it is not associated with a value"
    ],
    "wrong_return_type": [
        "TypeError: expected str, bytes or os.PathLike object, not int",
        "TypeError: expected str, bytes or os.PathLike object, not list",
        "TypeError: list indices must be integers or slices, not str",
        "TypeError: list indices must be integers or slices, not float",
        "TypeError: string indices must be integers",
        "TypeError: tuple indices must be integers or slices, not str",
        "TypeError: integer argument expected, got float",
        "TypeError: a bytes-like object is required, not 'str'",
        "TypeError: 'int' object is not iterable",
        "TypeError: 'float' object is not iterable",
        "TypeError: expected string or bytes-like object",
        "TypeError: can only join an iterable",
        "TypeError: Expected boolean, got string",
        "TypeError: '>' not supported between instances of 'str' and 'int'"
    ],
    "array_out_of_bounds": [
        "IndexError: index 5 is out of bounds for axis 0 with size 3",
        "IndexError: index 10 is out of bounds for axis 1 with size 5",
        "IndexError: invalid index to scalar variable.",
        "IndexError: too many indices for array",
        "IndexError: tuple index out of range",
        "IndexError: list index out of range",
        "IndexError: index out of bounds",
        "IndexError: arrays used as indices must be of integer (or boolean) type",
        "IndexError: shape mismatch: indexing arrays could not be broadcast together",
        "IndexError: only integers, slices (`:`), ellipsis (`...`), numpy.newaxis (`None`) and integer or boolean arrays are valid indices",
        "IndexError: list assignment index out of range",
        "IndexError: sequence index out of range"
    ],
    "infinite_loop": [
        "RecursionError: maximum recursion depth exceeded",
        "RecursionError: maximum recursion depth exceeded in comparison",
        "RecursionError: maximum recursion depth exceeded while calling a Python object",
        "RecursionError: maximum recursion depth exceeded while getting the str of an object",
        "MemoryError",
        "MemoryError: memory allocation failed",
        "TimeoutError: execution exceeded time limit",
        "TimeoutError: process took too long to complete",
        "KeyboardInterrupt", # often caused by manual termination of infinite loop
        "RecursionError: infinite loop simulated",
        "RuntimeError: maximum recursion depth exceeded",
        "TimeoutError: Script execution timed out"
    ],
    "indentation_logic": [
        "IndentationError: unexpected indent",
        "IndentationError: expected an indented block",
        "IndentationError: unindent does not match any outer indentation level",
        "IndentationError: expected an indented block after 'if' statement on line 10",
        "IndentationError: expected an indented block after 'for' statement",
        "IndentationError: expected an indented block after function definition",
        "TabError: inconsistent use of tabs and spaces in indentation",
        "IndentationError: expected an indented block after 'while' statement",
        "IndentationError: expected an indented block after 'def' statement",
        "IndentationError: expected an indented block after 'try' statement",
        "IndentationError: expected an indented block after 'except' statement",
        "IndentationError: unexpected unindent"
    ],
    "type_mismatch": [
        "TypeError: can only concatenate str (not \"int\") to str",
        "TypeError: can only concatenate list (not \"str\") to list",
        "TypeError: unsupported operand type(s) for +: 'int' and 'str'",
        "TypeError: unsupported operand type(s) for -: 'str' and 'int'",
        "TypeError: unsupported operand type(s) for *: 'list' and 'float'",
        "TypeError: unsupported operand type(s) for /: 'str' and 'int'",
        "TypeError: unsupported operand type(s) for ** or pow(): 'str' and 'int'",
        "TypeError: 'list' object cannot be interpreted as an integer",
        "TypeError: 'str' object cannot be interpreted as an integer",
        "TypeError: must be str, not int",
        "TypeError: can't multiply sequence by non-int of type 'float'",
        "TypeError: can't multiply sequence by non-int of type 'str'",
        "TypeError: bad operand type for unary -: 'str'",
        "TypeError: bad operand type for unary ~: 'float'"
    ],
    "logical_operator_confusion": [
        "SyntaxError: invalid syntax",
        "SyntaxError: can't assign to literal",
        "SyntaxError: can't assign to operator",
        "SyntaxError: can't assign to function call",
        "TypeError: 'bool' object is not iterable",
        "SyntaxError: expected ':'",
        "SyntaxError: invalid character in identifier",
        "SyntaxError: EOL while scanning string literal",
        "SyntaxError: EOF while scanning triple-quoted string literal",
        "SyntaxError: unmatched ')'",
        "SyntaxError: unmatched ']'",
        "SyntaxError: unmatched '}'",
        "SyntaxError: unexpected EOF while parsing",
        "ValueError: truth value of an array with more than one element is ambiguous"
    ],
    "missing_return": [
        "TypeError: 'NoneType' object is not subscriptable",
        "TypeError: 'NoneType' object is not iterable",
        "TypeError: unsupported operand type(s) for +: 'NoneType' and 'int'",
        "TypeError: unsupported operand type(s) for +: 'int' and 'NoneType'",
        "AttributeError: 'NoneType' object has no attribute 'append'",
        "AttributeError: 'NoneType' object has no attribute 'split'",
        "AttributeError: 'NoneType' object has no attribute 'join'",
        "TypeError: 'NoneType' object is not callable",
        "TypeError: object of type 'NoneType' has no len()",
        "TypeError: '>' not supported between instances of 'NoneType' and 'int'",
        "TypeError: '<' not supported between instances of 'int' and 'NoneType'",
        "TypeError: 'NoneType' object cannot be interpreted as an integer",
        "TypeError: int() argument must be a string, a bytes-like object or a real number, not 'NoneType'"
    ],
    "redundant_condition": [
        "SyntaxError: duplicate argument 'x' in function definition",
        "SyntaxError: keyword argument repeated",
        "SyntaxWarning: 'if' condition is always True",
        "SyntaxWarning: 'if' condition is always False",
        "AssertionError",
        "Exception: Unreachable code executed",
        "ValueError: Redundant Condition",
        "SyntaxError: positional argument follows keyword argument",
        "SyntaxError: non-default argument follows default argument",
        "SyntaxError: name 'var' is parameter and global",
        "SyntaxWarning: assertion is always true, perhaps remove parentheses?",
        "Warning: redundant conditional expression",
        "ValueError: condition already checked"
    ]
}

def augment():
    project_root = Path(os.path.abspath(os.path.dirname(__file__))).parent
    data_path = project_root / "data" / "labeled_dataset.json"
    
    if not data_path.exists():
        print(f"[-] Could not find labeled_dataset.json at {data_path}")
        return
        
    with open(data_path, "r", encoding="utf-8") as f:
        dataset = json.load(f)
        
    before_count = len(dataset)
    existing_errors = {item.get("error_raw", "") for item in dataset}
    
    # Generate new entries
    for concept, errors in AUGMENTATION_DATA.items():
        for i, error_str in enumerate(errors):
            if error_str in existing_errors:
                continue
                
            # Attempt to extract a naive "type" from the error string for error_normalized
            err_type = error_str.split(":")[0] if ":" in error_str else "Error"
            
            entry = {
                "id": f"aug_{concept}_{i}",
                "source": "augmented",
                "language": "python",
                "code": "",
                "error_raw": error_str,
                "error_normalized": [{"error_type": err_type, "message": error_str, "line": None}],
                "concept_label": concept,
                "confidence": "high"
            }
            dataset.append(entry)
            existing_errors.add(error_str)
            
    after_count = len(dataset)
    
    with open(data_path, "w", encoding="utf-8") as f:
        json.dump(dataset, f, indent=2)
        
    print(f"[*] Augmentation Complete")
    print(f"    - Entries before: {before_count}")
    print(f"    - Entries after:  {after_count}")
    
    # Print distribution
    counts = Counter(item["concept_label"] for item in dataset)
    print("\n[*] Count per concept gap:")
    for concept, count in counts.most_common():
        print(f"    - {concept}: {count}")

if __name__ == "__main__":
    augment()
