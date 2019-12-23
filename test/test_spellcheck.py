"""
Tests the spellcheck module of the spellcheckapp.

Makes use of flask's test client to perform integration tests.
"""
import os
import pathlib
import sys
import tempfile
import unittest
from unittest.mock import patch

import app

import bs4


parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)

beautifulsoup = bs4.BeautifulSoup

spellcheck_path = './spell_check.out'
wordlist_path = 'wordlist.txt'


class TestAuth(unittest.TestCase):
    """Groups Spellcheck tests to use the same test client."""

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
                       "SPELLCHECK": spellcheck_path,
                       "WORDLIST": wordlist_path,
                       "SESSION_COOKIE_HTTPONLY": True,
                       "SESSION_COOKIE_SAMESITE": 'Lax',
                       "REMEMBER_COOKIE_HTTPONLY": True}
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

    def spell_check_text(self, inputtext="", csrf_token=""):
        """Helper function to issue a spell check submission."""
        if inputtext:
            pdata = {"inputtext": inputtext,
                     "csrf_token": csrf_token}
        else:
            pdata = {"csrf_token": csrf_token}
        return self.app.post(
            '/spell_check',
            data=pdata,
            follow_redirects=True
        )

    def query_user_spell_history(self, userquery=None, csrf_token=""):
        """Helper function to issue a request to view spell check history."""
        if userquery:
            pdata = {"userquery": userquery,
                     "csrf_token": csrf_token}
        else:
            pdata = {"csrf_token": csrf_token}
        return self.app.post(
            '/history',
            data=pdata,
            follow_redirects=True
        )

    # Tests Start
    def test_spell_check_get_no_login(self):
        """Tests that spell_check page will redirect to login if a guest user visits."""
        response = self.app.get('/spell_check', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        soup = beautifulsoup(response.data, 'html.parser')
        results = soup.find_all('title')
        # Should have redirected to login page
        self.assertTrue(any(("Log In" in s.text) for s in results))

    def test_spell_check_get_with_login(self):
        """Tests that spell_check page is retrieved successfully while logged in."""
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
        # Now get the spell_check page
        response = self.app.get('/spell_check', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        soup = beautifulsoup(response.data, 'html.parser')
        results = soup.find_all('title')
        self.assertTrue(any(("Spell Checker - Submission" in s.text) for s in results))
        self.assertGreater(len(soup.find_all('textarea', id="inputtext")), 0, "No textarea with id 'inputtext' found.")

    def test_spell_check_csrf(self):
        """Tests that csrf token is required for spell_check form submission."""
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
        # Now get the spell_check page
        response = self.app.get('/spell_check', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        soup = beautifulsoup(response.data, 'html.parser')
        self.assertGreater(len(soup.find_all('input', id='csrf_token')), 0, "No csrf token found in input.")

    @patch('subprocess.Popen')
    @patch('tempfile.TemporaryFile', unittest.mock.mock_open(read_data=b''))
    def test_mock_spell_check_basic_input(self, subproc):
        """Mocks spell check executable and tests that spell check submission works and correct words are treated as expected returning an element with id 'no_misspelled'."""  # noqa: E501
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
        # Now get the spell_check page
        response = self.app.get('/spell_check', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        soup = beautifulsoup(response.data, 'html.parser')
        results = soup.find_all('title')
        self.assertTrue(any(("Spell Checker - Submission" in s.text) for s in results))
        self.assertGreater(len(soup.find_all('textarea', id="inputtext")), 0, "No textarea with id 'inputtext' found.")
        # Setup mocks
        subproc.return_value = unittest.mock.MagicMock()
        # Submit some text to spell checker
        csrf_token = soup.find_all('input', id='csrf_token')[0]['value']
        inputtext = " Some correct words"
        response = self.spell_check_text(inputtext=inputtext, csrf_token=csrf_token)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(subproc.called)
        soup = beautifulsoup(response.data, 'html.parser')
        results = soup.find('p', id="textout")
        self.assertTrue(inputtext in results.text)
        results = soup.find('p', id="no_misspelled")
        self.assertTrue(results)

    @patch('subprocess.Popen')
    @patch('tempfile.TemporaryFile', unittest.mock.mock_open(read_data=b'flkfkef\nlkferf\n'))
    def test_mock_spell_check_basic_misspelled_input(self, subproc):
        """Mocks spell check executable and tests that spell check submission works and incorrect words are treated as expected returning a list of misspelled words."""  # noqa: E501
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
        # Now get the spell_check page
        response = self.app.get('/spell_check', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        soup = beautifulsoup(response.data, 'html.parser')
        results = soup.find_all('title')
        self.assertTrue(any(("Spell Checker - Submission" in s.text) for s in results))
        self.assertGreater(len(soup.find_all('textarea', id="inputtext")), 0, "No textarea with id 'inputtext' found.")
        # Setup mocks
        subproc.return_value = unittest.mock.MagicMock()
        # Submit some text to spell checker
        csrf_token = soup.find_all('input', id='csrf_token')[0]['value']
        inputtext = " Some incorrect words "
        misspelled_words = "flkfkef lkferf"
        inputtext += misspelled_words
        response = self.spell_check_text(inputtext=inputtext, csrf_token=csrf_token)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(subproc.called)
        soup = beautifulsoup(response.data, 'html.parser')
        results = soup.find('p', id="textout")
        self.assertEqual(inputtext, results.text.replace("'", ''))
        results = soup.find('p', id="misspelled")
        misspelled_words_out = results.text.split(", ")
        self.assertEqual(len(misspelled_words_out), 2, "Did not return expected amount of misspelled words")
        for word in misspelled_words_out:
            self.assertTrue(word in misspelled_words, "Expected misspelled word not returned.")

    @patch('subprocess.Popen')
    @patch('tempfile.TemporaryFile', unittest.mock.mock_open(read_data=b'flkfkef\nlkferf\n'))
    def test_mock_spell_check_history(self, subproc):
        """Mocks spell check executable and tests that spell check history renders correctly."""
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
        # Now get the spell_check page
        response = self.app.get('/spell_check', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        soup = beautifulsoup(response.data, 'html.parser')
        results = soup.find_all('title')
        self.assertTrue(any(("Spell Checker - Submission" in s.text) for s in results))
        self.assertGreater(len(soup.find_all('textarea', id="inputtext")), 0, "No textarea with id 'inputtext' found.")
        # Setup mocks
        subproc.return_value = unittest.mock.MagicMock()
        # Submit some text to spell checker
        csrf_token = soup.find_all('input', id='csrf_token')[0]['value']
        inputtext = " Some incorrect words "
        misspelled_words = "flkfkef lkferf"
        inputtext += misspelled_words
        response = self.spell_check_text(inputtext=inputtext, csrf_token=csrf_token)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(subproc.called)
        soup = beautifulsoup(response.data, 'html.parser')
        results = soup.find('p', id="textout")
        self.assertEqual(inputtext, results.text.replace("'", ''))
        results = soup.find('p', id="misspelled")
        misspelled_words_out = results.text.split(", ")
        self.assertEqual(len(misspelled_words_out), 2, "Did not return expected amount of misspelled words")
        for word in misspelled_words_out:
            self.assertTrue(word in misspelled_words, "Expected misspelled word not returned.")
        # Now test that spell check history page stored our word.
        response = self.app.get('/history', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        soup = beautifulsoup(response.data, 'html.parser')
        results = soup.find('h3', id="numqueries")
        self.assertEqual("1", results.text)
        results = soup.find('a', id="query1")
        self.assertEqual("Query 1", results.text)

    @patch('subprocess.Popen')
    @patch('tempfile.TemporaryFile', unittest.mock.mock_open(read_data=b'flkfkef\nlkferf\n'))
    def test_mock_admin_spell_check_history(self, subproc):
        """Mocks spell check executable and tests that admin view of spell check history renders correctly. Also tests that admin can query for other user's histories."""  # noqa: E501
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
        # Now get the spell_check page
        response = self.app.get('/spell_check', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        soup = beautifulsoup(response.data, 'html.parser')
        results = soup.find_all('title')
        self.assertTrue(any(("Spell Checker - Submission" in s.text) for s in results))
        self.assertGreater(len(soup.find_all('textarea', id="inputtext")), 0, "No textarea with id 'inputtext' found.")
        # Setup mocks
        subproc.return_value = unittest.mock.MagicMock()
        # Submit some text to spell checker
        csrf_token = soup.find_all('input', id='csrf_token')[0]['value']
        inputtext = " Some incorrect words "
        misspelled_words = "flkfkef lkferf"
        inputtext += misspelled_words
        response = self.spell_check_text(inputtext=inputtext, csrf_token=csrf_token)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(subproc.called)
        soup = beautifulsoup(response.data, 'html.parser')
        results = soup.find('p', id="textout")
        self.assertEqual(inputtext, results.text.replace("'", ''))
        results = soup.find('p', id="misspelled")
        misspelled_words_out = results.text.split(", ")
        self.assertEqual(len(misspelled_words_out), 2, "Did not return expected amount of misspelled words")
        for word in misspelled_words_out:
            self.assertTrue(word in misspelled_words, "Expected misspelled word not returned.")
        # Logout
        response = self.logout()
        self.assertEqual(response.status_code, 200)
        # Login as admin
        response = self.app.get('/login', follow_redirects=True)
        soup = beautifulsoup(response.data, 'html.parser')
        # Login as default admin
        csrf_token = soup.find_all('input', id='csrf_token')[0]['value']
        response = self.login(uname='replaceme', pword='replaceme', csrf_token=csrf_token)
        self.assertEqual(response.status_code, 200)
        # Now test that spell check history page stored our word.
        response = self.app.get('/history', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        soup = beautifulsoup(response.data, 'html.parser')
        results = soup.find('h3', id="numqueries")
        self.assertEqual("0", results.text)
        # Query another User's history
        csrf_token = soup.find_all('input', id='csrf_token')[0]['value']
        username_to_query = "temp1234"
        response = self.query_user_spell_history(userquery=username_to_query, csrf_token=csrf_token)
        soup = beautifulsoup(response.data, 'html.parser')
        self.assertEqual(response.status_code, 200)
        results = soup.find('h3', id="numqueries")
        self.assertEqual("1", results.text)
        results = soup.find('a', id="query1")
        self.assertEqual("Query 1", results.text)
        results = soup.find('h2')
        self.assertTrue('temp1234' in results.text)

    @patch('subprocess.Popen')
    @patch('tempfile.TemporaryFile', unittest.mock.mock_open(read_data=b'flkfkef\nlkferf\n'))
    def test_mock_spell_check_query(self, subproc):
        """Mocks spell check executable and tests that spell check query page is created and renders correctly."""
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
        # Now get the spell_check page
        response = self.app.get('/spell_check', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        soup = beautifulsoup(response.data, 'html.parser')
        results = soup.find_all('title')
        self.assertTrue(any(("Spell Checker - Submission" in s.text) for s in results))
        self.assertGreater(len(soup.find_all('textarea', id="inputtext")), 0, "No textarea with id 'inputtext' found.")
        # Setup mocks
        subproc.return_value = unittest.mock.MagicMock()
        # Submit some text to spell checker
        csrf_token = soup.find_all('input', id='csrf_token')[0]['value']
        inputtext = " Some incorrect words "
        misspelled_words = "flkfkef lkferf"
        inputtext += misspelled_words
        response = self.spell_check_text(inputtext=inputtext, csrf_token=csrf_token)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(subproc.called)
        soup = beautifulsoup(response.data, 'html.parser')
        results = soup.find('p', id="textout")
        self.assertEqual(inputtext, results.text.replace("'", ''))
        results = soup.find('p', id="misspelled")
        misspelled_words_out = results.text.split(", ")
        self.assertEqual(len(misspelled_words_out), 2, "Did not return expected amount of misspelled words")
        for word in misspelled_words_out:
            self.assertTrue(word in misspelled_words, "Expected misspelled word not returned.")
        # Now test that spell check history page stored our word.
        response = self.app.get('/history', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        soup = beautifulsoup(response.data, 'html.parser')
        results = soup.find('h3', id="numqueries")
        self.assertEqual("1", results.text)
        results = soup.find('a', id="query1")
        query_url = results['href']
        self.assertEqual("Query 1", results.text)
        # Now test that the url was generated and we can access it.
        response = self.app.get(query_url, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        soup = beautifulsoup(response.data, 'html.parser')
        results = soup.find('td', id="querytext")
        self.assertEqual(inputtext, results.text.replace("'", ''))
        results = soup.find('td', id="queryresults")
        misspelled_words_out = results.text.split(", ")
        self.assertEqual(len(misspelled_words_out), 2, "Query result page did not store expected amount of misspelled words")
        for word in misspelled_words_out:
            self.assertTrue(word in misspelled_words, "Expected misspelled word not stored in query page.")

    @unittest.skipIf(((not pathlib.Path(spellcheck_path).exists()) or (not pathlib.Path(wordlist_path).exists())), 'Spellcheck executable or wordlist not in appropriate path.')  # noqa: E501
    def test_spell_check_basic_input(self):
        """Tests that spell check submission works and correct words are treated as expected returning an element with id 'no_misspelled'."""
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
        # Now get the spell_check page
        response = self.app.get('/spell_check', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        soup = beautifulsoup(response.data, 'html.parser')
        results = soup.find_all('title')
        self.assertTrue(any(("Spell Checker - Submission" in s.text) for s in results))
        self.assertGreater(len(soup.find_all('textarea', id="inputtext")), 0, "No textarea with id 'inputtext' found.")
        # Submit some text to spell checker
        csrf_token = soup.find_all('input', id='csrf_token')[0]['value']
        inputtext = " Some correct words"
        response = self.spell_check_text(inputtext=inputtext, csrf_token=csrf_token)
        self.assertEqual(response.status_code, 200)
        soup = beautifulsoup(response.data, 'html.parser')
        results = soup.find('p', id="textout")
        self.assertTrue(inputtext in results.text)
        results = soup.find('p', id="no_misspelled")
        self.assertTrue(results)

    @unittest.skipIf(((not pathlib.Path(spellcheck_path).exists()) or (not pathlib.Path(wordlist_path).exists())), 'Spellcheck executable or wordlist not in appropriate path.')  # noqa: E501
    def test_spell_check_basic_misspelled_input(self):
        """Tests that spell check submission works and incorrect words are treated as expected returning a list of misspelled words."""
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
        # Now get the spell_check page
        response = self.app.get('/spell_check', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        soup = beautifulsoup(response.data, 'html.parser')
        results = soup.find_all('title')
        self.assertTrue(any(("Spell Checker - Submission" in s.text) for s in results))
        self.assertGreater(len(soup.find_all('textarea', id="inputtext")), 0, "No textarea with id 'inputtext' found.")
        # Submit some text to spell checker
        csrf_token = soup.find_all('input', id='csrf_token')[0]['value']
        inputtext = " Some incorrect words "
        misspelled_words = "flkfkef lkferf"
        inputtext += misspelled_words
        response = self.spell_check_text(inputtext=inputtext, csrf_token=csrf_token)
        self.assertEqual(response.status_code, 200)
        soup = beautifulsoup(response.data, 'html.parser')
        results = soup.find('p', id="textout")
        self.assertEqual(inputtext, results.text.replace("'", ''))
        results = soup.find('p', id="misspelled")
        misspelled_words_out = results.text.split(", ")
        self.assertEqual(len(misspelled_words_out), 2, "Did not return expected amount of misspelled words")
        for word in misspelled_words_out:
            self.assertTrue(word in misspelled_words, "Expected misspelled word not returned.")


if __name__ == '__main__':
    unittest.main()
