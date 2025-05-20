function toggleModules() {
	var links = $('modulelinks');
	if(!links) return;
	links.hide();
	var header = $('modulelinksbutton');
	if(!header) return;
	header.style.cursor = "pointer";
	var color = header.style.color;
	header.onmouseover = function() {
		header.style.color = "#ff8000";
	}
	header.onmouseout = function() {
		header.style.color = color;
	}
	header.onclick = function() {
		new Effect.toggle(links,'blind',{duration:0.5});
		return false;
	}
}