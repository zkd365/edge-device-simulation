import random

letters_and_numbers = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z', 0, 1, 2, 3, 4, 5, 6, 7, 8, 9]

device_id = []

def generate_device_id(length):
    for i in range(length):
        letter = random.choice(letters_and_numbers)
        letter = str(letter)
        device_id.append(letter)

id_len = int(input("How long would you like the ID to be? "))

generate_device_id(id_len)

str_id = "".join(device_id)
print("Generated Device ID:", str_id)
