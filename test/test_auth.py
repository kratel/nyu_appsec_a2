import unittest
import tempfile
import bs4
import os, sys
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)

import app
from spellcheckapp.auth.models import MFA


beautifulsoup = bs4.BeautifulSoup

class TestAuth(unittest.TestCase):
    def setUp(self):
        db_fd, database_name = tempfile.mkstemp()
        print(database_name)
        test_config = { "SECRET_KEY":'test',
                        "TESTING": True,
                        "SQLALCHEMY_DATABASE_URI": 'sqlite:///' + database_name,
                        "SPELLCHECK":'./spell_check.out',
                        "WORDLIST":'wordlist.txt',
                        "SESSION_COOKIE_HTTPONLY": True,
                        "SESSION_COOKIE_SAMESITE":'Lax',
                        "REMEMBER_COOKIE_HTTPONLY":True}
        base_app = app.create_app(test_config)
        self.app = base_app.test_client()
        self.db_fd = db_fd
        self.database_name = database_name
        self.base_app = base_app

    def tearDown(self):
        os.close(self.db_fd)
        os.unlink(self.database_name)

    ## Helper Funcs
    def register(self, uname, pword, mfa="", csrf_token=""):
        if mfa:
            pdata = { "username": uname,
                      "password": pword,
                      "mfa": mfa,
                      "csrf_token": csrf_token}
        else:
            pdata = { "username": uname,
                      "password": pword,
                      "csrf_token": csrf_token}
        return self.app.post(
            '/register',
            data=pdata,
            follow_redirects=True
        )

    def login(self, uname, pword, mfa="", csrf_token=""):
        if mfa:
            pdata = { "username": uname,
                      "password": pword,
                      "mfa": mfa,
                      "csrf_token": csrf_token}
        else:
            pdata = { "username": uname,
                      "password": pword,
                      "csrf_token": csrf_token}
        return self.app.post(
            '/login',
            data=pdata,
            follow_redirects=True
        )

    def logout(self):
        return self.app.get(
            '/logout',
            follow_redirects=True
        )

    ## Tests Start
    def test_register_get(self):
        response = self.app.get('/register', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        soup = beautifulsoup(response.data, 'html.parser')
        self.assertGreater(len(soup.find_all('input', id='uname')), 0, "No input with id 'uname' found.")
        self.assertGreater(len(soup.find_all('input', id='pword')), 0, "No input with id 'pword' found.")
        self.assertGreater(len(soup.find_all('input', id='2fa')), 0, "No input with id '2fa' found.")

    def test_register_data_req_validation(self):
        # Make a GET to grab csrf token
        response = self.app.get('/register', follow_redirects=True)
        soup = beautifulsoup(response.data, 'html.parser')
        csrf_token = soup.find_all('input', id='csrf_token')[0]['value']
        # Test Data Required Validators
        response = self.register(uname='', pword='', mfa='', csrf_token='')
        self.assertEqual(response.status_code, 200)
        soup = beautifulsoup(response.data, 'html.parser')
        results = soup.find_all(id='success')
        self.assertGreater(len(results), 0, "No flash messages received")
        self.assertTrue(any(("This field is required" in s.text) and ("Username" in s.text) for s in results))
        self.assertTrue(any(("This field is required" in s.text) and ("Password" in s.text) for s in results))
        self.assertTrue(any(("The CSRF token is missing" in s.text) for s in results))

    def test_register_data_regex_validation(self):
        # Make a GET to grab csrf token
        response = self.app.get('/register', follow_redirects=True)
        soup = beautifulsoup(response.data, 'html.parser')
        csrf_token = soup.find_all('input', id='csrf_token')[0]['value']
        # Test Regex Validators
        response = self.register(uname='temp^1234', pword='temp123(<4', mfa='', csrf_token=csrf_token)
        self.assertEqual(response.status_code, 200)
        soup = beautifulsoup(response.data, 'html.parser')
        results = soup.find_all(id='success')
        self.assertTrue(any(("Auth failure" in s.text) for s in results))
        self.assertTrue(any(("Invalid char in password or not between 8 - 20 chars" in s.text) for s in results))
        self.assertTrue(any(("Invalid char in username or not between 8 - 20 chars" in s.text) for s in results))

    def test_register_csrf(self):
        response = self.app.get('/register', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        soup = beautifulsoup(response.data, 'html.parser')
        self.assertGreater(len(soup.find_all('input', id='csrf_token')), 0, "No csrf token found in input.")

    def test_register_valid_user_registration(self):
        response = self.app.get('/register', follow_redirects=True)
        soup = beautifulsoup(response.data, 'html.parser')
        csrf_token = soup.find_all('input', id='csrf_token')[0]['value']
        response = self.register(uname='temp1234', pword='temp1234', mfa='1234', csrf_token=csrf_token)
        self.assertEqual(response.status_code, 200)
        soup = beautifulsoup(response.data, 'html.parser')
        results = soup.find_all(id='success')
        self.assertGreater(len(results), 0, "No flash messages received")
        self.assertTrue(any("Registration success" in s.text for s in results))
        # Check that mfa was stored
        with self.base_app.app_context():
            mfa_stored = MFA.query.filter_by(username='temp1234').first()
            self.assertFalse(mfa_stored is None)

    def test_register_repeated_username(self):
        response = self.app.get('/register', follow_redirects=True)
        soup = beautifulsoup(response.data, 'html.parser')
        csrf_token = soup.find_all('input', id='csrf_token')[0]['value']
        response = self.register(uname='temp1234', pword='temp1234', mfa='1234', csrf_token=csrf_token)
        # Grab csrf token and try to register with the same username
        soup = beautifulsoup(response.data, 'html.parser')
        csrf_token = soup.find_all('input', id='csrf_token')[0]['value']
        response = self.register(uname='temp1234', pword='temp1234', mfa='1234', csrf_token=csrf_token)
        self.assertEqual(response.status_code, 200)
        soup = beautifulsoup(response.data, 'html.parser')
        results = soup.find_all(id='success')
        self.assertTrue(any(("Username is not available" in s.text) for s in results))
        self.assertTrue(any(("Registration failure" in s.text) for s in results))

    def test_login_get(self):
        response = self.app.get('/login', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        soup = beautifulsoup(response.data, 'html.parser')
        self.assertGreater(len(soup.find_all('input', id='uname')), 0, "No input with id 'uname' found.")
        self.assertGreater(len(soup.find_all('input', id='pword')), 0, "No input with id 'pword' found.")
        self.assertGreater(len(soup.find_all('input', id='2fa')), 0, "No input with id '2fa' found.")

    def test_login_data_req_validation(self):
        # Make a GET to grab csrf token
        response = self.app.get('/login', follow_redirects=True)
        soup = beautifulsoup(response.data, 'html.parser')
        csrf_token = soup.find_all('input', id='csrf_token')[0]['value']
        # Test Data Required Validators
        response = self.login(uname='', pword='', mfa='', csrf_token='')
        self.assertEqual(response.status_code, 200)
        soup = beautifulsoup(response.data, 'html.parser')
        results = soup.find_all(id='success')
        self.assertGreater(len(results), 0, "No flash messages received")
        self.assertTrue(any(("This field is required" in s.text) and ("Username" in s.text) for s in results))
        self.assertTrue(any(("This field is required" in s.text) and ("Password" in s.text) for s in results))
        self.assertTrue(any(("The CSRF token is missing" in s.text) for s in results))

    def test_login_regex_validation(self):
        # Make a GET to grab csrf token
        response = self.app.get('/login', follow_redirects=True)
        soup = beautifulsoup(response.data, 'html.parser')
        csrf_token = soup.find_all('input', id='csrf_token')[0]['value']
        # Test Regex Validators
        response = self.login(uname='temp^1234', pword='temp123(<4', mfa='', csrf_token=csrf_token)
        self.assertEqual(response.status_code, 200)
        soup = beautifulsoup(response.data, 'html.parser')
        results = soup.find_all(id='success')
        self.assertTrue(any(("Auth failure" in s.text) for s in results))
        self.assertTrue(any(("Invalid char in password or not between 8 - 20 chars" in s.text) for s in results))
        self.assertTrue(any(("Invalid char in username or not between 8 - 20 chars" in s.text) for s in results))

    def test_login_csrf(self):
        response = self.app.get('/login', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        soup = beautifulsoup(response.data, 'html.parser')
        self.assertGreater(len(soup.find_all('input', id='csrf_token')), 0, "No csrf token found in input.")

    def test_login_valid_user_login(self):
        # Register a user
        response = self.app.get('/register', follow_redirects=True)
        soup = beautifulsoup(response.data, 'html.parser')
        csrf_token = soup.find_all('input', id='csrf_token')[0]['value']
        response = self.register(uname='temp1234', pword='temp1234', mfa='1234', csrf_token=csrf_token)
        self.assertEqual(response.status_code, 200)
        soup = beautifulsoup(response.data, 'html.parser')
        results = soup.find_all(id='success')
        self.assertGreater(len(results), 0, "No flash messages received")
        self.assertTrue(any("Registration success" in s.text for s in results))
        # Login as a user
        csrf_token = soup.find_all('input', id='csrf_token')[0]['value']
        response = self.login(uname='temp1234', pword='temp1234', mfa='1234', csrf_token=csrf_token)
        self.assertEqual(response.status_code, 200)
        soup = beautifulsoup(response.data, 'html.parser')
        results = soup.find_all(id='result')
        self.assertGreater(len(results), 0, "No flash messages received")
        self.assertTrue(any("Login success" in s.text for s in results))

    def test_login_invalid_username_login(self):
        # Login as user that does not exist
        response = self.app.get('/login', follow_redirects=True)
        soup = beautifulsoup(response.data, 'html.parser')
        csrf_token = soup.find_all('input', id='csrf_token')[0]['value']
        response = self.login(uname='temp1234fake', pword='temp1234', mfa='1234', csrf_token=csrf_token)
        self.assertEqual(response.status_code, 200)
        soup = beautifulsoup(response.data, 'html.parser')
        results = soup.find_all(id='result')
        self.assertTrue(any("Incorrect credentials" in s.text for s in results))

    def test_login_invalid_password_login(self):
        # Register a user
        response = self.app.get('/register', follow_redirects=True)
        soup = beautifulsoup(response.data, 'html.parser')
        csrf_token = soup.find_all('input', id='csrf_token')[0]['value']
        response = self.register(uname='temp1234', pword='temp1234', mfa='1234', csrf_token=csrf_token)
        self.assertEqual(response.status_code, 200)
        soup = beautifulsoup(response.data, 'html.parser')
        results = soup.find_all(id='success')
        self.assertGreater(len(results), 0, "No flash messages received")
        self.assertTrue(any("Registration success" in s.text for s in results))
        # Login with wrong password
        csrf_token = soup.find_all('input', id='csrf_token')[0]['value']
        response = self.login(uname='temp1234', pword='oopswrongpassword', mfa='1234', csrf_token=csrf_token)
        self.assertEqual(response.status_code, 200)
        soup = beautifulsoup(response.data, 'html.parser')
        results = soup.find_all(id='result')
        self.assertTrue(any("Incorrect credentials" in s.text for s in results))

    def test_login_invalid_mfa_login(self):
        # Register a user
        response = self.app.get('/register', follow_redirects=True)
        soup = beautifulsoup(response.data, 'html.parser')
        csrf_token = soup.find_all('input', id='csrf_token')[0]['value']
        response = self.register(uname='temp1234', pword='temp1234', mfa='1234', csrf_token=csrf_token)
        self.assertEqual(response.status_code, 200)
        soup = beautifulsoup(response.data, 'html.parser')
        results = soup.find_all(id='success')
        self.assertGreater(len(results), 0, "No flash messages received")
        self.assertTrue(any("Registration success" in s.text for s in results))
        # Login without mfa
        csrf_token = soup.find_all('input', id='csrf_token')[0]['value']
        response = self.login(uname='temp1234', pword='temp1234', mfa='', csrf_token=csrf_token)
        self.assertEqual(response.status_code, 200)
        soup = beautifulsoup(response.data, 'html.parser')
        results = soup.find_all(id='result')
        self.assertTrue(any("Two-factor authentication failure" in s.text for s in results))
        # Login with wrong mfa
        csrf_token = soup.find_all('input', id='csrf_token')[0]['value']
        response = self.login(uname='temp1234', pword='temp1234', mfa='12', csrf_token=csrf_token)
        self.assertEqual(response.status_code, 200)
        soup = beautifulsoup(response.data, 'html.parser')
        results = soup.find_all(id='result')
        self.assertTrue(any("Two-factor authentication failure" in s.text for s in results))

    def test_logout(self):
        # Register a user
        response = self.app.get('/register', follow_redirects=True)
        soup = beautifulsoup(response.data, 'html.parser')
        csrf_token = soup.find_all('input', id='csrf_token')[0]['value']
        response = self.register(uname='temp1234', pword='temp1234', mfa='1234', csrf_token=csrf_token)
        self.assertEqual(response.status_code, 200)
        soup = beautifulsoup(response.data, 'html.parser')
        results = soup.find_all(id='success')
        self.assertGreater(len(results), 0, "No flash messages received")
        self.assertTrue(any("Registration success" in s.text for s in results))
        # Login as a user
        csrf_token = soup.find_all('input', id='csrf_token')[0]['value']
        response = self.login(uname='temp1234', pword='temp1234', mfa='1234', csrf_token=csrf_token)
        self.assertEqual(response.status_code, 200)
        soup = beautifulsoup(response.data, 'html.parser')
        results = soup.find_all(id='result')
        self.assertGreater(len(results), 0, "No flash messages received")
        self.assertTrue(any("Login success" in s.text for s in results))
        # Logout
        response = self.logout()
        self.assertEqual(response.status_code, 200)
        soup = beautifulsoup(response.data, 'html.parser')
        results = soup.find_all('p')
        self.assertTrue(any("Need to spell check some text?" in s.text for s in results))


if __name__ == '__main__':
    unittest.main()
