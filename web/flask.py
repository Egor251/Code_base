from flask import Flask

app = Flask(name)

@app.route('/')
def hello_world():
  return 'Hello, World!'

@app.route('/about')
def about():
  return 'This is the about page'


@app.route('/submit', methods=['POST'])
def submit():
  name = flask.request.form['name']
  return f'Hello, {name}'

if __name__ == '__main__':
  app.run(debug=True)