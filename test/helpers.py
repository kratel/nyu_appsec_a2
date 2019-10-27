def register(app, uname, pword, mfa="", csrf_token=""):
    if mfa:
        pdata = { "username": uname,
                  "password": pword,
                  "mfa": mfa,
                  "csrf_token": csrf_token}
    else:
        pdata = { "username": uname,
                  "password": pword,
                  "csrf_token": csrf_token}
    return app.post(
        '/register',
        data=pdata,
        follow_redirects=True
    )
 
def login(app, uname, pword, mfa="", csrf_token=""):
    if mfa:
        pdata = { "username": uname,
                  "password": pword,
                  "mfa": mfa,
                  "csrf_token": csrf_token}
    else:
        pdata = { "username": uname,
                  "password": pword,
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

def spell_check_text(app, inputtext="", csrf_token=""):
    if inputtext:
        pdata = { "inputtext": inputtext,
                  "csrf_token": csrf_token}
    else:
        pdata = {"csrf_token": csrf_token}
    return app.post(
        '/spell_check',
        data=pdata,
        follow_redirects=True
    )
