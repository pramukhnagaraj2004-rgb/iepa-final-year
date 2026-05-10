import json
import re
from pathlib import Path
from typing import List, Dict, Any

# Define the 8-10 MVP Concept Gap Categories
CONCEPT_CATEGORIES = [
    "off_by_one",
    "uninitialized_variable",
    "wrong_return_type",
    "array_out_of_bounds",
    "infinite_loop",
    "indentation_logic",
    "type_mismatch",
    "logical_operator_confusion",
    "missing_return",
    "redundant_condition"
]

# Rule-based weak supervisor mapping: Regex -> Concept Gap
# This dictionary maps common raw error string patterns to our concepts.
ERROR_TO_CONCEPT = {
    # Python specific mappings
    r"NameError: name '.*' is not defined": "uninitialized_variable",
    r"IndentationError: .*": "indentation_logic",
    r"TabError: .*": "indentation_logic",
    r"IndexError: list index out of range": "array_out_of_bounds",
    r"TypeError: can only concatenate .*": "type_mismatch",
    r"TypeError: unsupported operand type\(s\) .*": "type_mismatch",
    r"SyntaxError: invalid syntax": "logical_operator_confusion", # Our LOC synthetic scripts trigger this
    r"TypeError: 'NoneType' object is not subscriptable": "missing_return",
    r"TypeError: '>' not supported between instances of .* and 'NoneType'": "missing_return",
    r"TypeError: '>' not supported between instances of 'NoneType' and .*": "missing_return",
    r"ValueError: Redundant Condition": "redundant_condition",
    r"IndexError: list index out of range": "off_by_one", # Overlapping with bounds, but map to off by one for this demo if needed or we let array_out_of_bounds catch it. Let's make it catch both bounds.
    r"TypeError: Expected boolean, got string": "wrong_return_type",
    r"TypeError: '>' not supported between instances of 'str' and 'int'": "wrong_return_type",
    r"TypeError: can't multiply sequence by non-int of type 'str'": "type_mismatch",
    r"UnboundLocalError: cannot access local variable .*": "uninitialized_variable",
    r"RecursionError: infinite loop simulated": "infinite_loop",
    # C/GCC specific mappings
    r"error: ‘.*’ undeclared \(first use in this function\)": "uninitialized_variable",
    r"warning: implicit declaration of function": "uninitialized_variable", # could also be missing header, but map here for MVP
    r"warning: assignment makes pointer from integer without a cast": "type_mismatch",
    r"warning: assignment to ‘.*’ from ‘.*’ makes integer from pointer without a cast": "type_mismatch",
    r"error: expected ‘;’ before .*": "logical_operator_confusion", # general syntax catch-all placeholder
    r"Segmentation fault": "pointer_misuse", # General runtime error mapping for pointers/memory
    
    # Logic / Runtime generic mappings
    r"RecursionError: maximum recursion depth exceeded": "infinite_loop",
}

class WeakLabeler:
    """
    Applies regex-based rules to raw error logs to produce initial weak labels
    for the TF-IDF + LogisticRegression model.
    """
    
    def __init__(self):
        # Compile regex rules for performance
        self.compiled_rules = {re.compile(pattern): concept for pattern, concept in ERROR_TO_CONCEPT.items()}

    def map_error_to_concept(self, raw_error_msg: str) -> str:
        """
        Takes a raw error message from the execution sandbox and maps it to a concept.
        Returns 'unknown' if no rule matches.
        """
        # Clean the error message (remove line numbers, file paths for matching)
        # Assuming the normalizer gives us mostly the error string.
        clean_msg = raw_error_msg.strip()
        
        for regex_pattern, concept in self.compiled_rules.items():
            if regex_pattern.search(clean_msg):
                return concept
                
        return "unknown"

    def label_dataset(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Takes a list of normalized error events and applies the weak label.
        Expected input format per item: {'id': '123', 'raw_error': 'NameError: ...', 'language': 'python'}
        """
        labeled_data = []
        for item in data:
            concept = self.map_error_to_concept(item.get("raw_error", ""))
            labeled_item = item.copy()
            labeled_item["weak_label_concept"] = concept
            labeled_data.append(labeled_item)
            
        return labeled_data


if __name__ == "__main__":
    # Test block for the weak labeler
    print("--- Testing Weak Labeler ---")
    labeler = WeakLabeler()
    
    test_cases = [
        "Traceback (most recent call last):\n  File \"script.py\", line 2, in <module>\nNameError: name 'x' is not defined",
        "script.c:5:5: error: ‘y’ undeclared (first use in this function)",
        "IndexError: list index out of range",
        "IndentationError: expected an indented block after 'if' statement on line 10",
        "Some random output that isn't an error"
    ]
    
    for case in test_cases:
        label = labeler.map_error_to_concept(case)
        print(f"Raw: {case.splitlines()[-1] if 'Traceback' in case else case}")
        print(f"Mapped Concept: {label}\n")
