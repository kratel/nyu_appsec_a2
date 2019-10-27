def register(self, uname, pword, mfa=""):
    pdata = { "uname": uname,
              "pword": pword,
              "2fa": mfa}
    return self.app.post(
        '/register',
        data=pdata,
        follow_redirects=True
    )
 
def login(self, email, password):
    return self.app.post(
        '/login',
        data=dict(email=email, password=password),
        follow_redirects=True
    )
 
def logout(self):
    return self.app.get(
        '/logout',
        follow_redirects=True
    )