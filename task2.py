#task1
import tkinter as tk
import random

# Generate random number
number = random.randint(1, 100)

def check_guess():
    guess = int(entry.get())

    if guess < number:
        result_label.config(text="Too Low! Try again.")
    elif guess > number:
        result_label.config(text="Too High! Try again.")
    else:
        result_label.config(text="🎉 Correct! You guessed the number.")

# Create window
window = tk.Tk()
window.title("Number Guessing Game")
window.geometry("300x200")

title = tk.Label(window, text="Guess a number (1-100)", font=("Arial", 14))
title.pack(pady=10)

entry = tk.Entry(window)
entry.pack(pady=5)

guess_button = tk.Button(window, text="Submit Guess", command=check_guess)
guess_button.pack(pady=5)

result_label = tk.Label(window, text="")
result_label.pack(pady=10)

window.mainloop()
#Task2
import tkinter as tk
import random

# Generate random number
number = random.randint(1, 100)

def check_guess():
    guess = int(entry.get())

    if guess < number:
        result_label.config(text="Too Low! Try again.")
    elif guess > number:
        result_label.config(text="Too High! Try again.")
    else:
        result_label.config(text="🎉 Correct! You guessed the number!")

# Create window
window = tk.Tk()
window.title("Number Guessing Game")
window.geometry("300x200")

title_label = tk.Label(window, text="Guess a number (1-100)", font=("Arial", 14))
title_label.pack(pady=10)

entry = tk.Entry(window)
entry.pack(pady=5)

guess_button = tk.Button(window, text="Submit Guess", command=check_guess)
guess_button.pack(pady=5)

result_label = tk.Label(window, text="")
result_label.pack(pady=10)

window.mainloop()
#Task3
import tkinter as tk
import re

def check_strength():
    password = entry.get()
    score = 0

    if len(password) >= 8:
        score += 1
    if re.search("[A-Z]", password):
        score += 1
    if re.search("[a-z]", password):
        score += 1
    if re.search("[0-9]", password):
        score += 1
    if re.search("[@#$%^&*!]", password):
        score += 1

    if score == 5:
        result_label.config(text="Strong Password 💪", fg="green")
    elif score >= 3:
        result_label.config(text="Medium Password ⚠️", fg="orange")
    else:
        result_label.config(text="Weak Password ❌", fg="red")


window = tk.Tk()
window.title("Password Strength Checker")
window.geometry("350x200")

title = tk.Label(window, text="Enter Password", font=("Arial", 14))
title.pack(pady=10)

entry = tk.Entry(window, show="*", width=25)
entry.pack(pady=5)

button = tk.Button(window, text="Check Strength", command=check_strength)
button.pack(pady=10)

result_label = tk.Label(window, text="", font=("Arial", 12))
result_label.pack(pady=10)

window.mainloop()
#Task4
def fibonacci(n):
    a = 0
    b = 1

    print("Fibonacci Sequence:")

    for i in range(n):
        print(a, end=" ")
        a, b = b, a + b


terms = int(input("Enter number of terms: "))
fibonacci(terms)
#Task5
from collections import Counter
import string

filename = input("Enter file name: ")

with open(filename, "r") as file:
    text = file.read().lower()

# Remove punctuation
for p in string.punctuation:
    text = text.replace(p, "")

words = text.split()

# Count words
word_count = Counter(words)

# Display in alphabetical order
for word in sorted(word_count):
    print(word, ":", word_count[word])