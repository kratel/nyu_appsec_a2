import unittest
import os
import tempfile
import pathlib

import bs4

import app

from spellcheckapp.db import get_db
from test.helpers import register, login, logout, spell_check_text

beautifulsoup = bs4.BeautifulSoup

spellcheck_path = './spell_check.out'
wordlist_path = 'wordlist.txt'

class TestAuth(unittest.TestCase):
    def setUp(self):
        db_fd, database_name = tempfile.mkstemp()
        test_config = { "SECRET_KEY":'test',
                        "TESTING": True,
                        "DATABASE": database_name,
                        "SPELLCHECK": spellcheck_path,
                        "WORDLIST": wordlist_path}
        base_app = app.create_app(test_config)
        self.app = base_app.test_client()
        self.db_fd = db_fd
        self.database_name = database_name
        self.base_app = base_app

    def tearDown(self):
        os.close(self.db_fd)
        os.unlink(self.database_name)

    def test_spell_check_get_no_login(self):
        response = self.app.get('/spell_check', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        soup = beautifulsoup(response.data, 'html.parser')
        results = soup.find_all('title')
        # Should have redirected to login page
        self.assertTrue(any(("Log In" in s.text) for s in results))

    def test_spell_check_get_with_login(self):
        # Register a user
        response = self.app.get('/register', follow_redirects=True)
        soup = beautifulsoup(response.data, 'html.parser')
        csrf_token = soup.find_all('input', id='csrf_token')[0]['value']
        response = register(app=self.app, uname='temp1234', pword='temp1234', mfa='1234', csrf_token=csrf_token)
        self.assertEqual(response.status_code, 200)
        soup = beautifulsoup(response.data, 'html.parser')
        results = soup.find_all(id='success')
        self.assertGreater(len(results), 0, "No flash messages received")
        self.assertTrue(any("Registration success" in s.text for s in results))
        # Login as a user
        csrf_token = soup.find_all('input', id='csrf_token')[0]['value']
        response = login(app=self.app, uname='temp1234', pword='temp1234', mfa='1234', csrf_token=csrf_token)
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
        self.assertTrue(any(("Spell Checker - Spell Checker" in s.text) for s in results))
        self.assertGreater(len(soup.find_all('textarea', id="inputtext")), 0, "No textarea with id 'inputtext' found.")

    def test_spell_check_csrf(self):
        # Register a user
        response = self.app.get('/register', follow_redirects=True)
        soup = beautifulsoup(response.data, 'html.parser')
        csrf_token = soup.find_all('input', id='csrf_token')[0]['value']
        response = register(app=self.app, uname='temp1234', pword='temp1234', mfa='1234', csrf_token=csrf_token)
        self.assertEqual(response.status_code, 200)
        soup = beautifulsoup(response.data, 'html.parser')
        results = soup.find_all(id='success')
        self.assertGreater(len(results), 0, "No flash messages received")
        self.assertTrue(any("Registration success" in s.text for s in results))
        # Login as a user
        csrf_token = soup.find_all('input', id='csrf_token')[0]['value']
        response = login(app=self.app, uname='temp1234', pword='temp1234', mfa='1234', csrf_token=csrf_token)
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

    @unittest.skipIf(((not pathlib.Path(spellcheck_path).exists()) and (not pathlib.Path(wordlist_path).exists())), 'Spellcheck executable or wordlist not in appropriate path.')
    def test_spell_check_basic_input(self):
        # Register a user
        response = self.app.get('/register', follow_redirects=True)
        soup = beautifulsoup(response.data, 'html.parser')
        csrf_token = soup.find_all('input', id='csrf_token')[0]['value']
        response = register(app=self.app, uname='temp1234', pword='temp1234', mfa='1234', csrf_token=csrf_token)
        self.assertEqual(response.status_code, 200)
        soup = beautifulsoup(response.data, 'html.parser')
        results = soup.find_all(id='success')
        self.assertGreater(len(results), 0, "No flash messages received")
        self.assertTrue(any("Registration success" in s.text for s in results))
        # Login as a user
        csrf_token = soup.find_all('input', id='csrf_token')[0]['value']
        response = login(app=self.app, uname='temp1234', pword='temp1234', mfa='1234', csrf_token=csrf_token)
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
        self.assertTrue(any(("Spell Checker - Spell Checker" in s.text) for s in results))
        self.assertGreater(len(soup.find_all('textarea', id="inputtext")), 0, "No textarea with id 'inputtext' found.")
        # Submit some text to spell checker
        csrf_token = soup.find_all('input', id='csrf_token')[0]['value']
        inputtext = " Some correct words"
        response = spell_check_text(app=self.app, inputtext=inputtext, csrf_token=csrf_token)
        self.assertEqual(response.status_code, 200)
        soup = beautifulsoup(response.data, 'html.parser')
        results = soup.find('p', id="textout")
        # Text won't be equal because inputtext has a carriage return appended to it.
        self.assertTrue(inputtext in results.text)
        results = soup.find('p', id="no_misspelled")
        self.assertTrue(results)

    @unittest.skipIf(((not pathlib.Path(spellcheck_path).exists()) and (not pathlib.Path(wordlist_path).exists())), 'Spellcheck executable or wordlist not in appropriate path.')
    def test_spell_check_basic_misspelled_input(self):
        # Register a user
        response = self.app.get('/register', follow_redirects=True)
        soup = beautifulsoup(response.data, 'html.parser')
        csrf_token = soup.find_all('input', id='csrf_token')[0]['value']
        response = register(app=self.app, uname='temp1234', pword='temp1234', mfa='1234', csrf_token=csrf_token)
        self.assertEqual(response.status_code, 200)
        soup = beautifulsoup(response.data, 'html.parser')
        results = soup.find_all(id='success')
        self.assertGreater(len(results), 0, "No flash messages received")
        self.assertTrue(any("Registration success" in s.text for s in results))
        # Login as a user
        csrf_token = soup.find_all('input', id='csrf_token')[0]['value']
        response = login(app=self.app, uname='temp1234', pword='temp1234', mfa='1234', csrf_token=csrf_token)
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
        self.assertTrue(any(("Spell Checker - Spell Checker" in s.text) for s in results))
        self.assertGreater(len(soup.find_all('textarea', id="inputtext")), 0, "No textarea with id 'inputtext' found.")
        # Submit some text to spell checker
        csrf_token = soup.find_all('input', id='csrf_token')[0]['value']
        inputtext = " Some incorrect words "
        misspelled_words = "flkfkef lkferf"
        inputtext += misspelled_words
        response = spell_check_text(app=self.app, inputtext=inputtext, csrf_token=csrf_token)
        self.assertEqual(response.status_code, 200)
        soup = beautifulsoup(response.data, 'html.parser')
        results = soup.find('p', id="textout")
        # Text won't be equal because inputtext has a carriage return appended to it.
        self.assertTrue(inputtext in results.text)
        results = soup.find('p', id="misspelled")
        misspelled_words_out = results.text.split(", ")
        self.assertEqual(len(misspelled_words_out), 2, "Did not return expected amount of misspelled words")
        for word in misspelled_words_out:
            self.assertTrue(word in misspelled_words, "Expected misspelled word not returned.")


if __name__ == '__main__':
    unittest.main()
