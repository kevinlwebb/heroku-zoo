# Python: Getting Started

A barebones Flask app.

## Running Locally

Make sure you have Python 3.7 [installed locally](http://install.python-guide.org). To push to Heroku, you'll need to install the [Heroku CLI](https://devcenter.heroku.com/articles/heroku-cli).

```sh
$ git clone https://github.com/kevinlwebb/heroku-zoo.git
$ cd heroku-zoo

$ python3 -m venv heroku-env
$ pip3 install -r requirements.txt

$ flask run
```

Your app should now be running on [localhost:5000](http://localhost:5000/).

## Deploying to Heroku

[![Deploy to Heroku](https://www.herokucdn.com/deploy/button.png)](https://heroku.com/deploy)

## Documentation

For more information about using Python on Heroku, see these Heroku Dev Center articles:

- [Python on Heroku](https://devcenter.heroku.com/categories/python)

## Resources
https://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-i-hello-world
https://flask-sqlalchemy.palletsprojects.com/en/2.x/
https://www.palletsprojects.com/p/jinja/
https://www.palletsprojects.com/p/flask/