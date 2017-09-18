var _log = null;
var _overlay = null;
var _modal = null;

function log() {
  if (!_log) {
    var i = document.createElement('iframe');
    i.style.display = 'none';
    document.body.appendChild(i);
    _log = i.contentWindow.console.log;
  }

  _log.apply(this, arguments);
}

function modal() {
  if (!_modal) {
    _modal = $('<div />');
  }

  if (!overlay) {
    _overlay = $('<div class="modal-overlay" style="z-index: 4001;" />');
  }

  return _modal;
}

function onClickBuyThisTweet(tweetId) {
  log('clicked', tweetId);

}

setInterval(function() {
  $('div .tweet').each(function(i, tweet) {
    var tweetId = tweet.getAttribute('data-tweet-id');
    var actionList = $(tweet).find('.js-actions');

    if (!tweetId || !actionList) {
      return;
    } else if (tweet.getAttribute('data-tweet-btt')) {
      return;
    } else {
      tweet.setAttribute('data-tweet-btt', 'true');
    }

    var bttDiv = $('<div class="ProfileTweet-action" />');
    var bttBtn = $('<button class="ProfileTweet-actionButton ' +
                   'u-textUserColorHover js-actionButton" type="button" />');
    var bttIconContainer = $('<div class="IconContainer js-tooltip" ' +
                             'data-original-title="Buy this tweet" />');
    var bttIcon = $('<span class="Icon Icon--medium Icon--btt"></span>');

    $(bttDiv).click(function() { onClickBuyThisTweet(tweetId); });

    bttDiv.append(bttBtn);
    bttBtn.append(bttIconContainer);
    bttIconContainer.append(bttIcon);
    $(actionList).append(bttDiv);

  });
}, 50);
