def calculate_area(w, h):
    area = w * h
    # Missing return

result = calculate_area(5, 5)
if result > 20: # TypeError because result is None
    print("Big")
