/*-----------------------------------------------------------
    Toggles element's display value
    Input: any number of element id's
    Output: none 
    ---------------------------------------------------------*/
function toggleDisp() {
    for (var i=0;i<arguments.length;i++){
        var d = $(arguments[i]);
        if (d.style.display == 'none')
            d.style.display = 'block';
        else
            d.style.display = 'none';
    }
}
/*-----------------------------------------------------------
    Toggles tabs - Closes any open tabs, and then opens current tab
    Input:     1.The number of the current tab
                    2.The number of tabs
                    3.(optional)The number of the tab to leave open
                    4.(optional)Pass in true or false whether or not to animate the open/close of the tabs
    Output: none 
    ---------------------------------------------------------*/
function toggleTab(num,numelems,opennum,animate) {

    if($('panel'+num).style.display == 'none'){
        for (var i=1;i<=numelems;i++){

            var tempc = 'panel'+i;
            var c = $(tempc);
            if(c.style.display != 'none'){
                if (animate || typeof animate == 'undefined')
                    Effect.toggle(tempc,'appear',{duration:.7, queue:{scope:'menus', limit: 3}});
                else
                    toggleDisp(tempc);
            }
        }
        var c = $('panel'+num);
        c.style.marginTop = '2px';
        if (animate || typeof animate == 'undefined') {
            Effect.toggle('panel'+num,'appear',{duration:.7, queue:{scope:'menus', position:'end', limit: 3}});
 		}		
		else {
            toggleDisp('panel'+num);
        }
    }
}

function removeClasses(theArray) {
	for(var i=0;i<theArray.length;i++){
	theArray[i].removeClassName('current');
	}
}
function toggleNav() {
	var toggles = $$("div.panel");
	
	for (var i=0;i<toggles.length; i++) {
		toggles[i].style.display = "none";
		toggles[0].style.display = "block";
	}

	if(!$$("#content-nav a")) return;
	var links = $$("#content-nav a");
	if(!links[0]) return;
	links[0].addClassName('current');
	for (var i=0;i<links.length; i++) {
		var link = links[i];
		link.onclick = function() {
			var section = this.getAttribute("href").split("#panel")[1];
			removeClasses(links);
			this.toggleClassName('current','off');
			
			toggleTab(section,links.length);
			return false;
		}
	}
}

Event.observe(window,'load',toggleNav);
