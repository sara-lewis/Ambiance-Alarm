## Getting Started

```
cd ~/Desktop/final/alarm
source venv/bin/activate
source .env
flask run
```

To turn off virtual environment
```
deactivate
```

To open in `Atom`
```
atom .
```

## Pushing to Heroku

```
heroku login
git add .
git commit -m "ready to push to heroku"
git push heroku master
heroku open
```

