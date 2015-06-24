from app import app
app.secret_key = 'My special secret key'

if __name__ == "__main__":
    app.run()
