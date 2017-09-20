var _log;
var _modal, _modalContainer, _modalOverlay, _modalBody, _modalFooter;

$(document).ready(function() {
  _modalOverlay = $('<div class="modal-overlay" style="z-index: 4001;" />');
  _modal = $('<div class="modal-container" />');
  var modalContent = $('<div class="modal-content" />');
  _modalContainer = $('<div class="modal" />');
  _modal.append(_modalContainer);
  _modalContainer.append(modalContent);

  _modal.click(hideModal);
  _modal.find("*").click(function(e) { e.stopPropagation(); });

  var modalHeader = $('<div class="modal-header">' +
                 '<h3 class="modal-title">Buy this tweet</h3>' +
                 '</div>');
  modalContent.append(modalHeader);

  _modalBody = $('<div class="modal-body modal-tweet btt-body" />');
  modalContent.append(_modalBody);

  _modalFooter = $('<div class="modal-tweet-form-container btt-footer" />');
  modalContent.append(_modalFooter);

  var modalClose = $('<button type="button" class="modal-btn modal-close js-close">' +
                     '<span class="Icon Icon--close Icon--medium" />' +
                     '</button>');
  modalClose.click(hideModal);
  modalContent.append(modalClose);

  hideModal();

  $(document.body).append(_modalOverlay);
  $(document.body).append(_modal);
});

function log() {
  if (!_log) {
    var i = document.createElement('iframe');
    i.style.display = 'none';
    document.body.appendChild(i);
    _log = i.contentWindow.console.log;
  }

  _log.apply(this, arguments);
}

function showModal() {
  var leftPx = ($(document).width() - _modalContainer.width()) / 2;
  _modalContainer.css("left", leftPx + "px");

  _modalOverlay.fadeIn(200);
  _modal.fadeIn(200);
  $(document).bind('keyup', escHandler);
}

function hideModal() {
  _modalOverlay.hide();
  _modal.hide();
  _modalBody.find('*').remove();
  _modalFooter.find('*').remove();
  $(document).unbind('keyup', escHandler);
}

function escHandler(e) {
  if (e.keyCode === 27) {
    hideModal();
  }
}

function onClickBuyThisTweet(tweetId, handle) {
  log('clicked', tweetId);
  showModal();

  var src = 'http://btt.brbrb.us/get_tshirt_mockup?tweet_id=' + tweetId + '&color=White';
  _modalBody.append($('<img src="' + src + '" />'));

  var checkout = 'http://btt.brbrb.us/order_form?tweet_id=' + tweetId + '&color=White&quantity=1&product-type=1&size=L';

  _modalFooter.append($('<div class="btt-user"><a href="' + checkout + '" class="btn btn-primary">Buy a tweet from ' +
                        '<span class="btt-handle">@' + handle + '</span>' +
                        '</a></div>'));

}

setInterval(function() {
  $('div .tweet').each(function(i, tweet) {
    var tweetId = tweet.getAttribute('data-tweet-id');
    var screenName = tweet.getAttribute('data-screen-name');
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

    $(bttDiv).click(function() { onClickBuyThisTweet(tweetId, screenName); });

    bttDiv.append(bttBtn);
    bttBtn.append(bttIconContainer);
    bttIconContainer.append(bttIcon);
    $(actionList).append(bttDiv);
  });
}, 50);
