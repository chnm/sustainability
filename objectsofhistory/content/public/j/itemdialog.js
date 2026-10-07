// Open item pages (links marked data-dialog) in a modal <dialog>.
// showModal() traps focus, closes on Escape, and returns focus to the link.
document.addEventListener('click', function (e) {
	var link = e.target.closest && e.target.closest('a[data-dialog]');
	if (!link || e.button !== 0 || e.ctrlKey || e.metaKey || e.shiftKey || !window.HTMLDialogElement) return;
	e.preventDefault();
	var dialog = document.getElementById('item-dialog');
	if (!dialog) {
		dialog = document.createElement('dialog');
		dialog.id = 'item-dialog';
		dialog.innerHTML = '<form method="dialog"><button>Close</button></form><iframe></iframe>';
		// Unload the page on close so any playing media stops.
		dialog.addEventListener('close', function () { dialog.querySelector('iframe').src = 'about:blank'; });
		// A click on the backdrop lands on the dialog itself.
		dialog.addEventListener('click', function (ev) { if (ev.target === dialog) dialog.close(); });
		document.body.appendChild(dialog);
	}
	var frame = dialog.querySelector('iframe');
	var img = link.querySelector('img');
	frame.title = (img && img.alt) || link.textContent.trim() || 'Item';
	dialog.setAttribute('aria-label', frame.title);
	frame.src = link.href;
	dialog.showModal();
});
