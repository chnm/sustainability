AJS={BASE_URL:"",drag_obj:null,drag_elm:null,_drop_zones:[],_cur_pos:null,join:function(_1,_2){
try{
return _2.join(_1);
}
catch(e){
var r=_2[0]||"";
AJS.map(_2,function(_4){
r+=_1+_4;
},1);
return r+"";
}
},getScrollTop:function(){
var t;
if(document.documentElement&&document.documentElement.scrollTop){
t=document.documentElement.scrollTop;
}else{
if(document.body){
t=document.body.scrollTop;
}
}
return t;
},addClass:function(){
var _6=AJS.forceArray(arguments);
var _7=_6.pop();
var _8=function(o){
if(!new RegExp("(^|\\s)"+_7+"(\\s|$)").test(o.className)){
o.className+=(o.className?" ":"")+_7;
}
};
AJS.map(_6,function(_a){
_8(_a);
});
},setStyle:function(){
var _b=AJS.forceArray(arguments);
var _c=_b.pop();
var _d=_b.pop();
AJS.map(_b,function(_e){
_e.style[_d]=AJS.getCssDim(_c);
});
},_getRealScope:function(fn,_10,_11,_12){
var _13=window;
_10=AJS.$A(_10);
if(fn._cscope){
_13=fn._cscope;
}
return function(){
var _14=[];
var i=0;
if(_11){
i=1;
}
AJS.map(arguments,function(arg){
_14.push(arg);
},i);
_14=_14.concat(_10);
if(_12){
_14=_14.reverse();
}
return fn.apply(_13,_14);
};
},preloadImages:function(){
AJS.AEV(window,"load",AJS.$p(function(_17){
AJS.map(_17,function(src){
var pic=new Image();
pic.src=src;
});
},arguments));
},_createDomShortcuts:function(){
var _1a=["ul","li","td","tr","th","tbody","table","input","span","b","a","div","img","button","h1","h2","h3","br","textarea","form","p","select","option","iframe","script","center","dl","dt","dd","small","pre"];
var _1b=function(elm){
var _1d="return AJS.createDOM.apply(null, ['"+elm+"', arguments]);";
var _1e="function() { "+_1d+"    }";
eval("AJS."+elm.toUpperCase()+"="+_1e);
};
AJS.map(_1a,_1b);
AJS.TN=function(_1f){
return document.createTextNode(_1f);
};
},documentInsert:function(elm){
if(typeof (elm)=="string"){
elm=AJS.HTML2DOM(elm);
}
document.write("<span id=\"dummy_holder\"></span>");
AJS.swapDOM(AJS.$("dummy_holder"),elm);
},getWindowSize:function(doc){
doc=doc||document;
var _22,_23;
if(self.innerHeight){
_22=self.innerWidth;
_23=self.innerHeight;
}else{
if(doc.documentElement&&doc.documentElement.clientHeight){
_22=doc.documentElement.clientWidth;
_23=doc.documentElement.clientHeight;
}else{
if(doc.body){
_22=doc.body.clientWidth;
_23=doc.body.clientHeight;
}
}
}
return {"w":_22,"h":_23};
},flattenList:function(_24){
var r=[];
var _26=function(r,l){
AJS.map(l,function(o){
if(o==null){
}else{
if(AJS.isArray(o)){
_26(r,o);
}else{
r.push(o);
}
}
});
};
_26(r,_24);
return r;
},removeElement:function(){
var _2a=AJS.forceArray(arguments);
AJS.map(_2a,function(elm){
AJS.swapDOM(elm,null);
});
},_unloadListeners:function(){
if(AJS.listeners){
AJS.map(AJS.listeners,function(elm,_2d,fn){
AJS.REV(elm,_2d,fn);
});
}
AJS.listeners=[];
},partial:function(fn){
var _30=AJS.forceArray(arguments);
return AJS.$b(fn,null,_30.slice(1,_30.length).reverse(),false,true);
},getIndex:function(elm,_32,_33){
for(var i=0;i<_32.length;i++){
if(_33&&_33(_32[i])||elm==_32[i]){
return i;
}
}
return -1;
},isDefined:function(o){
return (o!="undefined"&&o!=null);
},isArray:function(obj){
return obj instanceof Array;
},setLeft:function(){
var _37=AJS.forceArray(arguments);
_37.splice(_37.length-1,0,"left");
AJS.setStyle.apply(null,_37);
},appendChildNodes:function(elm){
if(arguments.length>=2){
AJS.map(arguments,function(n){
if(AJS.isString(n)){
n=AJS.TN(n);
}
if(AJS.isDefined(n)){
elm.appendChild(n);
}
},1);
}
return elm;
},isOpera:function(){
return (navigator.userAgent.toLowerCase().indexOf("opera")!=-1);
},isString:function(obj){
return (typeof obj=="string");
},hideElement:function(elm){
var _3c=AJS.forceArray(arguments);
AJS.map(_3c,function(elm){
elm.style.display="none";
});
},setOpacity:function(elm,p){
elm.style.opacity=p;
elm.style.filter="alpha(opacity="+p*100+")";
},setHeight:function(){
var _40=AJS.forceArray(arguments);
_40.splice(_40.length-1,0,"height");
AJS.setStyle.apply(null,_40);
},setWidth:function(){
var _41=AJS.forceArray(arguments);
_41.splice(_41.length-1,0,"width");
AJS.setStyle.apply(null,_41);
},createArray:function(v){
if(AJS.isArray(v)&&!AJS.isString(v)){
return v;
}else{
if(!v){
return [];
}else{
return [v];
}
}
},isDict:function(o){
var _44=String(o);
return _44.indexOf(" Object")!=-1;
},isMozilla:function(){
return (navigator.userAgent.toLowerCase().indexOf("gecko")!=-1&&navigator.productSub>=20030210);
},_listenOnce:function(elm,_46,fn){
var _48=function(){
AJS.removeEventListener(elm,_46,_48);
fn(arguments);
};
return _48;
},createDOM:function(_49,_4a){
var i=0,_4c;
elm=document.createElement(_49);
if(AJS.isDict(_4a[i])){
for(k in _4a[0]){
_4c=_4a[0][k];
if(k=="style"){
elm.style.cssText=_4c;
}else{
if(k=="class"||k=="className"){
elm.className=_4c;
}else{
elm.setAttribute(k,_4c);
}
}
}
i++;
}
if(_4a[0]==null){
i=1;
}
AJS.map(_4a,function(n){
if(n){
if(AJS.isString(n)||AJS.isNumber(n)){
n=AJS.TN(n);
}
elm.appendChild(n);
}
},i);
return elm;
},setTop:function(){
var _4e=AJS.forceArray(arguments);
_4e.splice(_4e.length-1,0,"top");
AJS.setStyle.apply(null,_4e);
},getElementsByTagAndClassName:function(_4f,_50,_51){
var _52=[];
if(!AJS.isDefined(_51)){
_51=document;
}
if(!AJS.isDefined(_4f)){
_4f="*";
}
var els=_51.getElementsByTagName(_4f);
var _54=els.length;
var _55=new RegExp("(^|\\s)"+_50+"(\\s|$)");
for(i=0,j=0;i<_54;i++){
if(_55.test(els[i].className)||_50==null){
_52[j]=els[i];
j++;
}
}
return _52;
},bindMethods:function(_56){
for(var k in _56){
var _58=_56[k];
if(typeof (_58)=="function"){
_56[k]=AJS.$b(_58,_56);
}
}
},addEventListener:function(elm,_5a,fn,_5c,_5d){
if(!_5d){
_5d=false;
}
var _5e=AJS.$A(elm);
AJS.map(_5e,function(_5f){
if(_5c){
fn=AJS._listenOnce(_5f,_5a,fn);
}
if(AJS.isIn(_5a,["submit","load","scroll","resize"])){
var old=elm["on"+_5a];
elm["on"+_5a]=function(){
if(old){
fn(arguments);
return old(arguments);
}else{
return fn(arguments);
}
};
return;
}
if(AJS.isIn(_5a,["keypress","keydown","keyup"])){
var _61=fn;
fn=function(e){
e.key=e.keyCode?e.keyCode:e.charCode;
switch(e.key){
case 63232:
e.key=38;
break;
case 63233:
e.key=40;
break;
case 63235:
e.key=39;
break;
case 63234:
e.key=37;
break;
}
return _61.apply(null,arguments);
};
}
if(_5f.attachEvent){
_5f.attachEvent("on"+_5a,fn);
}else{
if(_5f.addEventListener){
_5f.addEventListener(_5a,fn,_5d);
}
}
AJS.listeners=AJS.$A(AJS.listeners);
AJS.listeners.push([_5f,_5a,fn]);
});
},isNumber:function(obj){
return (typeof obj=="number");
},map:function(_64,fn,_66,_67){
var i=0,l=_64.length;
if(_66){
i=_66;
}
if(_67){
l=_67;
}
for(i;i<l;i++){
fn.apply(null,[_64[i],i]);
}
},removeEventListener:function(elm,_6b,fn,_6d){
if(!_6d){
_6d=false;
}
if(elm.removeEventListener){
elm.removeEventListener(_6b,fn,_6d);
if(AJS.isOpera()){
elm.removeEventListener(_6b,fn,!_6d);
}
}else{
if(elm.detachEvent){
elm.detachEvent("on"+_6b,fn);
}
}
},getCssDim:function(dim){
if(AJS.isString(dim)){
return dim;
}else{
return dim+"px";
}
},log:function(o){
if(AJS.isMozilla()){
console.log(o);
}else{
var div=AJS.DIV({"style":"color: green"});
AJS.ACN(AJS.getBody(),AJS.setHTML(div,""+o));
}
},setHTML:function(elm,_72){
elm.innerHTML=_72;
return elm;
},bind:function(fn,_74,_75,_76,_77){
fn._cscope=_74;
return AJS._getRealScope(fn,_75,_76,_77);
},forceArray:function(_78){
var r=[];
AJS.map(_78,function(elm){
r.push(elm);
});
return r;
},update:function(l1,l2){
for(var i in l2){
l1[i]=l2[i];
}
return l1;
},getBody:function(){
return AJS.$bytc("body")[0];
},HTML2DOM:function(_7e,_7f){
var d=AJS.DIV();
d.innerHTML=_7e;
if(_7f){
return d.childNodes[0];
}else{
return d;
}
},getElement:function(id){
if(AJS.isString(id)||AJS.isNumber(id)){
return document.getElementById(id);
}else{
return id;
}
},removeClass:function(){
var _82=AJS.forceArray(arguments);
var cls=_82.pop();
var _84=function(o){
o.className=o.className.replace(new RegExp("\\s?"+cls),"");
};
AJS.map(_82,function(elm){
_84(elm);
});
},showElement:function(){
var _87=AJS.forceArray(arguments);
AJS.map(_87,function(elm){
elm.style.display="";
});
},swapDOM:function(_89,src){
_89=AJS.getElement(_89);
var _8b=_89.parentNode;
if(src){
src=AJS.getElement(src);
_8b.replaceChild(src,_89);
}else{
_8b.removeChild(_89);
}
return src;
},isIn:function(elm,_8d){
var i=AJS.getIndex(elm,_8d);
if(i!=-1){
return true;
}else{
return false;
}
}};
AJS.$=AJS.getElement;
AJS.$$=AJS.getElements;
AJS.$f=AJS.getFormElement;
AJS.$p=AJS.partial;
AJS.$b=AJS.bind;
AJS.$A=AJS.createArray;
AJS.DI=AJS.documentInsert;
AJS.ACN=AJS.appendChildNodes;
AJS.RCN=AJS.replaceChildNodes;
AJS.AEV=AJS.addEventListener;
AJS.REV=AJS.removeEventListener;
AJS.$bytc=AJS.getElementsByTagAndClassName;
AJS.addEventListener(window,"unload",AJS._unloadListeners);
AJS._createDomShortcuts();
AJS.Class=function(_8f){
var fn=function(){
if(arguments[0]!="no_init"){
return this.init.apply(this,arguments);
}
};
fn.prototype=_8f;
AJS.update(fn,AJS.Class.prototype);
return fn;
};
AJS.Class.prototype={extend:function(_91){
var _92=new this("no_init");
for(k in _91){
var _93=_92[k];
var cur=_91[k];
if(_93&&_93!=cur&&typeof cur=="function"){
cur=this._parentize(cur,_93);
}
_92[k]=cur;
}
return new AJS.Class(_92);
},implement:function(_95){
AJS.update(this.prototype,_95);
},_parentize:function(cur,_97){
return function(){
this.parent=_97;
return cur.apply(this,arguments);
};
}};
AJS.$=AJS.getElement;
AJS.$$=AJS.getElements;
AJS.$f=AJS.getFormElement;
AJS.$b=AJS.bind;
AJS.$p=AJS.partial;
AJS.$A=AJS.createArray;
AJS.DI=AJS.documentInsert;
AJS.ACN=AJS.appendChildNodes;
AJS.RCN=AJS.replaceChildNodes;
AJS.AEV=AJS.addEventListener;
AJS.REV=AJS.removeEventListener;
AJS.$bytc=AJS.getElementsByTagAndClassName;
AJSDeferred=function(req){
this.callbacks=[];
this.errbacks=[];
this.req=req;
};
AJSDeferred.prototype={excCallbackSeq:function(req,_9a){
var _9b=req.responseText;
while(_9a.length>0){
var fn=_9a.pop();
var _9d=fn(_9b,req);
if(_9d){
_9b=_9d;
}
}
},callback:function(){
this.excCallbackSeq(this.req,this.callbacks);
},errback:function(){
if(this.errbacks.length==0){
alert("Error encountered:\n"+this.req.responseText);
}
this.excCallbackSeq(this.req,this.errbacks);
},addErrback:function(fn){
this.errbacks.unshift(fn);
},addCallback:function(fn){
this.callbacks.unshift(fn);
},addCallbacks:function(fn1,fn2){
this.addCallback(fn1);
this.addErrback(fn2);
},sendReq:function(_a2){
if(AJS.isObject(_a2)){
this.req.send(AJS.queryArguments(_a2));
}else{
if(AJS.isDefined(_a2)){
this.req.send(_a2);
}else{
this.req.send("");
}
}
}};
script_loaded=true;


script_loaded=true;