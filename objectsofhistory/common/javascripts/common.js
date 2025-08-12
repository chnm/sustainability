function addLoadListener(fn) {
	if (typeof window.addEventListener != 'undefined') {
		window.addEventListener('load', fn, false);
	}
	else if (typeof document.addEventListener != 'undefined') {
		document.addEventListener('load', fn, false);
	}
	else if (typeof window.attachEvent != 'undefined') {
		window.attachEvent('onload', fn);
	}
	else {
		return false;
	}
	return true;
}

function attachEventListener(target, eventType, functionRef, capture){
    if (typeof target.addEventListener != "undefined") {
        target.addEventListener(eventType, functionRef, capture);
    }
    else if (typeof target.attachEvent != "undefined") {
        target.attachEvent("on" + eventType, functionRef);
    }
    else {
        return false;
    }
    return true;
}

function getElementsByAttribute(attribute, attributeValue)
{
  var elementArray = new Array();
  var matchedArray = new Array();

  if (document.all)
  {
    elementArray = document.all;
  }
  else
  {
    elementArray = document.getElementsByTagName("*");
  }

  for (var i = 0; i < elementArray.length; i++)
  {
    if (attribute == "class")
    {
      var pattern = new RegExp("(^| )" + attributeValue + "( |$)");

      if (pattern.test(elementArray[i].className))
      {
        matchedArray[matchedArray.length] = elementArray[i];
      }
    }
    else if (attribute == "for")
    {
      if (elementArray[i].getAttribute("htmlFor") || elementArray[i].getAttribute("for"))
      {
        if (elementArray[i].htmlFor == attributeValue)
        {
          matchedArray[matchedArray.length] = elementArray[i];
        }
      }
    }
    else if (elementArray[i].getAttribute(attribute) == attributeValue)
    {
      matchedArray[matchedArray.length] = elementArray[i];
    }
  }

  return matchedArray;
}

function getEventTarget(event)
{
  var targetElement = null;

  if (typeof event.target != "undefined")
  {
    targetElement = event.target;
  }
  else
  {
    targetElement = event.srcElement;
  }

  while (targetElement.nodeType == 3 && targetElement.parentNode != null)
  {
    targetElement = targetElement.parentNode;
  }

  return targetElement;
}

function getViewportSize()
{
  var size = [0,0];

  if (typeof window.innerWidth != 'undefined')
  {
    size = [
        window.innerWidth,
        window.innerHeight
    ];
  }
  else if (typeof document.documentElement != 'undefined'
      && typeof document.documentElement.clientWidth != 'undefined'
      && document.documentElement.clientWidth != 0)
  {
    size = [
        document.documentElement.clientWidth,
        document.documentElement.clientHeight
    ];
  }
  else
  {
    size = [
        document.getElementsByTagName('body')[0].clientWidth,
        document.getElementsByTagName('body')[0].clientHeight
    ];
  }

  return size;
}

function getScrollingPosition()
{
  //array for X and Y scroll position
  var position = [0, 0];

  //if the window.pageYOffset property is supported
  if(typeof window.pageYOffset != 'undefined')
  {
    //store position values
    position = [
        window.pageXOffset,
        window.pageYOffset
    ];
  }

  //if the documentElement.scrollTop property is supported
  //and the value is greater than zero
  if(typeof document.documentElement.scrollTop != 'undefined'
    && document.documentElement.scrollTop > 0)
  {
    //store position values
    position = [
        document.documentElement.scrollLeft,
        document.documentElement.scrollTop
    ];
  }

  //if the body.scrollTop property is supported
  else if(typeof document.body.scrollTop != 'undefined')
  {
    //store position values
    position = [
        document.body.scrollLeft,
        document.body.scrollTop
    ];
  }

  //return the array
  return position;
}

function insertAfter(newElement,targetElement) {
	var parent = targetElement.parentNode;
	if (parent.lastChild == targetElement) {
		parent.appendChild(newElement);
	} 
	else {
		parent.insertBefore(newElement,targetElement.nextSibling);
	}
}

// Nice function that helps you add alternating classes to any number of child elements.
function striper(parentElementTag, parentElementClass, childElementTag, styleClasses)
{
	var i=0,currentParent,currentChild;
	// capability and sanity check
	if ((document.getElementsByTagName)&&(parentElementTag)&&(childElementTag)&&(styleClasses)) {
		// turn the comma separate list of classes into an array
		var styles = styleClasses.split(',');
		// get an array of all parent tags
		var parentItems = document.getElementsByTagName(parentElementTag);
		// loop through all parent elements
		while (currentParent = parentItems[i++]) {
			// if parentElementClass was null, or if the current parent's class matches the specified class
			if ((parentElementClass == null)||(currentParent.className == parentElementClass)) {
				var j=0,k=0;
				// get all child elements in the current parent element
				var childItems = currentParent.getElementsByTagName(childElementTag);
				// loop through all child elements
				while (currentChild = childItems[j++]) {
					// based on the current element and the number of styles in the array, work out which class to apply
					k = (j+(styles.length-1)) % styles.length;
					// add the class to the child element - if any other classes were already present, they're kept intact
					currentChild.className = currentChild.className+" "+styles[k];
				}
			}
		}
	}
}

// Really handy function. Adds any class you want to any element you want.
function addClass(target, classValue) {
	var pattern = new RegExp("(^| )" + classValue + "( |$)");
	if (!pattern.test(target.className)) {
		if (target.className == "") {
			target.className = classValue;
		}
		else {
			target.className += " " + classValue;
		}
	}
	return true;
}

function makePopup(url, width, height, overflow)
{
  // if (width > 640) { width = 640; }
 //  if (height > 480) { height = 480; }

  if (overflow == '' || !/^(scroll|resize|both)$/.test(overflow))
  {
    overflow = 'both';
  }

  var win = window.open(url, '',
      'width=' + width + ',height=' + height
      + ',scrollbars=' + (/^(scroll|both)$/.test(overflow) ? 'yes' : 'no')
      + ',resizable=' + (/^(resize|both)$/.test(overflow) ? 'yes' : 'no')
      + ',status=yes,toolbar=no,menubar=no,location=no'
  );

  return win;
}

// Begin popup window function.
function popUps() {
	var links = getElementsByAttribute("class","popup");

	for (var i=0; i<links.length; i++) {
	link = links[i];
		link.onclick = function() {
			var popup = makePopup(this.href, 600, 600, 'scroll');
			return popup.closed;
		}  
	}
}

addLoadListener(popUps);