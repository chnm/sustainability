

function MM_findObj(n, d) { //v3.0
  var p,i,x;  if(!d) d=document; if((p=n.indexOf("?"))>0&&parent.frames.length) {
    d=parent.frames[n.substring(p+1)].document; n=n.substring(0,p);}
  if(!(x=d[n])&&d.all) x=d.all[n]; for (i=0;!x&&i<d.forms.length;i++) x=d.forms[i][n];
  for(i=0;!x&&d.layers&&i<d.layers.length;i++) x=MM_findObj(n,d.layers[i].document); return x;
}

function tmt_findObj(n){
	var x,t; if((n.indexOf("?"))>0&&parent.frames.length){t=n.split("?");
	x=eval("parent.frames['"+t[1]+"'].document.getElementById('"+t[0]+"')");
	}else{x=document.getElementById(n)}return x;
}

function MM_showHideLayers() { //v3.0A Modified by Al Sparber and Massimo Foti for NN6 Compatibility
  var i,p,v,obj,args=MM_showHideLayers.arguments;if(document.getElementById){
   for (i=0; i<(args.length-2); i+=3){ obj=tmt_findObj(args[i]);v=args[i+2];
   v=(v=='show')?'visible':(v='hide')?'hidden':v;
   if(obj)obj.style.visibility=v;}} else{
  for (i=0; i<(args.length-2); i+=3) if ((obj=MM_findObj(args[i]))!=null) { v=args[i+2];
    if (obj.style) { obj=obj.style; v=(v=='show')?'visible':(v='hide')?'hidden':v; }
    obj.visibility=v; }}
}

function MM_preloadImages() { //v3.0
  var d=document; if(d.images){ if(!d.MM_p) d.MM_p=new Array();
    var i,j=d.MM_p.length,a=MM_preloadImages.arguments; for(i=0; i<a.length; i++)
    if (a[i].indexOf("#")!=0){ d.MM_p[j]=new Image; d.MM_p[j++].src=a[i];}}
}

function MM_swapImgRestore() { //v3.0
  var i,x,a=document.MM_sr; for(i=0;a&&i<a.length&&(x=a[i])&&x.oSrc;i++) x.src=x.oSrc;
}

function MM_swapImage() { //v3.0
  var i,j=0,x,a=MM_swapImage.arguments; document.MM_sr=new Array; for(i=0;i<(a.length-2);i+=3)
   if ((x=MM_findObj(a[i]))!=null){document.MM_sr[j++]=x; if(!x.oSrc) x.oSrc=x.src; x.src=a[i+2];}
}

function Pop(winURL,winName) {
        window.open(winURL,winName,'height=600,width=440,toolbar=0,directories=0,menubar=0,status=0,location=0,scrollbars=1,resizable=1')
}  

function Pop2(winURL,winName) {
        window.open(winURL,winName,'width=720,Height=600,toolbar=yes,location=no,directories=no,status=yes,menubar=no,scrollbars=yes,resizable=yes');
}

var browserWindow;
	function openBrowserWindow(){
		var x=(screen.width-610)/2;
		var y=(screen.height-410)/2-20;
		browserWindow=window.open("./sm_detector.html","browserWin","width=740,height=420,left="+x+",top="+y+",toolbar=no,status=yes,scrollbars=no,resizeable=yes,menubar=no,location=no");
		browserWindow.opener = window;
	}

var windowDoPop

function go(whichURL) {
    windowDoPop=window.open(whichURL[whichURL.selectedIndex].value,'doPop','toolbar=yes,location=no,directories=no,status=yes,menubar=no,scrollbars=yes,resizable=yes,width=720,Height=' + screen.availHeight + '');
}