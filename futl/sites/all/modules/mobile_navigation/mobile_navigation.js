/**
 * @file
 * Mobile navigation behavior definition.
 *
 * Get fron Drupal the settings specified on mobile navigation administration page
 * and place them in a parameters structures to run the Mobile Menu plugin.
 */

(function($) {
  // Execute mobile-navigation construction with the settings on mobile_navigation.
  Drupal.behaviors.mobile_navigation = {
    attach: function(context) {
      /*********** REMOVE THIS ***********/
      $("body").prepend("<div id='debugInfo'></div>");
      $("#debugInfo").css({
        position : "fixed",
        right : "50px",
        top : "50px"
      });
      /*******************************/
      /******** Move mobile navigation menus to the body directly. *********/
      $("#mobile-navigation-menus").appendTo("body");
      /******** Setting *******/
      var configurations = Drupal.settings.mobile_navigation.configurations,
      	displays = Drupal.settings.mobile_navigation.displays,
       	module_path = Drupal.settings.mobile_navigation.module_path;
      for(menu_display in configurations) {
      	var data = {
       		'configuration': configurations[menu_display],
       		'display_definitions' : displays,
       		'name' : menu_display,
       		'files_path' : module_path + '/js/',
       	};
       	/* The keys of the configurations array is the same classes used for the menus. */
       	$("#" + menu_display + " ul", context).mobile_menu(menu_display, data);
      }
    }
  }
})(jQuery);
