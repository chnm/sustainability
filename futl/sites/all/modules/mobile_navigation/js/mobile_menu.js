/**
 * @file
 * Mobile_navigation 2.x Library functionality.
 *
 * Author - Christian Galicia
 * Licenses: GPLv2
 */

/*! matchMedia() polyfill - Test a CSS media type/query in JS. Authors & copyright (c) 2012: Scott Jehl, Paul Irish, Nicholas Zakas, David Knight. Dual MIT/BSD license */
window.matchMedia || (window.matchMedia = function() {
  "use strict";
  // For browsers that support matchMedium api such as IE 9 and webkit
  var styleMedia = (window.styleMedia || window.media);
  // For those that don't support matchMedium
  if (!styleMedia) {
    var style       = document.createElement('style'),
        script      = document.getElementsByTagName('script')[0],
        info        = null;
    style.type  = 'text/css';
    style.id    = 'matchmediajs-test';
    script.parentNode.insertBefore(style, script);
    // 'style.currentStyle' is used by IE <= 8 and 'window.getComputedStyle' for all other browsers
    info = ('getComputedStyle' in window) && window.getComputedStyle(style) || style.currentStyle;
    styleMedia = {
      matchMedium: function(media) {
        var text = '@media ' + media + '{ #matchmediajs-test { width: 1px; } }';
        // 'style.styleSheet' is used by IE <= 8 and 'style.textContent' for all other browsers
        if (style.styleSheet) {
          style.styleSheet.cssText = text;
        } else {
          style.textContent = text;
        }
        // Test if media query is true or false
        return info.width === '1px';
      }
    };
  }
  return function(media) {
    return {
      matches: styleMedia.matchMedium(media || 'all'),
      media: media || 'all'
    };
  };
}());

