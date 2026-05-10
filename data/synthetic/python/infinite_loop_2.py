def find_item():
    i = 0
    while True:
        if i == -1:
            break
        i += 1
        if i > 1000:
            raise RecursionError("infinite loop simulated")
find_item()
