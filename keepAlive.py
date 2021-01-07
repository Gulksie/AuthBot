# the purpose of this file is to setup a flask webserver to prevent repl.it from closing our program
from flask import Flask
from threading import Thread

app = Flask('/')

@app.route('/')
def home():
    return "Keep alive for discord bot. Check it out at https://github.com/Gulksie/AuthBot"

def run():
    Thread(target=lambda: app.run(host='0.0.0.0', port=8080)).start()