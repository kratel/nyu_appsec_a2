"""
Tests the auth module of the spellcheckapp.

Makes use of flask's test client to perform integration tests.
"""
import os
import sys
import tempfile
import unittest

import app

import bs4

import onetimepass

from spellcheckapp.auth.models import MFA, Users

parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)


beautifulsoup = bs4.BeautifulSoup


class TestAuth(unittest.TestCase):
    """Groups Auth tests to use the same test client."""

    def setUp(self):
        """
        Runs before each test.

        Creates test flask client, using a test config.
        Creates temporary sqlite file.
        """
        db_fd, database_name = tempfile.mkstemp()
        test_config = {"SECRET_KEY": 'test',
                       "TESTING": True,
                       "SQLALCHEMY_DATABASE_URI": 'sqlite:///' + database_name,
                       "SQLALCHEMY_TRACK_MODIFICATIONS": False,
                       "SPELLCHECK": './spell_check.out',
                       "WORDLIST": 'wordlist.txt',
                       "SESSION_COOKIE_HTTPONLY": True,
                       "SESSION_COOKIE_SAMESITE": 'Lax',
                       "REMEMBER_COOKIE_HTTPONLY": True,
                       "ADMIN_USERNAME": 'replaceme',
                       "ADMIN_PASSWORD": 'replaceme', }
        base_app = app.create_app(test_config)
        self.app = base_app.test_client()
        self.db_fd = db_fd
        self.database_name = database_name
        self.base_app = base_app

    def tearDown(self):
        """Tears down the test client and removes the sqlite file."""
        os.close(self.db_fd)
        os.unlink(self.database_name)

    # Helper Funcs
    def register(self, uname, pword, csrf_token=""):
        """Helper function to issue a register request."""
        pdata = {"username": uname,
                 "password": pword,
                 "csrf_token": csrf_token}
        return self.app.post(
            '/register',
            data=pdata,
            follow_redirects=True
        )

    def update_account(self, pword=None, mfa_enabled=None, csrf_token=""):
        """Helper function to issue an mfa confirmation request."""
        pdata = {}
        if pword:
            pdata["password"] = pword
        if mfa_enabled:
            pdata["mfa_enabled"] = mfa_enabled
        pdata["csrf_token"] = csrf_token
        return self.app.post(
            '/account',
            data=pdata,
            follow_redirects=True
        )

    def mfa_confirm(self, mfa_confirm=False, csrf_token=""):
        """Helper function to issue an mfa confirmation request."""
        pdata = {"mfa_confirm": mfa_confirm,
                 "csrf_token": csrf_token}
        return self.app.post(
            '/multifactor',
            data=pdata,
            follow_redirects=True
        )

    def login(self, uname, pword, mfa="", csrf_token=""):
        """Helper function to issue a login request."""
        if mfa:
            pdata = {"username": uname,
                     "password": pword,
                     "mfa": mfa,
                     "csrf_token": csrf_token}
        else:
            pdata = {"username": uname,
                     "password": pword,
                     "csrf_token": csrf_token}
        return self.app.post(
            '/login',
            data=pdata,
            follow_redirects=True
        )

    def logout(self):
        """Helper function to issue a logout request."""
        return self.app.get(
            '/logout',
            follow_redirects=True
        )

    def query_userid_history(self, userid=None, csrf_token=""):
        """Helper function to issue a request to view login history."""
        if userid:
            pdata = {"userid": userid,
                     "csrf_token": csrf_token}
        else:
            pdata = {"csrf_token": csrf_token}
        return self.app.post(
            '/login_history',
            data=pdata,
            follow_redirects=True
        )

    # Tests Start
    def test_register_get(self):
        """Tests that register page is retrieved successfully."""
        response = self.app.get('/register', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        soup = beautifulsoup(response.data, 'html.parser')
        self.assertGreater(len(soup.find_all('input', id='uname')), 0, "No input with id 'uname' found.")
        self.assertGreater(len(soup.find_all('input', id='pword')), 0, "No input with id 'pword' found.")

    def test_register_data_req_validation(self):
        """Tests that register page data required validation is being enforced."""
        # Make a GET to grab csrf token
        response = self.app.get('/register', follow_redirects=True)
        soup = beautifulsoup(response.data, 'html.parser')
        # Test Data Required Validators
        response = self.register(uname='', pword='', csrf_token='')
        self.assertEqual(response.status_code, 200)
        soup = beautifulsoup(response.data, 'html.parser')
        results = soup.find_all(id='success')
        self.assertGreater(len(results), 0, "No flash messages received")
        self.assertTrue(any(("This field is required" in s.text) and ("Username" in s.text) for s in results))
        self.assertTrue(any(("This field is required" in s.text) and ("Password" in s.text) for s in results))
        self.assertTrue(any(("The CSRF token is missing" in s.text) for s in results))

    def test_register_data_regex_validation(self):
        """Tests that register page regex validation is being enforced."""
        # Make a GET to grab csrf token
        response = self.app.get('/register', follow_redirects=True)
        soup = beautifulsoup(response.data, 'html.parser')
        csrf_token = soup.find_all('input', id='csrf_token')[0]['value']
        # Test Regex Validators
        response = self.register(uname='temp^1234', pword='temp123(<4', csrf_token=csrf_token)
        self.assertEqual(response.status_code, 200)
        soup = beautifulsoup(response.data, 'html.parser')
        results = soup.find_all(id='success')
        self.assertTrue(any(("Auth failure" in s.text) for s in results))
        self.assertTrue(any(("Invalid char in password or not between" in s.text) for s in results))
        self.assertTrue(any(("Invalid char in username or not between" in s.text) for s in results))

    def test_register_csrf(self):
        """Tests that csrf token is required for register form submission."""
        response = self.app.get('/register', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        soup = beautifulsoup(response.data, 'html.parser')
        self.assertGreater(len(soup.find_all('input', id='csrf_token')), 0, "No csrf token found in input.")

    def test_register_valid_user_registration(self):
        """Tests that a registration request with valid answers is successful."""
        response = self.app.get('/register', follow_redirects=True)
        soup = beautifulsoup(response.data, 'html.parser')
        csrf_token = soup.find_all('input', id='csrf_token')[0]['value']
        response = self.register(uname='temp1234', pword='temp1234', csrf_token=csrf_token)
        self.assertEqual(response.status_code, 200)
        soup = beautifulsoup(response.data, 'html.parser')
        results = soup.find_all(id='success')
        self.assertGreater(len(results), 0, "No flash messages received")
        self.assertTrue(any("Registration success" in s.text for s in results))

    def test_register_repeated_username(self):
        """Tests that the same username can not be registered twice."""
        response = self.app.get('/register', follow_redirects=True)
        soup = beautifulsoup(response.data, 'html.parser')
        csrf_token = soup.find_all('input', id='csrf_token')[0]['value']
        response = self.register(uname='temp1234', pword='temp1234', csrf_token=csrf_token)
        # Grab csrf token and try to register with the same username
        soup = beautifulsoup(response.data, 'html.parser')
        csrf_token = soup.find_all('input', id='csrf_token')[0]['value']
        response = self.register(uname='temp1234', pword='temp1234', csrf_token=csrf_token)
        self.assertEqual(response.status_code, 200)
        soup = beautifulsoup(response.data, 'html.parser')
        results = soup.find_all(id='success')
        self.assertTrue(any(("Username is not available" in s.text) for s in results))
        self.assertTrue(any(("Registration failure" in s.text) for s in results))

    def test_login_get(self):
        """Tests that login page is retrieved successfully."""
        response = self.app.get('/login', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        soup = beautifulsoup(response.data, 'html.parser')
        self.assertGreater(len(soup.find_all('input', id='uname')), 0, "No input with id 'uname' found.")
        self.assertGreater(len(soup.find_all('input', id='pword')), 0, "No input with id 'pword' found.")
        self.assertGreater(len(soup.find_all('input', id='2fa')), 0, "No input with id '2fa' found.")

    def test_login_data_req_validation(self):
        """Tests that login page data required validation is being enforced."""
        # Make a GET to grab csrf token
        response = self.app.get('/login', follow_redirects=True)
        soup = beautifulsoup(response.data, 'html.parser')
        # Test Data Required Validators
        response = self.login(uname='', pword='', mfa='', csrf_token='')
        self.assertEqual(response.status_code, 200)
        soup = beautifulsoup(response.data, 'html.parser')
        results = soup.find_all(id='result')
        self.assertGreater(len(results), 0, "No flash messages received")
        self.assertTrue(any(("This field is required" in s.text) and ("Username" in s.text) for s in results))
        self.assertTrue(any(("This field is required" in s.text) and ("Password" in s.text) for s in results))
        self.assertTrue(any(("The CSRF token is missing" in s.text) for s in results))

    def test_login_regex_validation(self):
        """Tests that login page regex validation is being enforced."""
        # Make a GET to grab csrf token
        response = self.app.get('/login', follow_redirects=True)
        soup = beautifulsoup(response.data, 'html.parser')
        csrf_token = soup.find_all('input', id='csrf_token')[0]['value']
        # Test Regex Validators
        response = self.login(uname='temp^1234', pword='temp123(<4', mfa='', csrf_token=csrf_token)
        self.assertEqual(response.status_code, 200)
        soup = beautifulsoup(response.data, 'html.parser')
        results = soup.find_all(id='result')
        self.assertTrue(any(("Auth failure" in s.text) for s in results))
        self.assertTrue(any(("Invalid char in password or not between" in s.text) for s in results))
        self.assertTrue(any(("Invalid char in username or not between" in s.text) for s in results))

    def test_login_csrf(self):
        """Tests that csrf token is required for login form submission."""
        response = self.app.get('/login', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        soup = beautifulsoup(response.data, 'html.parser')
        self.assertGreater(len(soup.find_all('input', id='csrf_token')), 0, "No csrf token found in input.")

    def test_login_valid_user_login(self):
        """Tests that a login request with valid answers is successful."""
        # Register a user
        response = self.app.get('/register', follow_redirects=True)
        soup = beautifulsoup(response.data, 'html.parser')
        csrf_token = soup.find_all('input', id='csrf_token')[0]['value']
        response = self.register(uname='temp1234', pword='temp1234', csrf_token=csrf_token)
        self.assertEqual(response.status_code, 200)
        soup = beautifulsoup(response.data, 'html.parser')
        results = soup.find_all(id='success')
        self.assertGreater(len(results), 0, "No flash messages received")
        self.assertTrue(any("Registration success" in s.text for s in results))
        # Login as a user
        csrf_token = soup.find_all('input', id='csrf_token')[0]['value']
        response = self.login(uname='temp1234', pword='temp1234', csrf_token=csrf_token)
        self.assertEqual(response.status_code, 200)
        soup = beautifulsoup(response.data, 'html.parser')
        results = soup.find_all(id='result')
        self.assertGreater(len(results), 0, "No flash messages received")
        self.assertTrue(any("Login success" in s.text for s in results))

    def test_login_invalid_username_login(self):
        """Tests that a login request with an invalid username fails."""
        # Login as user that does not exist
        response = self.app.get('/login', follow_redirects=True)
        soup = beautifulsoup(response.data, 'html.parser')
        csrf_token = soup.find_all('input', id='csrf_token')[0]['value']
        response = self.login(uname='temp1234fake', pword='temp1234', csrf_token=csrf_token)
        self.assertEqual(response.status_code, 200)
        soup = beautifulsoup(response.data, 'html.parser')
        results = soup.find_all(id='result')
        self.assertTrue(any("Incorrect credentials" in s.text for s in results))

    def test_login_invalid_password_login(self):
        """Tests that a login request with an invalid password fails."""
        # Register a user
        response = self.app.get('/register', follow_redirects=True)
        soup = beautifulsoup(response.data, 'html.parser')
        csrf_token = soup.find_all('input', id='csrf_token')[0]['value']
        response = self.register(uname='temp1234', pword='temp1234', csrf_token=csrf_token)
        self.assertEqual(response.status_code, 200)
        soup = beautifulsoup(response.data, 'html.parser')
        results = soup.find_all(id='success')
        self.assertGreater(len(results), 0, "No flash messages received")
        self.assertTrue(any("Registration success" in s.text for s in results))
        # Login with wrong password
        csrf_token = soup.find_all('input', id='csrf_token')[0]['value']
        response = self.login(uname='temp1234', pword='oopswrongpassword', csrf_token=csrf_token)
        self.assertEqual(response.status_code, 200)
        soup = beautifulsoup(response.data, 'html.parser')
        results = soup.find_all(id='result')
        self.assertTrue(any("Incorrect credentials" in s.text for s in results))

    def test_account_valid_mfa_setup(self):
        """Tests that mfa setup is working correctly."""
        # Register a user
        response = self.app.get('/register', follow_redirects=True)
        soup = beautifulsoup(response.data, 'html.parser')
        csrf_token = soup.find_all('input', id='csrf_token')[0]['value']
        response = self.register(uname='temp1234', pword='temp1234', csrf_token=csrf_token)
        self.assertEqual(response.status_code, 200)
        soup = beautifulsoup(response.data, 'html.parser')
        results = soup.find_all(id='success')
        self.assertGreater(len(results), 0, "No flash messages received")
        self.assertTrue(any("Registration success" in s.text for s in results))
        # Login without mfa
        csrf_token = soup.find_all('input', id='csrf_token')[0]['value']
        response = self.login(uname='temp1234', pword='temp1234', mfa='', csrf_token=csrf_token)
        self.assertEqual(response.status_code, 200)
        # Go to account page
        response = self.app.get('/account', follow_redirects=True)
        soup = beautifulsoup(response.data, 'html.parser')
        csrf_token = soup.find_all('input', id='csrf_token')[0]['value']
        # Start MFA setup
        response = self.update_account(mfa_enabled=True, csrf_token=csrf_token)
        soup = beautifulsoup(response.data, 'html.parser')
        csrf_token = soup.find_all('input', id='csrf_token')[0]['value']
        self.assertEqual(response.status_code, 200)
        # Confirm MFA setup
        response = self.mfa_confirm(mfa_confirm=True, csrf_token=csrf_token)
        soup = beautifulsoup(response.data, 'html.parser')
        # Check that mfa was stored and mfa was enabled for user.
        with self.base_app.app_context():
            mfa_stored = MFA.query.filter_by(username='temp1234').first()
            self.assertFalse(mfa_stored is None)
            user_stored = Users.query.filter_by(username='temp1234').first()
            self.assertTrue(user_stored.mfa_registered)

    def test_account_disable_mfa(self):
        """Tests that mfa can be disabled successfully."""
        # Register a user
        response = self.app.get('/register', follow_redirects=True)
        soup = beautifulsoup(response.data, 'html.parser')
        csrf_token = soup.find_all('input', id='csrf_token')[0]['value']
        response = self.register(uname='temp1234', pword='temp1234', csrf_token=csrf_token)
        self.assertEqual(response.status_code, 200)
        soup = beautifulsoup(response.data, 'html.parser')
        results = soup.find_all(id='success')
        self.assertGreater(len(results), 0, "No flash messages received")
        self.assertTrue(any("Registration success" in s.text for s in results))
        # Login without mfa
        csrf_token = soup.find_all('input', id='csrf_token')[0]['value']
        response = self.login(uname='temp1234', pword='temp1234', mfa='', csrf_token=csrf_token)
        self.assertEqual(response.status_code, 200)
        # Go to account page
        response = self.app.get('/account', follow_redirects=True)
        soup = beautifulsoup(response.data, 'html.parser')
        csrf_token = soup.find_all('input', id='csrf_token')[0]['value']
        # Start MFA setup
        response = self.update_account(mfa_enabled=True, csrf_token=csrf_token)
        soup = beautifulsoup(response.data, 'html.parser')
        csrf_token = soup.find_all('input', id='csrf_token')[0]['value']
        self.assertEqual(response.status_code, 200)
        # Confirm MFA setup
        response = self.mfa_confirm(mfa_confirm=True, csrf_token=csrf_token)
        soup = beautifulsoup(response.data, 'html.parser')
        # Check that mfa was stored
        with self.base_app.app_context():
            mfa_stored = MFA.query.filter_by(username='temp1234').first()
            self.assertFalse(mfa_stored is None)
            user_stored = Users.query.filter_by(username='temp1234').first()
            self.assertTrue(user_stored.mfa_registered)
        # Now go back to account page
        response = self.app.get('/account', follow_redirects=True)
        soup = beautifulsoup(response.data, 'html.parser')
        csrf_token = soup.find_all('input', id='csrf_token')[0]['value']
        # Disable MFA
        response = self.update_account(mfa_enabled=False, csrf_token=csrf_token)
        soup = beautifulsoup(response.data, 'html.parser')
        csrf_token = soup.find_all('input', id='csrf_token')[0]['value']
        self.assertEqual(response.status_code, 200)
        # Verify MFA is disabled
        with self.base_app.app_context():
            mfa_stored = MFA.query.filter_by(username='temp1234').first()
            self.assertTrue(mfa_stored is None)
            user_stored = Users.query.filter_by(username='temp1234').first()
            self.assertFalse(user_stored.mfa_registered)
        # Now logout
        response = self.logout()
        self.assertEqual(response.status_code, 200)
        # And try to login without mfa
        response = self.app.get('/login', follow_redirects=True)
        soup = beautifulsoup(response.data, 'html.parser')
        csrf_token = soup.find_all('input', id='csrf_token')[0]['value']
        response = self.login(uname='temp1234', pword='temp1234', csrf_token=csrf_token)
        self.assertEqual(response.status_code, 200)
        soup = beautifulsoup(response.data, 'html.parser')
        results = soup.find_all(id='result')
        self.assertGreater(len(results), 0, "No flash messages received")
        self.assertTrue(any("Login success" in s.text for s in results))

    def test_account_update_password(self):
        """Tests that password is updated successfully."""
        # Register a user
        response = self.app.get('/register', follow_redirects=True)
        soup = beautifulsoup(response.data, 'html.parser')
        csrf_token = soup.find_all('input', id='csrf_token')[0]['value']
        response = self.register(uname='temp1234', pword='temp1234', csrf_token=csrf_token)
        self.assertEqual(response.status_code, 200)
        soup = beautifulsoup(response.data, 'html.parser')
        results = soup.find_all(id='success')
        self.assertGreater(len(results), 0, "No flash messages received")
        self.assertTrue(any("Registration success" in s.text for s in results))
        # Login without mfa
        csrf_token = soup.find_all('input', id='csrf_token')[0]['value']
        response = self.login(uname='temp1234', pword='temp1234', mfa='', csrf_token=csrf_token)
        self.assertEqual(response.status_code, 200)
        # Go to account page
        response = self.app.get('/account', follow_redirects=True)
        soup = beautifulsoup(response.data, 'html.parser')
        csrf_token = soup.find_all('input', id='csrf_token')[0]['value']
        # Update Password
        response = self.update_account(pword='temp2345', csrf_token=csrf_token)
        soup = beautifulsoup(response.data, 'html.parser')
        csrf_token = soup.find_all('input', id='csrf_token')[0]['value']
        self.assertEqual(response.status_code, 200)
        results = soup.find_all(id='success')
        self.assertTrue(any("Password has been updated." in s.text for s in results))
        # Now logout
        response = self.logout()
        self.assertEqual(response.status_code, 200)
        # And try to login with new password
        response = self.app.get('/login', follow_redirects=True)
        soup = beautifulsoup(response.data, 'html.parser')
        csrf_token = soup.find_all('input', id='csrf_token')[0]['value']
        response = self.login(uname='temp1234', pword='temp2345', csrf_token=csrf_token)
        self.assertEqual(response.status_code, 200)
        soup = beautifulsoup(response.data, 'html.parser')
        results = soup.find_all(id='result')
        self.assertGreater(len(results), 0, "No flash messages received")
        self.assertTrue(any("Login success" in s.text for s in results))

    def test_login_valid_mfa_login(self):
        """Tests that login with mfa works correctly."""
        # Register a user
        response = self.app.get('/register', follow_redirects=True)
        soup = beautifulsoup(response.data, 'html.parser')
        csrf_token = soup.find_all('input', id='csrf_token')[0]['value']
        response = self.register(uname='temp1234', pword='temp1234', csrf_token=csrf_token)
        self.assertEqual(response.status_code, 200)
        soup = beautifulsoup(response.data, 'html.parser')
        results = soup.find_all(id='success')
        self.assertGreater(len(results), 0, "No flash messages received")
        self.assertTrue(any("Registration success" in s.text for s in results))
        # Login without mfa
        csrf_token = soup.find_all('input', id='csrf_token')[0]['value']
        response = self.login(uname='temp1234', pword='temp1234', mfa='', csrf_token=csrf_token)
        self.assertEqual(response.status_code, 200)
        # Go to account page
        response = self.app.get('/account', follow_redirects=True)
        soup = beautifulsoup(response.data, 'html.parser')
        csrf_token = soup.find_all('input', id='csrf_token')[0]['value']
        # Start MFA setup
        response = self.update_account(mfa_enabled=True, csrf_token=csrf_token)
        soup = beautifulsoup(response.data, 'html.parser')
        csrf_token = soup.find_all('input', id='csrf_token')[0]['value']
        self.assertEqual(response.status_code, 200)
        # Confirm MFA setup
        response = self.mfa_confirm(mfa_confirm=True, csrf_token=csrf_token)
        soup = beautifulsoup(response.data, 'html.parser')
        # Check that mfa was stored
        with self.base_app.app_context():
            mfa_stored = MFA.query.filter_by(username='temp1234').first()
            self.assertFalse(mfa_stored is None)
            user_stored = Users.query.filter_by(username='temp1234').first()
            self.assertTrue(user_stored.mfa_registered)
        # Now logout
        response = self.logout()
        self.assertEqual(response.status_code, 200)
        # And try to login with mfa
        response = self.app.get('/login', follow_redirects=True)
        soup = beautifulsoup(response.data, 'html.parser')
        csrf_token = soup.find_all('input', id='csrf_token')[0]['value']
        with self.base_app.app_context():
            mfa_stored = MFA.query.filter_by(username='temp1234').first()
            mfa_token = onetimepass.get_totp(mfa_stored.mfa_secret)
            response = self.login(uname='temp1234', pword='temp1234', mfa=mfa_token, csrf_token=csrf_token)
        self.assertEqual(response.status_code, 200)
        soup = beautifulsoup(response.data, 'html.parser')
        results = soup.find_all(id='result')
        self.assertGreater(len(results), 0, "No flash messages received")
        self.assertTrue(any("Login success" in s.text for s in results))

    def test_login_invalid_mfa_login(self):
        """Tests that a login request with an invalid mfa entry fails."""
        # Register a user
        response = self.app.get('/register', follow_redirects=True)
        soup = beautifulsoup(response.data, 'html.parser')
        csrf_token = soup.find_all('input', id='csrf_token')[0]['value']
        response = self.register(uname='temp1234', pword='temp1234', csrf_token=csrf_token)
        self.assertEqual(response.status_code, 200)
        soup = beautifulsoup(response.data, 'html.parser')
        results = soup.find_all(id='success')
        self.assertGreater(len(results), 0, "No flash messages received")
        self.assertTrue(any("Registration success" in s.text for s in results))
        # Login without mfa
        csrf_token = soup.find_all('input', id='csrf_token')[0]['value']
        response = self.login(uname='temp1234', pword='temp1234', mfa='', csrf_token=csrf_token)
        self.assertEqual(response.status_code, 200)
        # Go to account page
        response = self.app.get('/account', follow_redirects=True)
        soup = beautifulsoup(response.data, 'html.parser')
        csrf_token = soup.find_all('input', id='csrf_token')[0]['value']
        # Start MFA setup
        response = self.update_account(mfa_enabled=True, csrf_token=csrf_token)
        soup = beautifulsoup(response.data, 'html.parser')
        csrf_token = soup.find_all('input', id='csrf_token')[0]['value']
        self.assertEqual(response.status_code, 200)
        # Confirm MFA setup
        response = self.mfa_confirm(mfa_confirm=True, csrf_token=csrf_token)
        soup = beautifulsoup(response.data, 'html.parser')
        # Check that mfa was stored
        with self.base_app.app_context():
            mfa_stored = MFA.query.filter_by(username='temp1234').first()
            self.assertFalse(mfa_stored is None)
            user_stored = Users.query.filter_by(username='temp1234').first()
            self.assertTrue(user_stored.mfa_registered)
        # Now logout
        response = self.logout()
        self.assertEqual(response.status_code, 200)
        # Now try to login with wrong mfa token
        response = self.app.get('/login', follow_redirects=True)
        soup = beautifulsoup(response.data, 'html.parser')
        csrf_token = soup.find_all('input', id='csrf_token')[0]['value']
        response = self.login(uname='temp1234', pword='temp1234', mfa='000000', csrf_token=csrf_token)
        self.assertEqual(response.status_code, 200)
        soup = beautifulsoup(response.data, 'html.parser')
        results = soup.find_all(id='result')
        self.assertTrue(any("Two-factor authentication failure" in s.text for s in results))

    def test_logout(self):
        """Tests that logout request is successful and redirects to expected page."""
        # Register a user
        response = self.app.get('/register', follow_redirects=True)
        soup = beautifulsoup(response.data, 'html.parser')
        csrf_token = soup.find_all('input', id='csrf_token')[0]['value']
        response = self.register(uname='temp1234', pword='temp1234', csrf_token=csrf_token)
        self.assertEqual(response.status_code, 200)
        soup = beautifulsoup(response.data, 'html.parser')
        results = soup.find_all(id='success')
        self.assertGreater(len(results), 0, "No flash messages received")
        self.assertTrue(any("Registration success" in s.text for s in results))
        # Login as a user
        csrf_token = soup.find_all('input', id='csrf_token')[0]['value']
        response = self.login(uname='temp1234', pword='temp1234', csrf_token=csrf_token)
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

    def test_login_history(self):
        """Tests that the login history page can be accessed by an admin user."""
        response = self.app.get('/login', follow_redirects=True)
        soup = beautifulsoup(response.data, 'html.parser')
        # Login as default admin
        csrf_token = soup.find_all('input', id='csrf_token')[0]['value']
        response = self.login(uname='replaceme', pword='replaceme', csrf_token=csrf_token)
        self.assertEqual(response.status_code, 200)
        soup = beautifulsoup(response.data, 'html.parser')
        results = soup.find_all(id='result')
        self.assertGreater(len(results), 0, "No flash messages received")
        self.assertTrue(any("Login success" in s.text for s in results))
        # Check out login history page
        response = self.app.get('/login_history', follow_redirects=True)
        soup = beautifulsoup(response.data, 'html.parser')
        csrf_token = soup.find_all('input', id='csrf_token')[0]['value']
        userid_to_query = 1
        response = self.query_userid_history(userid=userid_to_query, csrf_token=csrf_token)
        soup = beautifulsoup(response.data, 'html.parser')
        self.assertEqual(response.status_code, 200)
        login_userid_entry = int(soup.find_all('td', id='login_userid')[0].text)
        self.assertEqual(userid_to_query, login_userid_entry, "Retrieved history does not match userid queried.")
        self.assertGreater(len(soup.find_all('td', id='login_username')), 0, "No column entry with id 'login_username' found.")
        self.assertGreater(len(soup.find_all('td', id='login1')), 0, "No column entry with id 'login1' found.")
        self.assertGreater(len(soup.find_all('td', id='login1_time')), 0, "No column entry with id 'login1_time' found.")
        self.assertGreater(len(soup.find_all('td', id='logout1_time')), 0, "No column entry with id 'logout1_time' found.")


if __name__ == '__main__':
    unittest.main()
