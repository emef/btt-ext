import numpy as np
import subprocess
import tempfile
import os
import urllib
from PIL import Image

from flask import Flask, url_for, redirect, render_template, request as flask_request
import requests

app = Flask(__name__)
app.debug = True
app.threaded = True

# local configuration
PORT = 5000
HOSTNAME = 'http://localhost:%d' % PORT
CHROME_PATH = os.getenv(
  'CHROME_PATH',
  '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome')

# constants
TEMPLATE = 'template.html'
OEMBED_ENDPOINT = 'https://publish.twitter.com/oembed'
STATUS_ENDPOINT = 'https://twitter.com/statuses/'
ZOOM = '3'

# these options could be set by the client
DEFAULT_OPTIONS = {
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
  tweet_id = flask_request.args.get('tweet_id')
  print tweet_id

  outfd, outsock_path = screenshot_tweet(tweet_id)

  outsock = os.fdopen(outfd, 'rb')
  data = outsock.read()
  outsock.close()
  os.remove(outsock_path)

  return data, 200, {'Content-type': 'image/png'}

def screenshot_tweet(tweet_id):
  '''
  Take a screenshot of the given tweet via headless chrome.

  returns (fd, path) of the temporary png file created
  '''
  print 'chrome path', CHROME_PATH
  outfd, outsock_path = tempfile.mkstemp(suffix='.png')
  redirect_url = HOSTNAME + url_for('get_html', tweet_id=tweet_id)
  args = [
      CHROME_PATH,
      '--headless',
      '--disable-gpu', # this kludge is required by current version of chrome
      '--screenshot=' + outsock_path,
      redirect_url,
      '--virtual-time-budget=1000', # add time to let javascript etc load.
      '--force-device-scale-factor=' + ZOOM, # ZOOM to render in higher DPI
      '--default-background-color=0', # what forces the background transparent
      '--window-size=516,700'] # 516 is tweet width = 500 exactly, + 8 (x2) for default html body padding. height is just whatever max
  print args
  subprocess.check_call(args)

  crop_whitespace_inplace(outsock_path)

  return outfd, outsock_path

def crop_whitespace_inplace(path):
    pil_image = Image.open(path)
    np_array = np.array(pil_image)
    blank_px = [0, 0, 0, 0]
    mask = np_array != blank_px
    coords = np.argwhere(mask)
    x0, y0, z0 = coords.min(axis=0)
    x1, y1, z1 = coords.max(axis=0) + 1
    cropped_box = np_array[x0:x1, y0:y1, z0:z1]
    pil_image = Image.fromarray(cropped_box, 'RGBA')
    print(pil_image.width, pil_image.height)
    pil_image.save(path)

# render template for phantomjs to render
@app.route('/render_template')
def get_html():
  tweet_id=flask_request.args.get('tweet_id')
  html = fetch_tweet(tweet_id)
  #print html
  return render_template(TEMPLATE, embed=html)

def fetch_tweet(tweet_id):
  get_tweet_url = STATUS_ENDPOINT + urllib.quote(tweet_id)
  print get_tweet_url
  redir = requests.head(get_tweet_url, allow_redirects=True)
  print redir.url
  querystring = urllib.urlencode(dict(
    url=redir.url,
    omit_script='true',
    **DEFAULT_OPTIONS))
  get_embed_url = '%s?%s' % (OEMBED_ENDPOINT, querystring)
  print get_embed_url
  response = requests.get(get_embed_url)

  response_json = response.json()

  # note: can tell the type of the tweet using "type" field
  return response_json['html']

if __name__ == '__main__':
  app.run(threaded=True, port=PORT) # threaded is important, or else it will hang badly on render.
