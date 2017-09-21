var COLORS = {
  'White': '#ffffff',
  'Navy': 'rgb(18,40,76)',
  'Dark Grey': 'rgb(84,88,90)',
  'Cardinal': 'rgb(159,32,50)',
}

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

function onClickBuyThisTweet(tweetId) {
  log('clicked', tweetId);
  showModal();

  var previewContainer = $('<div class="btt-preview-container" />');
  var colorSelectorContainer = $('<div class="btt-color-selector-container" />');

  var divs = [];
  var selectors = [];

  for (color in COLORS) {
    if (COLORS.hasOwnProperty(color)) {
      var src = 'http://btt.brbrb.us/get_tshirt_mockup?tweet_id=' + tweetId + '&color=' + color;
      var img = $('<img class="btt-preview" src="' + src + '" />');
      var div = $('<div class="btt-preview btt-loading" />');
      var selector = $('<div class="btt-color-selector" style="background: ' + COLORS[color] + ';" />');
      var index = divs.length;

      img.on('load', (function(div) {
        return function(e) {
          div.removeClass('btt-loading');
          log('image loaded');
        };
      })(div));

      selector.on('click', (function(div, selector) {
        return function(e) {
          for (var i=0; i<divs.length; i++) {
            divs[i].hide();
            selectors[i].removeClass('btt-color-selected');
          }

          selector.addClass('btt-color-selected');
          div.show();
        };
      })(div, selector));

      divs.push(div);
      selectors.push(selector);

      div.hide();
      div.append(img);
      previewContainer.append(div);
      colorSelectorContainer.append(selector);
    }
  }

  // default to first color is displayed
  divs[0].show();
  selectors[0].addClass('btt-color-selected');

  _modalBody.append(previewContainer);
  _modalBody.append(colorSelectorContainer);

  // TODO: dynamic tweet author
  var handle = 'Interior';
  _modalFooter.append($('<div class="btt-user">Buy a tweet from ' +
                        '<span class="btt-handle">@' + handle + '</span>' +
                        '</div>'));

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
