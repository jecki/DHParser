/******************************************************************************
 * This code handles:                                                         *
 * - the obsolete warning on outdated specs                                   *
 ******************************************************************************/
(function() {
  "use strict";

  var ESCAPEKEY = 27;
  /* Deprecation warning */
  if (document.location.hostname === "www.w3.org") {
    var request = new XMLHttpRequest();

    request.open('GET', '//www.w3.org/TR/tr-outdated-spec');
    request.onload = function() {
      if (request.status < 200 || request.status >= 400) {
        return;
      }
      try {
        var currentSpec = JSON.parse(request.responseText);
      } catch (err) {
        console.error(err);
        return;
      }
      document.body.classList.add("outdated-spec");
      var w3cCSS = document.querySelector('link[href*="www.w3.org/StyleSheets/TR/W3C-"]'); //old specs don't have the TR stylesheets
      var node = document.createElement("p");
      node.classList.add("outdated-warning");
      node.tabIndex = -1;
      node.setAttribute("role", "dialog");
      node.setAttribute("aria-modal", "true");
      node.setAttribute("aria-labelledby", "outdatedWarning");
      if (currentSpec.style) {
          node.classList.add(currentSpec.style);
      }

      var frag = document.createDocumentFragment();
      var heading = document.createElement("strong");
      heading.id = "outdatedWarning";
      heading.innerHTML = currentSpec.header;
      frag.appendChild(heading);

      var anchor = document.createElement("a");
      anchor.id = "outdated-note";
      anchor.href = currentSpec.latestUrl;
      anchor.innerText = currentSpec.latestUrl + ".";

      var warning = document.createElement("span");
      warning.innerText = currentSpec.warning;
      warning.appendChild(anchor);
      frag.appendChild(warning);

      if (w3cCSS) {
        var button = document.createElement("button");
        var handler = makeClickHandler(node);
        button.addEventListener("click", handler);
        button.innerHTML = "&#9662; collapse";
        frag.appendChild(button);
      }
      node.appendChild(frag);

      function makeClickHandler(node) {
        var isOpen = true;
        return function collapseWarning(event) {
          var button = event.target;
          isOpen = !isOpen;
          node.classList.toggle("outdated-collapsed");
          document.body.classList.toggle("outdated-spec");
          button.innerText = (isOpen) ? '\u25BE collapse' : '\u25B4 expand';
        }
      }

      document.body.appendChild(node);

      if (w3cCSS) {
        button.focus();
        window.onkeydown = function (event) {
          var isCollapsed = node.classList.contains("outdated-collapsed");
          if (event.keyCode === ESCAPEKEY && !isCollapsed) {
            button.click();
          }
        }

        document.addEventListener("focus", function(event) {
          var isCollapsed = node.classList.contains("outdated-collapsed");
          var containsTarget = node.contains(event.target);
          if (!isCollapsed && !containsTarget) {
            event.stopPropagation();
            node.focus();
          }
        }, true); // use capture to enable event delegation as focus doesn't bubble up
      }
    };

    request.onerror = function() {
      console.error("Request to https://www.w3.org/TR/tr-outdated-spec failed.");
    };

    request.send();
  }
})();
