def add_numbers(a, b):
    return str(a + b) # Returns string instead of int

result = add_numbers(5, 5)
if result > 0: # TypeError
    print("Positive")
