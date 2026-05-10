def check_age(age):
    if age > 18:
        return True
    elif age > 18: # Redundant
        return False

# Forcing an error for the parser to catch
raise ValueError("Redundant Condition")
