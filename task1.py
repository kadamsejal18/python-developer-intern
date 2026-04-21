def reverse_string(s):
    return ''.join(reversed(s))

print(reverse_string("hello"))

#Task2
# Temperature Conversion Program

temp = float(input("Enter the temperature value: "))
unit = input("Enter the unit (C for Celsius, F for Fahrenheit): ")

if unit == "C" or unit == "c":
    fahrenheit = (temp * 9/5) + 32
    print("Temperature in Fahrenheit:", fahrenheit)

elif unit == "F" or unit == "f":
    celsius = (temp - 32) * 5/9
    print("Temperature in Celsius:", celsius)

else:
    print("Invalid unit. Please enter C or F.")
#Task3    
import re

def validate_email(email):
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    if re.match(pattern, email):
        return True
    return False
#task4
def calculator(num1, num2, operator):
    if operator == "+":
        return num1 + num2
    elif operator == "-":
        return num1 - num2
    elif operator == "*":
        return num1 * num2
    elif operator == "/":
        if num2 != 0:
            return num1 / num2
        else:
            return "Error: Division by zero"
    elif operator == "%":
        return num1 % num2
    else:
        return "Invalid operator"


# User Input
num1 = float(input("Enter first number: "))
num2 = float(input("Enter second number: "))
operator = input("Enter operator (+, -, *, /, %): ")

result = calculator(num1, num2, operator)
print("Result:", result)
#Task5
def check_palindrome(text):
    text = text.lower()          # convert to lowercase
    if text == text[::-1]:       # compare with reversed string
        return True
    else:
        return False


word = input("Enter a word: ")

if check_palindrome(word):
    print("It is a Palindrome")
else:
    print("It is not a Palindrome")
    
