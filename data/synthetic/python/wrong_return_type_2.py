def is_even(n):
    if n % 2 == 0:
        return "yes" # returns str instead of bool
    return "no"

if is_even(4) == True: # logic fails or type error elsewhere
    pass
else:
    raise TypeError("Expected boolean, got string") # force an error for the parser
