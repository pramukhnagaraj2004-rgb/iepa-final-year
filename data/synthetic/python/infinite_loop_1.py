def count_down(n):
    while n > 0:
        print(n)
        # Missing n -= 1
        if n == 5:
            raise RecursionError("infinite loop simulated") # forcefully raise so timeout doesn't just silence it as unknown
count_down(5)
