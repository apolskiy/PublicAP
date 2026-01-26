"""Aleksandr Polskiy practice of checking if brackets are correctly nested in a string."""
import unittest
from flask import Flask
app = Flask(__name__)
from flask import Flask

app = Flask(__name__)
@app.route('/')

def hello_world():
    return 'Hello, World!'


def verify_brackets(input: str) -> bool:
    """
    Checks if a string has balanced and correctly nested brackets.
    """
    #Using list a stack
    print(f"Executting verify_brackets for {input}\n:")
    stack = [] 
    
    #Bracket map uses keys for closing brackets and values for opening brackets
    bracket_map = {')': '(', '}': '{', ']': '['}
    for symbol in input:
        if symbol in bracket_map.values():  # If it's an opening bracket
            stack.append(symbol)  # Push onto the stack
        elif symbol in bracket_map.keys():  # If it's a closing bracket
            # Check if stack is empty (no matching open bracket) or top doesn't match
            #print (f"Symbol {symbol}: top stack value:{stack[-1]}\n")
            if not stack or stack.pop() != bracket_map[symbol]:
                return False  # Invalid sequence
        # Ignore other characters if any

    # After checking all characters, the stack must be empty for it to be valid
    return not stack

class TestBracketVerification(unittest.TestCase):
    def test_verify_brackets_three_in_arow(self):
        self.assertTrue(verify_brackets("()[]{}"))

    def test_verify_brackets_three_nested(self):
        self.assertTrue(verify_brackets("[{()}]"))

    def test_verify_brackets_incorrect_closing_order(self):
        self.assertFalse(verify_brackets("([)]"))

    def test_verify_brackets_nomatching(self):
        self.assertFalse(verify_brackets("([{}]))"))

    def test_verify_brackets_empty_string(self):
        self.assertTrue(verify_brackets(""))

if __name__ == "__main__":
    unittest.main()
    app.run(debug=True)

