function roundCorners() {
	Nifty("div#teachermaterials a", "transparent");
	Nifty("h3.item-section-title", "transparent top");
	Nifty("p.item-section-content", "transparent tr bl br");
	Nifty("ul#sitenav a", "transparent");
	Nifty("ul.sectionnav a","transparent top");
	Nifty("ul#secondarynav a","transparent top");
	Nifty("div.section a","big same-height transparent");
	Nifty("div#preparation", "big transparent");
}

addLoadListener(roundCorners);