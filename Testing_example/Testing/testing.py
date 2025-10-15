import unittest
from HelloWorld import Loud

class testing(unittest.TestCase):
    def test_default_greeting_se(self):
        loud = Loud()
        self.asserEqual(loud.message, 'Hello World!')


if __name__ == '__main__':
    unittest.main()