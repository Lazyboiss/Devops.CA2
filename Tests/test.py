import unittest
from flask import json
from App.app import app

class TestApp(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        cls.client = app.test_client()

    # Validity Testing
    def test_valid_registration(self):
        response = self.client.post('/register', data={
            'username': 'testuser',
            'password': 'ValidPass123',
            'confirm_password': 'ValidPass123'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)

    # Range Testing
    def test_invalid_username_length(self):
        response = self.client.post('/register', data={
            'username': 'a',  # Too short
            'password': 'ValidPass123',
            'confirm_password': 'ValidPass123'
        }, follow_redirects=True)

        self.assertIn(b'Username must be at least 3 characters long.', response.data)  # Ensure exact match


    # Consistency Testing
    def test_duplicate_user_registration(self):
        self.client.post('/register', data={
            'username': 'duplicateUser',
            'password': 'ValidPass123',
            'confirm_password': 'ValidPass123'
        }, follow_redirects=True)
        response = self.client.post('/register', data={
            'username': 'duplicateUser',
            'password': 'ValidPass123',
            'confirm_password': 'ValidPass123'
        }, follow_redirects=True)
        self.assertIn(b'Username already taken', response.data)

    # Unexpected Failure Testing
    def test_unexpected_input(self):
        response = self.client.post('/register', data={
            'username': 'validuser',
            'password': '<script>alert(1)</script>',
            'confirm_password': '<script>alert(1)</script>'
        }, follow_redirects=True)

        self.assertIn(b'Invalid username: Only letters, numbers, and underscores are allowed.', response.data)



    # Expected Failure Testing
    def test_mismatched_passwords(self):
        response = self.client.post('/register', data={
            'username': 'validuser',
            'password': 'ValidPass123',
            'confirm_password': 'WrongPass123'
        }, follow_redirects=True)
        self.assertIn(b'Passwords do not match', response.data)

    # REST API Testing
    def test_get_letter_history(self):
        self.client.post('/login', data={
            'username': 'testuser',
            'password': 'ValidPass123'
        }, follow_redirects=True)

        response = self.client.get('/history/letters')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Letter Generation History', response.data)

    def test_get_sentence_history(self):
        self.client.post('/login', data={
            'username': 'testuser',
            'password': 'ValidPass123'
        }, follow_redirects=True)

        response = self.client.get('/history/sentences')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Sentence Generation History', response.data)

    def test_generate_letter_prediction(self):
        # Ensure a test user exists
        self.client.post('/register', data={
            'username': 'testuser',
            'password': 'ValidPass123',
            'confirm_password': 'ValidPass123'
        }, follow_redirects=True)

        # Log in before making the request
        self.client.post('/login', data={
            'username': 'testuser',
            'password': 'ValidPass123'
        }, follow_redirects=True)

        # Now send the generate letter request
        response = self.client.post('/generate_letter', data={'letter': 'A'}, follow_redirects=True)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Generating content for letter', response.data) 


    def test_generate_sentence_prediction(self):
        self.client.post('/register', data={
            'username': 'testuser',
            'password': 'ValidPass123',
            'confirm_password': 'ValidPass123'
        }, follow_redirects=True)

        self.client.post('/login', data={
            'username': 'testuser',
            'password': 'ValidPass123'
        }, follow_redirects=True)

        response = self.client.post('/generate_sentence', data={'text': 'HELLO'})
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Sentence image saved to Supabase successfully', response.data)


if __name__ == '__main__':
    unittest.main()
