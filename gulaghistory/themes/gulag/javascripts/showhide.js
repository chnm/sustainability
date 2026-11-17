function toggleTranscript() {
	var header = $('transcription-header');
	if(!header) return;
	header.style.cursor = "pointer";
	header.style.background = "#c7d5e3";
	header.style.padding = "12px";
	header.style.width = "14em";
	header.style.margin = "0";
	var transcript = $('transcription-text');
	transcript.style.background = "#c7d5e3";
	transcript.style.padding = "12px";
	transcript.hide();
	
	header.onclick = function() {
		
		new Effect.toggle(transcript,'blind');
		return;
	}
}

//Event.observe(window,'load',toggleTranscript);