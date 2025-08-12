function imagePagination() {
	if(!document.getElementById) return;
	if(!document.createElement) return;
	if(!document.createTextNode) return;
	
	var container = document.getElementById("imagezoom");
	var imageBox = document.getElementById("images");
	if(!document.getElementById("imagezoom")) return;
	if(!document.getElementById("images")) return;
	
	var imageNav = document.createElement("ul");
	imageNav.setAttribute("id","image-nav");
	container.appendChild(imageNav);
	var newImage = document.createElement("img");
	
	images = imageBox.getElementsByTagName("img");
	
	for(var i=0; i<images.length; i++) {
		var length = images.length;
		if (length < 2) return;
		var firstImageSrc = images[0].src;
		images[i].style.display = "none";
		var imageSource = images[i].src;
		var imageListItem = document.createElement("li");
		var imageLink = document.createElement("a");
		imageLink.href = imageSource;
		var imageText = document.createTextNode("Image " + (i+1));
		imageLink.appendChild(imageText);
		imageListItem.appendChild(imageLink);
		imageNav.appendChild(imageListItem);
		
		newImage.src = firstImageSrc;

		imageLink.onclick = function() {
			newImage.src = this.href;
			return false;
		}
	}

	container.appendChild(newImage);
	
	
}

addLoadListener(imagePagination);