(function($, document, window) {
  /**
   * MOBILE NAVIGATION PLUGINS
   */ 
  /**
   * Basic Plugin
   */
  window.none = function(element) {
    $ = jQuery;
    
    this.element = element;
    this.build = function() {};
    this.reset = function() {};     
  } // End of Basic plugin
  
  /**
   * Accordion Plugin
   */
  window.accordion = function(element) {
    $ = jQuery;  
    this.e = element;
    this.build = function() {
      var e = this.e;
        if (e.data.conf.expand_only_active_trail!=0) {
            e.data.me.find(".item-with-ul:not(.active-trail) ul").hide();
            e.data.me.find(".item-with-ul.active-trail").addClass("active");
        } else {
            e.data.me.find(".item-with-ul ul").hide();
        }
        e.data.me.find(".item-with-ul").unbind('click').click(function(ev) {
            if (e.data.conf.expand_only_active_trail!=0) {
              e.data.me.find(".item-with-ul ul").not($(this).find("ul")).not($(this).parents()).slideUp("fast");
            }
            $(this).find("ul").first().slideToggle(function() {
              e.data.me.find(".item-with-ul").removeClass("active");
              e.data.me.find(".item-with-ul ul").each(function() {
                if ($(this).css("display") != "none") {
                  $(this).parent("li").addClass("active");
                }
              });
            });
            ev.stopPropagation();
        });
        e.data.me.find(".item-with-ul a").unbind('click').click(function(e) {
          e.stopPropagation();
        });
    };
    this.reset = function() {
    	this.e.data.me.find(".item-with-ul ul").hide();
    };
  } // End of accordion plugin
  
  /**
   * slide navigation Plugin
   */
  window.slide_navigation = function(element) {
    this.e = element;
    this.build = function() {
          var e = this.e;
          e.data.me.find(".item-with-ul ul").hide();
          e.data.me.find("ul.mobile-menu-body").addClass("mobile-menu-slide mobile-menu-slide-first")
            .wrap("<div class='mobile-menu-display'></div>")
            .wrap("<div class='slide-menu-clip'></div>");
          e.data.me.find(".mobile-menu-display").css({
            overflow : "hidden"
          });
          function buildNewSub(sub) {
            var no = e.data.me.find("ul.mobile-menu-slide").length, 
              id = "mobile-menu-" + no, 
              mm_w = e.data.me.find(".mobile-menu-inner-wrapper").width();
            var sub = $(sub).clone().removeClass("item-with-ul"),
              ul = $($('<div></div>').html(sub)).html();
            e.data.me.find(".slide-menu-clip").append("<ul class='" + id + " mobile-menu mobile-menu-slide'>" + ul + "</ul>");
            e.data.me.find("." + id + " > li > ul").show();
            e.data.me.find("." + id + " > li > *").first().addClass("return-link");
            e.data.me.find("." + id + " > li > ul").css({
              padding : 0
            });
            
            e.data.me.find(".slide-menu-clip").css({
              width : (100 * (no + 1)) + "%", //(mm_w * (no + 1)),
              float : "left"
            });
            e.data.me.find(".mobile-menu-slide").css({
              width : (100 / (no + 1)) + "%", //mm_w,
              float : "left"
            });
            e.data.me.find(".slide-menu-clip").animate({
              "marginLeft" : -(mm_w * no)
            }, 'normal');
            bindClick(e.data.me.find("." + id));
            e.data.me.find("." + id + " .return-link").unbind('click').click(function(ev) {
              e.data.me.find('.slide-menu-clip').animate({
                "marginLeft" : -(e.data.me.find(".mobile-menu-inner-wrapper").width() * (e.data.me.find(".mobile-menu-slide").length - 2))
              }, 'normal', function() {
                e.data.me.find(".mobile-menu-slide:last").remove();
                var no = e.data.me.find("ul.mobile-menu-slide").length;
                e.data.me.find('.slide-menu-clip').css({
                  width : (100 * no) + "%", // (e.data.me.find(".mobile-menu-inner-wrapper").width() * (e.data.me.find(".mobile-menu-slide").length)),
                  float : "left"
                });
                e.data.me.find(".mobile-menu-slide").css({
                  width : (100 / (no)) + "%", //mm_w,
                });
              });
              
              ev.preventDefault();
              ev.stopPropagation();
            });
          }
          function bindClick(item) {
            $(item).find(".item-with-ul").unbind('click').click(function(ev) {
              buildNewSub(this);
              ev.preventDefault();
              ev.stopPropagation();
            });
            $(item).find("li a").unbind('click').click(function(ev) {
              ev.stopPropagation();
            });
          }
          bindClick("#"+e.data.name);
    };
    this.reset = function() {
    	var e = this.e;
    	e.data.me.find('.slide-menu-clip').animate({
           "marginLeft" : 0
        }, 'normal', function() {
           e.data.me.find(".mobile-menu-slide").not(".mobile-menu-slide-first").remove();
           e.data.me.find('.slide-menu-clip').css({
             width : "100%", //(e.data.me.find(".mobile-menu-inner-wrapper").width() * (e.data.me.find(".mobile-menu-slide").length)),
             float : "left"
           });
           var no = e.data.me.find("ul.mobile-menu-slide").length;
           e.data.me.find(".mobile-menu-slide").css({
             width : (100 / (no)) + "%", //mm_w,
           });
        });
    };
  } // End of slide nav plugin
  // End of mobile navigation plugins

  /**
   * MOBILE NAVIGATION SHOW AND HIDE EFFECTS
   */
  /**
   * MOBILE NAVIGATION EXPAND DOWN
   */
  window.expand_down = function(element) {
    $ = jQuery;
    this.e = element;
    this.build = function() {
      if (this.e.data.conf.use_button) {
        $("#"+this.e.data.name).appendTo(this.e.data.conf.button_container);  
      }
      this.e.data.me.find(".menu-tab-handler").addClass('bottom'); 
    };
    this.hide = function() {
      this.e.data.me.find('.mobile-menu-inner-wrapper').hide();
      this.e.data.collapsed = true;
    };
    this.show = function() {
      this.e.data.me.find('.mobile-menu-inner-wrapper').show('slow');
      this.e.data.collapsed = false;
    };
    this.collapse = function() {
      this.e.data.me.find('.mobile-menu-inner-wrapper').slideUp('slow');
      this.e.data.collapsed = true;
    };
    this.expand = function() {
      this.e.data.me.find('.mobile-menu-inner-wrapper').slideDown('slow');
      this.e.data.collapsed = false;
    };
  } // end of expand_down effect
  
  /**
   * MOBILE NAVIGATION MODAL TOP EFFECT
   */
  window.modal_top = function(element) {
    $ = jQuery;
    this.e = element;
    this.build = function() {
      this.e.data.me.find(".menu-tab-handler").addClass('bottom'); 
    };
    this.hide = function() {
      this.e.data.me.find('.mobile-menu-inner-wrapper').hide();
      this.e.data.collapsed = true;
    };
    this.show = function() {};
    this.collapse = function() {
        this.e.data.me.find('.mobile-menu-inner-wrapper').slideUp('slow');
      this.e.data.collapsed = true;
    };
    this.expand = function() {
      this.e.data.me.find('.mobile-menu-inner-wrapper').slideDown('slow');
      this.e.data.collapsed = false;
    };
  } // end of modal top effect
  
  /**
   * MOBILE NAVIGATION MODAL LEFT EFFECT
   */
  window.modal_left = function(element) {
    $ = jQuery;
    this.e = element;
    this.build = function() {
      this.e.data.me.find(".menu-tab-handler").addClass('right'); 
      this.ww = this.e.data.me.find(".mobile-menu-inner-wrapper").width();
    };
    this.hide = function() {
      this.e.data.me.find(".mobile-menu-outer-wrapper").css({
        left : "-" + this.e.data.conf.menu_width + "%"
      });
      this.e.data.collapsed = true;
    };
    this.show = function() {};
    this.collapse = function() {
        this.e.data.me.find(".mobile-menu-outer-wrapper").animate({
          left : "-" + this.e.data.conf.menu_width + "%"
        }, "fast", function() {});
      this.e.data.collapsed = true;
    };
    this.expand = function() {
      this.e.data.me.find(".mobile-menu-outer-wrapper").animate({
          left : 0
        }, "fast", function() {});
      this.e.data.collapsed = false;
    };
  } // end of modal left effect
  
  /**
   * MOBILE NAVIGATION MODAL RIGHT EFFECT
   */
  window.modal_right = function(element) {
    $ = jQuery;
    this.e = element;
    this.build = function() {
      this.e.data.me.find(".menu-tab-handler").addClass('left'); 
      this.ww = this.e.data.me.find(".mobile-menu-inner-wrapper").width();
    };
    this.hide = function() {
      this.e.data.me.find(".mobile-menu-outer-wrapper").css({
        right : "-" + this.e.data.conf.menu_width + "%"
      });
      this.e.data.collapsed = true;
    };
    this.show = function() {};
    this.collapse = function() {
        this.e.data.me.find(".mobile-menu-outer-wrapper").animate({
          right : "-" + this.e.data.conf.menu_width + "%"
        }, "fast", function() {
          // Animation complete.
        });
        
      this.e.data.collapsed = true;
    };
    this.expand = function() {
      this.e.data.me.find(".mobile-menu-outer-wrapper").animate({
          right : 0
        }, "fast", function() {});
      this.e.data.collapsed = false;
    };
  } // end of modal right effect
  
  /**
   * MOBILE NAVIGATION MODAL BOTTOM EFFECT
   */
  window.modal_bottom = function(element) {
    $ = jQuery;
    this.e = element;
    var hh;
    this.build = function() {
      this.e.data.me.find(".menu-tab-handler").addClass('top');
      hh = this.e.data.me.find(".mobile-menu-inner-wrapper").height(); 
    };
    this.hide = function() {
      this.e.data.me.find(".mobile-menu-outer-wrapper").css({
        bottom : "-" + hh + "px"
      });
      this.e.data.collapsed = true;
    };
    this.show = function() {};
    this.collapse = function() {
      this.e.data.me.find(".mobile-menu-outer-wrapper").animate({
        bottom : "-" + hh + "px"
      }, "fast", function() {});
      this.e.data.collapsed = true;
    };
    this.expand = function() {
      this.e.data.me.find(".mobile-menu-outer-wrapper").animate({
          bottom : 0
        }, "fast", function() {});
      this.e.data.collapsed = false;
    };
  } // end of modal bottom effect
  
  /**
   * MOBILE NAVIGATION DRAWER TOP EFFECT
   */
  window.drawer_top = function(element) {
    $ = jQuery;
    this.e = element;
    this.build = function() {
      this.e.data.me.find(".menu-tab-handler").addClass('bottom'); 
    };
    this.hide = function() {
      this.e.data.me.find('.mobile-menu-inner-wrapper').hide();
      this.e.data.collapsed = true;
    };
    this.show = function() {};
    this.collapse = function() {
      this.e.data.me.find(".mobile-menu-inner-wrapper").slideUp();
      this.e.data.collapsed = true;
    };
    this.expand = function() {
       this.e.data.me.find(".mobile-menu-inner-wrapper").slideDown();
       this.e.data.collapsed = false;
    };
  } // end of drawer top effect
  
  /**
   * MOBILE NAVIGATION DRAWER LEFT EFFECT
   */
  window.drawer_left = function(element) {
    $ = jQuery;
    this.e = element;
    this.build = function() {
      this.e.useContentWrapper();
      this.e.data.me.find(".menu-tab-handler").addClass('right'); 
      this.e.data.me.find(".mobile-menu-inner-wrapper").css({
              minHeight : $(window).height() + "px"
        });
        this.ww = this.e.data.me.find(".mobile-menu-inner-wrapper").width();
    };
    this.hide = function() {
      this.e.data.me.find(".mobile-menu-outer-wrapper").css({
        left : "-" + this.e.data.conf.menu_width + "%"
      });
      $("#mobile_navigation_main_content_wrapper").css({
        left : "0",
        overflow : "",
        height : "",
        position : "",
        width : ""
      });
      this.e.data.collapsed = true;
    };
    this.show = function() {
      $("#mobile_navigation_main_content_wrapper").css({
          overflow : "hidden",
          height : $(window).height() + "px",
          position : "fixed",
          width: "100%",
          left: this.e.data.conf.menu_width + "%"
      });
    },
    this.collapse = function() {
        this.e.data.me.find(".mobile-menu-outer-wrapper").animate({
          left : "-" + this.e.data.conf.menu_width + "%"
        }, "slow", function() {});
        $("#mobile_navigation_main_content_wrapper").animate({
          left : "0"
        }, "slow", function() {
          $(this).css({
            overflow : "",
            height : "",
            position : "",
            width : ""
          })
        });
      this.e.data.collapsed = true;
    };
    this.expand = function() {
       $("#mobile_navigation_main_content_wrapper").css({
          overflow : "hidden",
          height : $(window).height() + "px",
          position : "fixed",
          width: "100%"
       }).animate({
          left : this.e.data.conf.menu_width + "%"
       }, "slow", function() {});
       this.e.data.me.find(".mobile-menu-outer-wrapper").animate({
          left : 0
       }, "slow", function() {});
       this.e.data.collapsed = false;
    };
  } // end of drawer left effect
  
  /**
   * MOBILE NAVIGATION DRAWER RIGHT EFFECT
   */
  window.drawer_right = function(element) {
    $ = jQuery;
    this.e = element;
    this.build = function() {
      this.e.useContentWrapper();
      this.e.data.me.find(".menu-tab-handler").addClass('left'); 
      this.e.data.me.find(".mobile-menu-inner-wrapper").css({
              minHeight : $(window).height() + "px"
        });
        this.ww = this.e.data.me.find(".mobile-menu-inner-wrapper").width();
    };
    this.hide = function() {
      this.e.data.me.find(".mobile-menu-outer-wrapper").css({
          left : "100%",
          width: 0
        });
        this.e.data.me.find(".mobile-menu-inner-wrapper").css({
          display: "none"
        });
        
        $("#mobile_navigation_main_content_wrapper").css({
          left : "0",
          overflow : "",
          height : "",
          position : ""
        });
        
      this.e.data.collapsed = true;
    };
    this.show = function() {
       /*this.e.data.me.find(".mobile-menu-inner-wrapper").show();
       that.e.data.me.find(".mobile-menu-outer-wrapper").show();
       $("#mobile_navigation_main_content_wrapper").css({
          overflow : "hidden",
          height : $(window).height() + "px",
          position : "fixed",
          width: "100%",
          left: (-this.e.data.conf.menu_width) + "%"
       });
       this.e.data.me.find(".mobile-menu-outer-wrapper").css({
         display : "block",
         width : this.e.data.conf.menu_width + "%",
         left: (100-this.e.data.conf.menu_width) + "%",
       });*/
       
       
       this.e.data.me.find(".mobile-menu-inner-wrapper").show();
       $("#mobile_navigation_main_content_wrapper").css({
          overflow : "hidden",
          height : $(window).height() + "px",
          position : "fixed",
          width: "100%",
          left : -this.e.data.conf.menu_width + "%"
       });
       this.e.data.me.find(".mobile-menu-outer-wrapper").show().css({
         display : "block",
         width : this.e.data.conf.menu_width + "%",
         left : (100 - this.e.data.conf.menu_width) + "%"
       });
       this.e.data.collapsed = false;
       
    };
    var e = this.e;
    this.collapse = function() {
        var that = this;
        e.data.me.find(".mobile-menu-outer-wrapper").animate({
          left : "100%"
        }, "slow", function() {
           that.e.data.me.find(".mobile-menu-inner-wrapper").hide();
           that.e.data.me.find(".mobile-menu-outer-wrapper").css({
              width: 0
           });
        });
        $("#mobile_navigation_main_content_wrapper").animate({
          left : "0"
        }, "slow", function() {
          $(this).css({
            overflow : "",
            height : "",
            position : ""
          });
        });
        this.e.data.collapsed = true;
    };
    this.expand = function() {
       this.e.data.me.find(".mobile-menu-inner-wrapper").show();
       $("#mobile_navigation_main_content_wrapper").css({
          overflow : "hidden",
          height : $(window).height() + "px",
          position : "fixed",
          width: "100%"
       }).animate({
          left : -this.e.data.conf.menu_width + "%"
       }, "slow", function() {});
       this.e.data.me.find(".mobile-menu-outer-wrapper").show().css({
         display : "block",
         width : this.e.data.conf.menu_width + "%"
       }).animate({
         left : (100 - this.e.data.conf.menu_width) + "%"
       }, "slow");
       this.e.data.collapsed = false;
    };
    
  } // end of drawer right effect
  // End of mobile navigation show and hide effects
  
  
  var mobile_navigation_instances = {};

  // Main Class
  var mobile_menu = function(elem, options) {
      
    this.methods = {

      /* destroy */
      destroy : function() {

      }, // End of destroy
        
      build : function() {
        $("#mobile-navigation-menus").prependTo("body");
        var show_hide_effect = _this.data.conf.show_hide_effect;
        var classes = _this.data.name + " mobile-menu-outer-wrapper mobile-menu plugin-" + _this.data.conf.plugin + " display-" + _this.data.conf.display + " effect-" + show_hide_effect;
        _this.data.me.wrapInner("<div class='" + classes + "'><div class='mobile-menu-inner-wrapper mobile-menu-inner'></div></div>");
        _this.data.me.find("ul:first").addClass("mobile-menu-body");
        _this.data.me.find("ul").addClass("mobile-menu");
        // Setting configured menu width
        _this.data.me.find(".mobile-menu-outer-wrapper").css("width", (_this.data.conf.menu_width+"%"));
        _this.data.me.find("li").each(function() {
          if ($(this).find("ul").length) {
            $(this).addClass("item-with-ul");
          }
        });
        _this.data.me.find("li.item-with-ul > *:first-child").each(function() {
          if ($(this).get(0).tagName == "A") {
            $(this).wrap("<div></div>");
          }
          $(this).parent().addClass("submenu-title");
        });
        // Add special classes to menu.
        if (_this.data.conf.use_classes) {
          function addClassesToUl(ul, parentClass) {
            var ii = 1;
            $(ul).find("> li").each(function() {
              if (parentClass == "") {
                var cls = "menuitem-" + ii;
              } else {
                var cls = "menuitem-" + parentClass + "-" + ii;
              }
              $(this).addClass(cls);
              if ($(this).hasClass("item-with-ul")) {
                if (parentClass == "") {
                  addClassesToUl($(this).find("> ul"), ii);
                } else {
                  addClassesToUl($(this).find("> ul"), parentClass + "-" + ii);
                }
              }
              ii++;
            });
          }
          addClassesToUl(_this.data.me.find("ul"), "");
        }
        if (_this.data.conf.use_handler!="0") {
          _this.data.me.find( ".mobile-menu-outer-wrapper" )
            .prepend("<a id='" + _this.data.name + "-menu-handler' class='menu-tab-handler " + _this.data.name + "-trigger'>" + _this.data.conf.handler_title + "</a>");
        }
        if (_this.data.conf.use_mask!="0") {
          $("body #mobile-navigation-menus").css({
            position : "relative"
          }).append("<div id='mobile-navigation-" + _this.data.name + "-mask' class='mobile-navigation-mask'></div>");
        }
        if ('ontouchstart' in document.documentElement) {
          $("." + _this.data.name + "-trigger").on('touchstart', function(e) {
            _this.toggle();
            e.stopPropagation();
            e.preventDefault();
          });
        } else {
            $("." + _this.data.name + "-trigger").unbind('click').click(function(e) {
              _this.toggle();
              e.stopPropagation();
              e.preventDefault();
            });
        }
      }, // End of build()
    
      toggle : function() {
        if (_this.data.conf.use_mask) {
          if (_this.data.collapsed) {
            if (_this.data.conf.use_mask!="0") {
              $("#mobile-navigation-" + _this.data.name + "-mask").unbind("click").click(function() {
                _this.toggle();
                }).fadeIn();
            }
          } else {
            if (_this.data.conf.use_mask!="0") {
              $("#mobile-navigation-" + _this.data.name + "-mask").unbind("click").fadeOut();
            }
          }
        }
        if (_this.data.collapsed) {
          _this.data.effect.expand();
        } else {
          _this.data.plugin.reset();
          _this.data.effect.collapse();    
        }
      }, // End of toggle()
    
      applyNavigationPlugin : function() {
        var plugin = _this.data.conf.plugin;
        _this.data.plugin = new window[plugin](_this);
        _this.data.plugin.build();
      }, // End of applyNavigationPlugin()
    
      applyShowAndHideEffect : function() {
        var effect = _this.data.conf.show_hide_effect;
        _this.data.effect = new window[effect](_this);
        _this.data.effect.build();
        if (_this.data.conf.collapse_by_default!="0") {
          _this.data.effect.hide();  
        } else {
          if (_this.data.conf.use_mask!="0") {
            $("#mobile-navigation-" + _this.data.name + "-mask").unbind("click").click(function() {
              _this.toggle();
            }).fadeIn();
          }
          _this.data.effect.show();
        }
      }, // End of applyShowAndHideEffect()
    
      useContentWrapper : function() {
        if (!$("#mobile_navigation_main_content_wrapper").length) {
          $("body").wrapInner("<div id='mobile_navigation_main_content_wrapper'></div>");
          $("#mobile-navigation-menus").prependTo("body");
        }
      }, // end of useContentWrapper()
      
      // Verify if a query is valid for current browser width.
      checkQuery : function(query) {
        return window.matchMedia(query).matches;
      }, // End of checkQuery
      
      isCurrentDisplay : function() {
        
        var mediaQuery = _this.data.display_definitions[_this.data.conf.display]
        
        if (_this.checkQuery(mediaQuery)) {
        	return true;
        }
        return false;
        /*
        var displays = _this.data.display_definitions,
            display;
        for (display in displays) {
          var mediaQuery = displays[display];
          if (_this.checkQuery(mediaQuery)) {
            break;
          }
        }
        
        return display;*/
      }, // End of currentDisplay
      getCurrentDisplays : function() {
        
        var display_list = _this.data.display_definitions,
            current_displays = [];
        for (display in display_list) {
          var mediaQuery = display_list[display];
          if (_this.checkQuery(mediaQuery)) {
            current_displays.push(display);
          }
        }
        
        return current_displays;
      }, // End of currentDisplay
      
        
      enable : function() {
        _this.data.me.show();
        
        $("#" + _this.data.name + "-button").show()
        $(_this.data.conf.menu_selector).hide();
      }, // End of hide()
        
      disable : function() {
      	if (_this.data.effect!=null) {
	      	_this.data.effect.hide();
	      	_this.data.plugin.reset();
	      	
	      	if (_this.data.conf.use_mask!="0") {
	          $("#mobile-navigation-" + _this.data.name + "-mask").unbind("click").hide();
	        }
	            
	        _this.data.me.hide();
	        $("#" + _this.data.name + "-button").hide();
	        $(_this.data.conf.menu_selector).show();
	    }
      }, // End of disable()
        
      /* Display is detected using the checkQuery function wich uses matchMedia. 
      * Display list is iterated and tested on the resize method to find the current 
      * and apply corresponding configuration if there is any for that display.*/
      onResize : function() {
        var conf = _this.data.conf;
        
        /* Get Current displays */
        currentDisplays = _this.getCurrentDisplays();
        
        /** DEBUG INFO *****************************/
        
        var displays_string = "";
        for(disp in currentDisplays) {
        	if (displays_string!="") {
        		displays_string = displays_string + ",";
        	}
        	displays_string = displays_string + currentDisplays[disp]; 
        }
        
        $("#debugInfo").html($(window).width() + " - " + displays_string);
        /*******************************/
        
        if (currentDisplays.indexOf(_this.data.prevDisplay)) { //  !=currentDisplay) {
          if (_this.isCurrentDisplay()) {
            if (!_this.data.done) {
              _this.build(); 
              _this.applyNavigationPlugin();
              _this.applyShowAndHideEffect();        
              _this.data.done = true;
            }
            _this.enable();        
          } else {
            _this.disable();
          }

        }
      }, // End of onResize
      // INIT
      init : function(elem, opts) {
        _this.data = {};
        _this.data.target = elem;
        _this.data.name = opts['name'];
        _this.data.files_path = opts['files_path']; 
        _this.data.configuration = _this.data.conf = opts['configuration'];
        _this.data.display_definitions = opts['display_definitions'];
        _this.data.me = $("#"+_this.data.name);
        _this.data.done = false;
        _this.data.prevDisplay = "";
        _this.data.effect = null;
        // bind to the window resize method.
        $(window).resize(_this.onResize);
        // call resize method
        _this.onResize();
      } // end of init
    };
      // end of methods
      var _this = this.methods;
  };
    // end of mobile_menu class

    // $.FN
    $.fn.mobile_menu = function(name, opts) {
      if (!(!$.support.leadingWhitespace)) {
        //Not IE7 nor IE8.
        if (mobile_navigation_instances[name] === undefined) {
          mobile_navigation_instances[name] = new mobile_menu(this, opts);
          return mobile_navigation_instances[name].methods.init(this, opts);
        } else if (mobile_navigation_instances[name]) {
          return mobile_navigation_instances[name].methods;
        } else {
          return $(this);
        }
      }
    };
    // end of $.fn.mobile_menu

})(jQuery, document, window);
