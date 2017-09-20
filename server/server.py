from functools import partial
import os
from StringIO import StringIO
import subprocess
import tempfile
import urllib
import json

from flask import (
    abort,
    Flask,
    redirect,
    render_template,
    request as flask_request,
    send_file,
    Response,
    url_for)
import numpy as np
from PIL import Image

import requests
from requests.auth import HTTPBasicAuth

app = Flask(__name__)
app.debug = True
app.threaded = True

# local configuration
PORT = 5000
HOSTNAME = 'http://localhost:%d' % PORT
CHROME_PATH = os.getenv(
  'CHROME_PATH',
  '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome')

PRE_RENDER_PATH = os.getenv(
  'PRE_RENDER_PATH',
  '/tmp/pre_render/')

PRE_RENDER_ENABLED = os.getenv('PRE_RENDER_ENABLED', 'false') == 'true'

if not os.path.exists(PRE_RENDER_PATH):
  os.makedirs(PRE_RENDER_PATH)

# constants
TEMPLATE = 'template.html'
OEMBED_ENDPOINT = 'https://publish.twitter.com/oembed'
STATUS_ENDPOINT = 'https://twitter.com/statuses/'
ZOOM = '3'

SCALABLE_PRESS_API = "https://api.scalablepress.com/v2/"
SCALABLE_PRESS_KEY = os.getenv("SCALABLE_PRESS_KEY", "12345")
CHUNK_SIZE = 1024

# these options could be set by the client
DEFAULT_OPTIONS = {
  'hide_thread': 'true', # show the tweet to which you are replying
  'hide_media': 'false', # don't show images
}
# more params: https://dev.twitter.com/rest/reference/get/statuses/oembed

LOG = open('/opt/buythistweet/buythistweet.log', 'a')

@app.route('/')
def index():
  return "hello. send tweet_id GET param to /render_png and follow redirects", 200, {'Content-Type': 'text/plain'}

# redirect user to phantomjs server with route back to us for template render
@app.route('/render_png')
def get_png():
  tweet_id = flask_request.args.get('tweet_id')
  print tweet_id

  image_data = get_tweet_image_stream(tweet_id)

  return send_file(image_data, 'image/png')

@app.route('/get_tshirt_mockup')
def get_tshirt_mockup():
  tweet_id = flask_request.args.get('tweet_id')
  color = flask_request.args.get('tweet_id', 'White')
  image_data = get_tweet_image_stream(tweet_id)
  mockup_response = scalable_press_mockup_api(tweet_id, image_data, color)
  LOG.write(json.dumps(mockup_response) + '\n')

  if 'url' in mockup_response:
    url = mockup_response['url']
    LOG.write('streaming ' + url + '\n')
    with requests.get(url, stream=True) as img_stream:
      return Response(
        # (chunk for chunk in img_stream.iter_content(CHUNK_SIZE)),
        img_stream.content,
        status=200,
        content_type='image/png')

  else:
    # error
    response = json.dumps(mockup_response)
    return response, 200,  {'Content-Type': 'application/json'}

def get_tweet_image_stream(tweet_id):
  '''
  Get tweet screenshot image as a stream. May use pre-rendered version.
  '''
  pre_rendered_path = os.path.join(PRE_RENDER_PATH, tweet_id + '.png')
  if PRE_RENDER_ENABLED and os.path.exists(pre_rendered_path):
    return open(pre_rendered_path, 'rb')

  outfd, outsock_path = screenshot_tweet(tweet_id)

  try:
    image_data = read_and_post_process(outsock_path)

  finally:
    outsock = os.fdopen(outfd, 'w')
    outsock.close()
    os.remove(outsock_path)

  if PRE_RENDER_ENABLED:
    with open(pre_rendered_path, 'w') as f:
      f.write(image_data.read())

    image_data.seek(0)

  return image_data

def screenshot_tweet(tweet_id):
  '''
  Take a screenshot of the given tweet via headless chrome.

  returns (fd, path) of the temporary png file created
  '''
  outfd, outsock_path = tempfile.mkstemp(suffix='.png')
  redirect_url = HOSTNAME + url_for('get_html', tweet_id=tweet_id)
  args = [
      CHROME_PATH,
      '--headless',
      '--disable-gpu', # this kludge is required by current version of chrome
      '--screenshot=' + outsock_path,
      redirect_url,
      '--virtual-time-budget=3000', # add time to let javascript etc load.
      '--force-device-scale-factor=' + ZOOM, # ZOOM to render in higher DPI
      '--default-background-color=0', # what forces the background transparent
      '--window-size=516,700'] # 516 is tweet width = 500 exactly, + 8 (x2) for default html body padding. height is just whatever max
  print args
  subprocess.check_call(args)

  return outfd, outsock_path

def read_and_post_process(path):
  pil_image = Image.open(path)
  np_array = np.array(pil_image)
  blank_px = [0, 0, 0, 0]
  mask = np_array != blank_px
  coords = np.argwhere(mask)
  x0, y0, z0 = coords.min(axis=0)
  x1, y1, z1 = coords.max(axis=0) + 1
  cropped_box = np_array[x0:x1, y0:y1, z0:z1]
  pil_image = Image.fromarray(cropped_box, 'RGBA')
  img_buffer = StringIO()
  pil_image.save(img_buffer, format='PNG')
  img_buffer.seek(0) # only works on StringIO, not cStringIO
  return img_buffer

# render template for phantomjs to render
@app.route('/render_template')
def get_html():
  tweet_id=flask_request.args.get('tweet_id')
  html = fetch_tweet(tweet_id)
  #print html
  return render_template(TEMPLATE, embed=html)

@app.route('/press/<path:endpoint>', methods=('GET', 'POST'))
def press_proxy(endpoint):
  url = SCALABLE_PRESS_API + endpoint

  make_request = None

  if flask_request.method == 'GET':
    make_request = requests.get
    url += '?' + urllib.urlencode(flask_request.args)

  elif flask_request.method == 'POST':
    headers = {
      'Content-type': flask_request.headers.get('Content-type'),
      'Content-length': str(len(flask_request.data))
    }
    make_request = partial(
      requests.post,
      headers=headers,
      data=flask_request.data)

  response = make_request(
    url,
    stream=True,
    auth=HTTPBasicAuth("", SCALABLE_PRESS_KEY))

  print "Fetch", response.status_code, flask_request.method, url

  def generate():
    for chunk in response.iter_content(CHUNK_SIZE):
      yield chunk

  # note: does not pass along redirect header if any, would need to be rewritten

  return Response(
    generate(),
    status=response.status_code,
    content_type=response.headers.get('Content-type'))

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

def scalable_press_mockup_api(tweet_id, img_data, color):
  fields = {
    'template[name]': 'front',
    'product[id]': 'canvas-unisex-t-shirt',
    'product[color]': color,
    'design[type]': 'dtg',
    'design[sides][front][artwork]': '%simg/%s.png' % (flask_request.host_url, tweet_id),
    'design[sides][front][dimensions][width]': '8',
    'design[sides][front][position][horizontal]': 'C',
    'design[sides][front][position][offset][top]': '2.5',
    'output[width]': '1000',
    'output[height]': '1000',
    'padding[height]': '10',
    'output[format]': 'png',
  }

  r = requests.post(
    'https://api.scalablepress.com/v3/mockup',
    data=fields,
    auth=HTTPBasicAuth('', SCALABLE_PRESS_KEY))

  return r.json()



if __name__ == '__main__':
  app.run(threaded=True, port=PORT) # threaded is important, or else it will hang badly on render.
