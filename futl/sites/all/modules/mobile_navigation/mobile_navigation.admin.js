
(function($, document, window) {
	
  Drupal.behaviors.mobile_navigation_admin = {
    attach: function(context) {
      if ($("#mobile-navigation-displays-form").length) {
      	
      	$("#mobile-navigation-displays-form .field_bottom").parent()
      		.css({
      			float: "left",
      			width: "30%"
      		});
      	$("#mobile-navigation-displays-form .field_top").parent()
      		.css({
      			float: "left",
      			width: "70%"
      		});	
      		
      	$("#mobile-navigation-displays-form td, #edit-mobile-navigation-create-new-display").each(function() {
      		if ($(this).find(".field_media_query").length) {
		      	if ($(this).find(".field_media_query").val()) {
		      		$(this).find(".automatic_description").hide();
	      			$(this).find(".field_top").parent().hide();
	      			$(this).find(".field_bottom").parent().hide();
	      			$(this).find(".activate_manual").hide();
		      	} else {
		      		$(this).find(".manual_description").hide();
		      		$(this).find(".field_media_query").parent().hide();
		      		$(this).find(".activate_automatic").hide();	
	      	    }	
      		}
      	});
      	$("#mobile-navigation-displays-form .activate_manual").each(function() {
      		var parent = $(this).parent();
      		$(this).click(function(e) {
      			parent.find(".automatic_description").hide();
      			parent.find(".field_top").parent().hide();
      			parent.find(".field_bottom").parent().hide();
      			$(this).hide();
      			parent.find(".manual_description").show();
      	        parent.find(".field_media_query").parent().show();
      	        parent.find(".activate_automatic").show();
      	        //parent.find(".field_top").val("");
      	        //parent.find(".field_bottom").val("");
      			e.preventDefault();
      		});
      	});
      	$("#mobile-navigation-displays-form .activate_automatic").each(function() {
      		var parent = $(this).parent();
      		$(this).click(function(e) {
      			parent.find(".manual_description").hide();
      			parent.find(".field_media_query").parent().hide();
      			$(this).hide();
      			parent.find(".automatic_description").show();
      			parent.find(".field_top").parent().show();
      			parent.find(".field_bottom").parent().show();
      			parent.find(".activate_manual").show();
      			//parent.find(".field_media_query").val("");
      			e.preventDefault();
      		});
      	});
      	$("#mobile-navigation-displays-form .field_bottom, #mobile-navigation-displays-form .field_top").each(function() {
      		$(this).change(function(e) {
      			var parent = $(this).parent().parent();
      			if ($(this).val()!="") {
      				parent.find(".field_media_query").val('');	
      			}
      		});
      	});
      	$("#mobile-navigation-displays-form .field_media_query").each(function() {
      		$(this).change(function(e) {
      			var parent = $(this).parent().parent();
      			if ($(this).val()!="") {
      				parent.find(".field_bottom").val('');	
      				parent.find(".field_top").val('');
      			}
      		});
      	});
      	
      }
      
      if ($("#mobile-navigation-configuration-form").length) {
    	$('#edit-mobile-navigation-plugin input').change(function() {
    		if($("#edit-mobile-navigation-plugin-accordion").is(':checked')) { 
    			$("#edit-mobile-navigation-accordion-behaviors").show();
    		} else {
    			$("#edit-mobile-navigation-accordion-behaviors").hide();
    		}
    	});
    	$('#edit-mobile-navigation-plugin input').change();
    	$("#button-title-three-bars").click(function(e) {
    		var val = $("#edit-mobile-navigation-button-title").val();
    		$("#edit-mobile-navigation-button-title").val( val + "&#9776;");
    		e.preventDefault();
    	});
    	$("#handler-title-three-bars").click(function(e) {
    		var val = $("#edit-mobile-navigation-handler-title").val();
    		$("#edit-mobile-navigation-handler-title").val( val + "&#9776;");
    		e.preventDefault();
    	});
    	$("#edit-mobile-navigation-use-handler").change(function() {
    		if ($("#edit-mobile-navigation-use-handler").is(':checked')) {
    			$("#edit-mobile-navigation-handler-title-fieldset").show();	
    		} else {
    			$("#edit-mobile-navigation-handler-title-fieldset").hide();	
    		}
    	});
    	$("#edit-mobile-navigation-use-handler").change();
    	$("#edit-mobile-navigation-use-button").change(function() {
    		if ($("#edit-mobile-navigation-use-button").is(':checked')) {
    			$("#edit-mobile-navigation-button-title-fieldset").show();	
    		} else {
    			$("#edit-mobile-navigation-button-title-fieldset").hide();	
    		}
    	});
    	$("#edit-mobile-navigation-use-button").change();
     }
    }
  }
	
})(jQuery, document, window);