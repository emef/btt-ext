import urllib
import tempfile
import subprocess
import os

from gevent.wsgi import WSGIServer
from flask import Flask, url_for, redirect, render_template, request as flask_request
import requests

app = Flask(__name__)

# local configuration
hostname = 'http://localhost:5000'
path_to_chrome = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'

# constants
template = 'template.html'
oembed_endpoint = 'https://publish.twitter.com/oembed'
status_endpoint = 'https://twitter.com/statuses/'
zoom = '3'

# these options could be set by the client
default_options = {
  'hide_thread': 'true', # show the tweet to which you are replying
  'hide_media': 'false', # don't show images
}
# more params: https://dev.twitter.com/rest/reference/get/statuses/oembed

@app.route('/')
def index():
  return "hello. send tweet_id GET param to /render_png and follow redirects", 200, {'Content-Type': 'text/plain'}

# redirect user to phantomjs server with route back to us for template render
@app.route('/render_png')
def get_png():
  tweet_id=flask_request.args.get('tweet_id')
  print tweet_id

  redirect_url = hostname + url_for('get_html', tweet_id=tweet_id)

  outfd, outsock_path = tempfile.mkstemp(suffix='png')

  args = [
      path_to_chrome,
      '--headless',
      '--disable-gpu', # this kludge is required by current version of chrome
      '--screenshot=' + outsock_path,
      redirect_url,
      '--virtual-time-budget=1000', # add time to let javascript etc load.
      '--force-device-scale-factor=' + zoom, # zoom to render in higher DPI
      '--default-background-color=0', # what forces the background transparent
      '--window-size=516,700'] # 516 is tweet width = 500 exactly, + 8 (x2) for default html body padding. height is just whatever max
  print args
  subprocess.check_call(args)

  outsock = os.fdopen(outfd, 'rb')
  data = outsock.read()
  outsock.close()
  os.remove(outsock_path)

  return data, 200, {'Content-type': 'image/png'}

# render template for phantomjs to render
@app.route('/render_template')
def get_html():
  tweet_id=flask_request.args.get('tweet_id')
  html = fetch_tweet(tweet_id)
  print html
  return render_template(template, embed=html)

def fetch_tweet(tweet_id):
  get_tweet_url = status_endpoint + urllib.quote(tweet_id)
  print get_tweet_url
  redir = requests.head(get_tweet_url, allow_redirects=True)
  print redir.url
  get_embed_url = '%s?%s' % (oembed_endpoint, urllib.urlencode(dict(url=redir.url, omit_script='true', **default_options)))
  print get_embed_url
  response = requests.get(get_embed_url)

  response_json = response.json()

  # note: can tell the type of the tweet using "type" field
  return response_json['html']

if __name__ == '__main__':
  app.debug = True
  app.run(threaded=True) # threaded is important, or else it will hang badly on render.
