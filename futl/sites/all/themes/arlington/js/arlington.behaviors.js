(function ($) {

    /**
     * The recommended way for producing HTML markup through JavaScript is to write
     * theming functions. These are similiar to the theming functions that you might
     * know from 'phptemplate' (the default PHP templating engine used by most
     * Drupal themes including Omega). JavaScript theme functions accept arguments
     * and can be overriden by sub-themes.
     *
     * In most cases, there is no good reason to NOT wrap your markup producing
     * JavaScript in a theme function.
     */
    Drupal.theme.prototype.arlingtonExampleButton = function (path, title) {
        // Create an anchor element with jQuery.
        return $('<a href="' + path + '" title="' + title + '">' + title + '</a>');
    };

    /**
     * Behaviors are Drupal's way of applying JavaScript to a page. In short, the
     * advantage of Behaviors over a simple 'document.ready()' lies in how it
     * interacts with content loaded through Ajax. Opposed to the
     * 'document.ready()' event which is only fired once when the page is
     * initially loaded, behaviors get re-executed whenever something is added to
     * the page through Ajax.
     *
     * You can attach as many behaviors as you wish. In fact, instead of overloading
     * a single behavior with multiple, completely unrelated tasks you should create
     * a separate behavior for every separate task.
     *
     * In most cases, there is no good reason to NOT wrap your JavaScript code in a
     * behavior.
     *
     * @param context
     *   The context for which the behavior is being executed. This is either the
     *   full page or a piece of HTML that was just added through Ajax.
     * @param settings
     *   An array of settings (added through drupal_add_js()). Instead of accessing
     *   Drupal.settings directly you should use this because of potential
     *   modifications made by the Ajax callback that also produced 'context'.
     */
    Drupal.behaviors.arlingtonExampleBehavior = {
        attach: function (context, settings) {
            // By using the 'context' variable we make sure that our code only runs on
            // the relevant HTML. Furthermore, by using jQuery.once() we make sure that
            // we don't run the same piece of code for an HTML snippet that we already
            // processed previously. By using .once('foo') all processed elements will
            // get tagged with a 'foo-processed' class, causing all future invocations
            // of this behavior to ignore them.
            $('.some-selector', context).once('foo', function () {
                // Now, we are invoking the previously declared theme function using two
                // settings as arguments.
                var $anchor = Drupal.theme('arlingtonExampleButton', settings.myExampleLinkPath, settings.myExampleLinkTitle);

                // The anchor is then appended to the current element.
                $anchor.appendTo(this);
            });

            //log in
            if( $('.not-logged-in').length) {
                $('#user-login #edit-submit, #user-login--2 #edit-submit--2').attr('value', 'Enter');
                $("#user-login #edit-name, #user-login--2 #edit-name--2").attr("placeholder", "Username").val("");
                $("#user-login #edit-pass, #user-login--2 #edit-pass--2").attr("placeholder", "Password").val("");

                //
            }

            //Home page
            if( $('.front').length) {
                $('.boxwrap').click(function () {
                    $(this).siblings('.popupme').show();
                    $('.teachwrap').css('z-index', '0');
                    $('.rightside').css('z-index', '0');
                });
                $('.popupme').click(function () {
                    $(this).hide();
                    $('.teachwrap').css('z-index', '1');
                    $('.rightside').css('z-index', '1');
                });
            }

            //If user is not logged in, prevent guests from typing
            if( $('.not-logged-in').length) {
                if( $('textarea').length) {
                    $('textarea').attr('disabled','disabled');
                }
                if( $('.webform-submit').length) {
                    $('.webform-submit').attr('disabled','disabled');
                    $('.webform-submit').css('background-color', '#a4abb1');
                }
            }

            //If guest account, change the "Home" button
            if( $('body.role-guest').length) {
                $('.breadcrumb li:first').html('<a href="/module-preview">Module</a>');
            }

            //Remove "home" from breadcrumb title
            if( $('.breadcrumb li:first').text() == 'Home') {
                $('.breadcrumb li:first').hide()
            }

            //If an Accordion
            if( $('.accordion').length) {
                $('.atitle').click(function () {
                    if($(this).hasClass('selected')) {
                        $(this).removeClass('selected');
                    }
                    else {
                        $(this).addClass("selected");
                    }
                    $(this).siblings().toggle("selected");
                });
            }

            //Hypothesis Pages
            if( $('.node-type-hypothesis').length) {
                if($('.webform').length == 1){
                    $('.hidden').css('display', 'inline-block');
                }
            }

            //Look Closer Pages
            if( $('.node-type-look-closer').length) {
                //Start with the first children selected
                //$('.clues .cluewrap:first-child').addClass('selected');
                $(".buttonholder .button").css('background-color', '#adb6bf');

                //Hold the IDs of the magnifying glasses
                var $indexholder = [];
                $indexholder.push( $('.srcimg .glass.selected').attr('id') );
                var $numglass = $('.srcimg .glass').length;
                //console.log($indexholder.length);
                //console.log($numglass);

                ////When you click, turn the small circle red and turn on the corresponding clue at the side
                $('.srcimg .glass').click(function() {
                    var $check = $(this).attr('id'); //get the id of the current one
                    if ($.inArray($check, $indexholder) == -1 ){ //if not in the array, put it in
                        $indexholder.push($check);
                        //console.log($indexholder.length);
                    }

                    $('.srcimg .selected').addClass('visited');

                    $('.srcimg .glass').removeClass('selected');
                    $('.clues .cluewrap').removeClass('selected');

                    var $index = $(this).index()+1;
                    //console.log($index);
                    $('.srcimg .glass:nth-child('+$index+')').addClass('selected');
                    $('.clues .cluewrap:nth-child('+$index+')').addClass('selected');

                    //Compare the number of the magnifying glasses to how many elements are in the array
                    if( $numglass == $indexholder.length) {
                        $(".buttonholder .button").removeClass('disable');
                        $(".buttonholder .button").css('background-color', '#007A8F');
                    }

                });
            }
            //Special case LookCloser pages
            if( $('.node-type-look-closer.page-node-623').length) {
                $(".buttonholder .button").css('background-color', '#007A8F');
                $('.clues .cluewrap').addClass('selected');

            }
            if( $('.node-type-look-closer.page-node-605').length) {
                $(".nextpart").hide();
            }

            //Resource Pages
            if( $('.node-type-resource').length) {
                $('.toright').wrapAll('<div class="rightme"></div>');
                if ($('.webform').length == 1) {
                    $('.hidden').css('display', 'block');
                }

                //Setting up for the first load
                $('.view-resource-image .views-field-field-source-1 li').addClass('myfuture');
                $('.view-resource-image .views-field-field-source-1 li:first-child').removeClass('myfuture');
                $('.view-resource-image .views-field-field-source-1 li:first-child').addClass('myself');
                $('.views-field-field-html5-video .lightbox-processed:first-child').addClass('myself');
                $('.views-field-field-citation- p:first-child').addClass('myself');
                $('.views-field-field-transcription .accordion:first-child').addClass('myself');
                $('.views-field-field-transcription .accordion .hidden').each(function () { //for each labeled "Hidden"
                    $(this).parent().parent().addClass('hideme');
                });

                if( $('.view-resource-image .views-field-field-source-1 li').length < 2){
                    $('.view-resource-image .views-field-field-source-1 li').hide();
                }

                else {
                    //Now. For switching the indexes around.
                    $('.view-resource-image .views-field-field-source-1 li').click(function () {
                        var index = $(this).index();
                        $('.view-resource-image .views-field-field-source-1 li').removeClass('myself myfuture mypast');
                        $('.views-field-field-html5-video .lightbox-processed').removeClass('myself myfuture mypast');
                        $('.views-field-field-transcription .accordion').removeClass('myself myfuture mypast');
                        $('.views-field-field-citation- p').removeClass('myself myfuture mypast');

                        $(this).addClass('myself');
                        $(this).prevAll().addClass('mypast');
                        $(this).nextAll().addClass('myfuture');
                        $('.views-field-field-html5-video .lightbox-processed').eq(index).addClass('myself');
                        $('.views-field-field-transcription .accordion').eq(index).addClass('myself');
                        $('.views-field-field-citation- p').eq(index).addClass('myself');

                    });

                }
            }

            //Rethink Page
            if( $('.node-type-rethink').length) {
                $('.halfme #aimforme').html( $('.moveme').detach() );


                $('.grayme .views-label').each(function() { //for each hypothesis
                    $(this).html($(this).html().replace(":", ""));
                });

                if($('.webform').length == 1){
                    $('.hidden').css('display', 'block');
                }
            }

            //In Action Pages
            if( $('.node-type-in-action').length) {
                $('.instclick').click(function() {
                    $(this).siblings('.sniplet').hide();
                    $(this).siblings('.wholetxt').show();
                    $(this).hide();
                    $(this).siblings('.instclick2').css('display','inline-block');
                });
                $('.instclick2').click(function() {
                    $(this).siblings('.sniplet').show();
                    $(this).siblings('.wholetxt').hide();
                    $(this).hide();
                    $(this).siblings('.instclick').css('display','inline-block');
                });

                $('.srccircle img').click(function() {
                    $(this).parent().siblings('.lightboxme.hideme').removeClass('hideme');

                    //In the Source listing, make sure to just print 1 citation with 1 image?
                    var indexer = $(this).index();
                    var index = indexer;
                    //  console.log(indexer);
                    $('.view-resource-multi-sources li').hide();
                    $(this).parent().siblings('.lightboxme').find('.view-resource-multi-sources li').eq(indexer).show();
                    $('.srcwriting p').hide();
                    $(this).parent().siblings('.lightboxme').find('.srcwriting p').eq(index).show();

                });

                $('.exitleft').click(function() {
                    $('.lightboxme').addClass('hideme');
                });

                $('#target').html( $('.moveme').detach() );

                $('.bothalf .matchme').matchHeight();

                //Disable upload button
                $(".webform .form-managed-file #edit-submitted-file-upload-button").prop('disabled', true);
                $(".webform .form-managed-file #edit-submitted-file-upload-button").css('background-color', '#adb6bf');

                //Enable upload button once file has been selected
                $('.webform .form-file').click(function() {
                    $(".webform .form-managed-file #edit-submitted-file-upload-button").prop('disabled', false);
                    $(".webform .form-managed-file #edit-submitted-file-upload-button").css('background-color', '#95002f');

                });

            }

            //Teacher Dashboard Page
            if( $('.page-node-99').length) {

                var vars = getUrlVars();
                if(vars!=null) {
                    var theGroup = vars['module'];
                    $('#'+theGroup).removeClass('selected');
                    $('#'+theGroup).siblings().toggle("selected");
                }


                $('.modviewer .view').each(function() { //For every module in class
                    $(this).find('.views-row').each(function() { //for every module listed
                        var $title2comp = $(this).find('.title span').text(); //Get the title of the module
                        var $title2comp2 = $(this).find('.views-field-title .field-content').text(); //Get the title of the module
                        var $storethepic;
                        $('.modulepic .views-row').each(function() { //for each module on the site
                            if($title2comp == $(this).find('.checktitle').text() ){
                                $storethepic = $(this).find('.movesrc').html();
                            }
                            else if($title2comp2 == $(this).find('.checktitle').text() ){
                                $storethepic = $(this).find('.movesrc').html();
                            }
                        });

                        $(this).prepend($storethepic);
                    });
                });

                $('.studmod .view').each(function() { //For every class
                    $(this).find('.views-row').each(function() { //for every module listed
                        var $title2comp = $(this).find('.views-field-title .visited').text(); //Get the title of the module
                        var $storethepic;
                        $('.modulepic .views-row').each(function() { //for each module on the site
                            if($title2comp == $(this).find('.checktitle').text() ){
                                $storethepic = $(this).find('.movesrc').html();
                            }
                        });
                        $(this).prepend($storethepic);

                        var $teachcomment;
                        $('.view-student-view-of-the-teacher-comments .views-row .views-field').each(function() { //for each module on the site
                            console.log( $(this).find('.views-label').text() );
                            if($title2comp == $(this).find('.views-label').text() ){
                                $teachcomment = $(this).find('.views-field-value .field-content').html();
                            }
                        });
                        $(this).append($teachcomment);

                        //Now if you see a .visited.current, throw flag
                        if( $(this).find('.views-field-title .visited.current').length) {
                            var $href = $(this).find('.views-field-title .visited.current').attr('href');
                            // console.log($href);
                            $(this).find('.views-field-php').show();
                            $(this).append('<a href="'+$href+'" class="contbutton">Continue</a>');
                        }
                        else if($(this).find('.views-field-title .visited.complete').length ){
                            $(this).find('.views-field-php').show();
                            $(this).find('.views-field-php').prepend('<span class="endflag">Submitted: </span>');
                        }
                        else if($(this).find('.views-field-title .visited').length ){
                            var $href = $(this).find('.views-field-title .visited').attr('href');
                            //console.log($href);
                            $(this).find('.views-field-php').hide();
                            $(this).append('<a href="'+$href+'" class="startbutton">Start</a>');
                        }
                    });
                });
            }

            //Student Submission Page
            if( $('.page-content-studentwork').length) {
                $('.accordion .inaction').each(function() { //for each In Action aka completed module
                    if( $(this).find('.view').length) { } //If there's a view, then ignore it
                    else{ //otherwise, erase it.
                        $(this).parents('.accordion').hide();
                    }
                });

                $('.acont .views-label').each(function() { //for each hypothesis
                    $(this).html($(this).html().replace(":", ""));
                });

                $('.seghistory #target').html( $('.seghis').detach() );
                $('.seggovt #target').html( $('.seggov').detach() );
                $('.lchistory #target').html( $('.lchis').detach() );
                $('.lcgovt #target').html( $('.lcgov').detach() );
                $('.mrhistory #target').html( $('.mrhis').detach() );
                $('.mrgovt #target').html( $('.mrgov').detach() );
                $('.arlhistory #target').html( $('.arhis').detach() );
                $('.arlgovt #target').html( $('.argov').detach() );
                $('.saddis #target').html( $('.sadterdis').detach() );
                $('.fightside #target').html( $('.fightsidebside').detach() );
                $('.inservice #target').html( $('.inservicecont').detach() );
                $('.inspirit #target').html( $('.inspiritfrat').detach() );
                $('.rosie #target').html( $('.beforerosie').detach() );


                $('.webform .webform-component--user-id').each(function() { //for each User ID Field, fill it with the url
                    var $result = window.location.href.substring(window.location.href.lastIndexOf('/') + 1);
                    $result = $result.replace('#', '');
                    console.log($result);
                    $(this).find('.form-text').val($result);
                });
            }

            //For the Book navigation options
            if( $('.pane-node-book-nav .book-navigation__links').length) {
                $('.book-navigation__previous').text("‹ Back");
                $('.book-navigation__next').text("Next ›");
            }

            //Account Registeration Page fix-its
            if( $('.page-user-register').length) {
                $('.titlewrap h1').text('Teacher Registration');
                $('.pane-page-content').prepend('<div class="introtext"><p>Welcome to For Us The Living!</p><p>Registration is easy and quick. Just complete this form to create a FREE teacher account!</p></div>');
            }
			
			//Forgot Password Page
			if( $('.page-user-password').length) {
				$('.pane-page-content').prepend('<div class="instructions"><p><strong>Students</strong><br/>Please contact your teacher to reset your password.</p><p><strong>Teachers</strong><br/>Enter your username or email address to reset your password.</p></div>');
			}


        }
    };

    function getUrlVars() {
        var vars = {};
        var parts = window.location.href.replace(/[?&]+([^=&]+)=([^&]*)/gi, function(m,key,value) {
            vars[key] = value;
        });
        return vars;
    }

})(jQuery);
