import unittest
import os
import tempfile

import bs4

import auth
import app
from test.helpers import register, login, logout

beautifulsoup = bs4.BeautifulSoup

class TestAuth(unittest.TestCase):
	def setUp(self):
		db_fd, database_name = tempfile.mkstemp()
		test_config = { "SECRET_KEY":'test',
						"TESTING": True,
						"DATABASE": database_name,
						"SPELLCHECK":'./spell_check.out',
						"WORDLIST":'wordlist.txt'}
		base_app = app.create_app(test_config)
		self.app = base_app.test_client()
		self.db_fd = db_fd
		self.database_name = database_name

	def tearDown(self):
		os.close(self.db_fd)
		os.unlink(self.database_name)

	def test_register_get(self):
		response = self.app.get('/register', follow_redirects=True)
		soup = beautifulsoup(response.data, 'html.parser')
		self.assertEqual(response.status_code, 200)


if __name__ == '__main__':
	unittest.main()
