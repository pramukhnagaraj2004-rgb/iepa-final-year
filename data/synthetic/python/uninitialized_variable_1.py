def calc_sum():
    for i in range(5):
        total += i # total uninitialized
    return total

calc_sum()
