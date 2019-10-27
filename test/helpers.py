def register(app, uname, pword, mfa="", csrf_token=""):
    pdata = { "username": uname,
              "password": pword,
              "mfa": mfa,
              "csrf_token": csrf_token}
    return app.post(
        '/register',
        data=pdata,
        follow_redirects=True
    )
 
def login(app, uname, pword, mfa="", csrf_token=""):
    pdata = { "username": uname,
              "password": pword,
              "mfa": mfa,
              "csrf_token": csrf_token}
    return app.post(
        '/login',
        data=pdata,
        follow_redirects=True
    )
 
def logout(app):
    return app.get(
        '/logout',
        follow_redirects=True
    )