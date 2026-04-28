/**
 * Created by James McCartney on 7/16/2015.
 */

/**
 * @file
 * Provides the Course Tracker Drupal behavior.
 */

/**
 * The Course Tracker Drupal behavior.
 */
(function ($) {
    var base = '/dhcert/'
    Drupal.behaviors.course_tracker = {
        attach: function(context, settings) {


            if($('.statinfo').length){
                $('.statinfo').html('&nbsp;0');

                $.post(base + 'course_tracker/op/getNumModDone/', {
                    uid: Drupal.settings.course_tracker.uid
                }, function(val) {
                    //console.log(val);
                    set_stat_info(val);
                });

                function set_stat_info(num){
                    if(num){
                        num = num - 1;
                        $('.statinfo').html(num);
                    }else{
                        $('.statinfo').html('0');

                    }
                }
            }

            if($('.nextmodule').length){
                $('.nextmodule').html(Drupal.settings.course_tracker.next_page)
            }



			//for the 8 Guys in Treton Module Page
			if(Drupal.settings.currentUser == 203){
				$('.page-node-596 .eightguys .eguysfactblock .eguyfact').show();
			}



        }
    };
})(jQuery);
