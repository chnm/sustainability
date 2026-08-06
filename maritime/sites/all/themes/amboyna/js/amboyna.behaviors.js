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
    Drupal.theme.prototype.amboynaExampleButton = function (path, title) {
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
    Drupal.behaviors.amboynaExampleBehavior = {
        attach: function (context, settings) {

            //Stop "Exhibit" from redirecting to homepage
//            $('.l-header ul.menu li.first a').removeAttr("href");

            //Add accordion
            $( ".accordion" ).accordion({
                active: 0,
                collapsible: true,
                icons: { "header": "\tui-icon-circle-triangle-e", "activeHeader": "\tui-icon-circle-triangle-s" }
            });

            //Add Tabs
            $( ".tabs" ).tabs();

            //Accessibility helper: trap Tab within a dialog and close it on Escape.
            function makeDialogAccessible($dialog, closeFn) {
                $dialog.on('keydown.a11ydialog', function(e) {
                    if (e.key === 'Escape' || e.keyCode === 27) {
                        e.preventDefault();
                        closeFn();
                        return;
                    }
                    if (e.key === 'Tab' || e.keyCode === 9) {
                        var $focusable = $dialog.find('button, [href], iframe, input, select, textarea, [tabindex]:not([tabindex="-1"])').filter(':visible');
                        if (!$focusable.length) { return; }
                        var first = $focusable.get(0);
                        var last = $focusable.get($focusable.length - 1);
                        if (e.shiftKey && document.activeElement === first) {
                            e.preventDefault();
                            last.focus();
                        } else if (!e.shiftKey && document.activeElement === last) {
                            e.preventDefault();
                            first.focus();
                        }
                    }
                });
            }

            //For homepage
            if( $('.front').length) {
                var $videoDialog = $('.videofunsies');
                var $videoTrigger = $('.homevid .button');

                function closeVideoDialog() {
                    //Stop playback by reloading the iframe rather than the src
                    var $iframe = $videoDialog.find('.vidpopup iframe');
                    $iframe.attr('src', $iframe.attr('src'));
                    $videoDialog.hide();
                    $videoDialog.off('keydown.a11ydialog');
                    $videoTrigger.trigger('focus');
                }

                makeDialogAccessible($videoDialog, closeVideoDialog);

                //Pull up the pop up
                $videoTrigger.click(function() {
                    $videoDialog.show();
                    $videoDialog.find('.exitbutt').trigger('focus');
                });

                //Exit out of the pop up
                $( ".videofunsies .exitbutt, .videofunsies .overlay" ).click(function() {
                    closeVideoDialog();
                });
            }

            //For Exhibits
            if( $('.node-type-exhibits').length) {
                //if there's an empty accordion, then hide it
                $( ".ui-accordion-header" ).each(function() {
                    // console.log($(this).text());
                    if( !$(this).text().length ){
                        $(this).hide();
                        // console.log( "Hide me" );
                    }
                });

                //If there isn't a yt to display (aka all but Trade in Deerskin)
                if( ! $('.pop.ytvid iframe').length) {
                    $('.introdetail').css('width','100%');
                    $('.ytvid.button').hide();
                }

                $('.pop.ytvid').hide();

                var $sourceDialog = $('.popupwrap');
                var $lastSourceTrigger = null;

                function closeSourceDialog() {
                    $('.popupfun').hide();
                    $('.pop .srcholder').hide();
                    $('.archivelink').remove();

                    //if we're ytvid, we need to get fancy
                    var $holdhtml =  $('.pop.ytvid').html();
                    $('.pop.ytvid').hide();
                    $('.pop.ytvid').html($holdhtml);

                    $sourceDialog.off('keydown.a11ydialog');
                    if ($lastSourceTrigger) {
                        $lastSourceTrigger.trigger('focus');
                        $lastSourceTrigger = null;
                    }
                }

                makeDialogAccessible($sourceDialog, closeSourceDialog);

                //On yt button click, open popup
                $( ".ytvid.button" ).click(function() {
                    $lastSourceTrigger = $(this);
                    $('.popupfun').show();
                    $('.pop.ytvid').show();
                    $sourceDialog.find('.exitbutt').trigger('focus');
                });

                //Make each source card keyboard-operable (mouse clicks already bubble up to
                //the .accontent article handler below, from whichever element is clicked).
                //A card's excerpt text can occasionally contain a real link (e.g. "View the
                //Zheng Organization Graphic" on the Zheng Description card) - putting
                //role="button" around that would nest an interactive link inside another
                //interactive control, which is invalid. So: if the excerpt has a link, only
                //the thumbnail image (which never contains a link) becomes the keyboard
                //trigger; otherwise the whole excerpt area does.
                $( ".accontent article" ).each(function() {
                    var $article = $(this);
                    var $content = $article.find('.node__content');
                    var hasNestedLink = $content.find('a[href]').length > 0;
                    var $trigger = hasNestedLink ? $content.find('.field--name-field-source-thumbnail') : $content;
                    var title = $article.find('.node__title').text().trim();

                    $trigger.addClass('card-trigger').attr({
                        'tabindex': '0',
                        'role': 'button',
                        'aria-label': 'Preview source: ' + title
                    }).on('keydown', function(e) {
                        if (e.key === 'Enter' || e.key === ' ' || e.keyCode === 13 || e.keyCode === 32) {
                            e.preventDefault();
                            $(this).trigger('click');
                        }
                    });
                });

                //Clicking on a source
                $( ".accontent article" ).click(function(e) {
                    $lastSourceTrigger = $(e.target).closest('.card-trigger');
                    if (!$lastSourceTrigger.length) { $lastSourceTrigger = $(this); }

                    var $indexofsrc = $(this).index() + 1;
                    var $indexofsection = $(this).parent().parent().index()/2 + 0.5;

                    $('.popupfun').show();
                    $('.pop.sec'+$indexofsection+' .srcholder.src'+$indexofsrc).show();

                    // console.log( $(this).find('.node__links a') );
                    //Make me a "View in Archive" Link
                    var $htmlhold = $(this).find('.node__links a').attr("href");
                    $('.pop.sec'+$indexofsection).before('<a target="_blank" class="archivelink" href="'+$htmlhold+'">View in Archive</a>');

                    $sourceDialog.find('.exitbutt').trigger('focus');
                });

                //Exit out of the pop up
                $( ".popupfun .exitbutt, .popupfun .overlay" ).click(function() {
                    closeSourceDialog();
                });

            }

            //For Key Actors Landing Page
            if( $('.page-node-6').length) {
                //Format to be turned into accordion
                $('.view-people-landing .view-content h2').each(function() {
                    $(this).nextUntil('h2').wrapAll('<div class="accotent"></div>');
                });

                //Make into accordion
                $('.view-people-landing .view-content').accordion({
                    active: 0,
                    collapsible: true,
                    icons: { "header": "\tui-icon-circle-triangle-e", "activeHeader": "\tui-icon-circle-triangle-s" }
                });

                //Now move the txt from the body into these
                $('#ui-accordion-1-panel-0').prepend($('.maritimeinfo').detach());
                $('#ui-accordion-1-panel-1').prepend($('.tradeinfo').detach());
                $('#ui-accordion-1-panel-2').prepend($('.continfo').detach());

            }

            //For Sources
            if( $('.view-source-ind').length) {
                $( ".view-source-ind" ).each(function() {
                    //If there's a picture and transcript/translation, make the picture take just 1/2 the page
                    if( $(this).find('.toright p').length && $(this).find('.srcpic img').length ) {
                        //console.log($(this).find('.srcpic').height());
                        $(this).find('.srcpic').addClass('halfwidth');
                        // $(this).find('.srcpic').css('width', '45%');
                        // $(this).find('.srcpic').css('margin', 'inherit');
                        //$(this).find('.srcpic').css('display', 'inline-block');
                        $(this).find('.toleft').hide();
                    }

                    //If there is no picture or translation/transcript, then we need to make the pdf file/video take the whole page
                    if( !$(this).find('.toright p').length && !$(this).find('.srcpic img').length ) {
                        $(this).find('.toleft').css('width', '100%');
                    }

                    //if there is both translation and transcript, need to toggle
                    if( $(this).find('.srctranscript').length && $(this).find('.srctransclate').length) {
                        //Leave Transcript on by default
                        $(this).find('.srctransclate .srctranwrap').hide();
                        $(this).find('.srctranscript .togglewrap').hide();
                        $(this).find('.srctranscript').addClass("selected");
                    }
                    //if there aren't both, get rid of the toggle
                    else{
                        $(this).find('.togglewrap').remove();
                    }

                    //When you click on togglewrap, toggle
                    $( ".togglewrap" ).click(function() {
                        if( $('.srctranscript.selected').length) {
                            //Turn on Translation
                            $('.srctranscript.selected').removeClass('selected');
                            $('.srctransclate .srctranwrap').show(); //show the translation text
                            $('.srctranscript .srctranwrap').hide(); //hide transcript text
                            $('.srctransclate .togglewrap').hide(); //hide the translation button
                            $('.srctranscript .togglewrap').show(); //show the transcript button
                            $('.srctransclate').addClass("selected");
                        }
                        else{
                            //Turn on Transcription
                            $('.srctransclate.selected').removeClass('selected');
                            $('.srctransclate .srctranwrap').hide(); //hide the translation text
                            $('.srctranscript .srctranwrap').show(); //show transcript text
                            $('.srctransclate .togglewrap').show(); //show the translation button
                            $('.srctranscript .togglewrap').hide(); //hide the transcript button
                            $('.srctranscript').addClass("selected");
                        }
                    });

                    //If there isn't any Related Links, delete the h4
                    if( !$('.srcrelated article').length) {
                        $('.srcrelated').remove();
                    }

                    // If there's an alt title, replace it with the current title
                    if( $('.srcrelated .field--name-field-alternative-title').length) {
                        $( ".srcrelated .field--name-field-alternative-title" ).each(function() {
                            //make it disappear
                            $(this).hide();
                            var $temptit = $(this).find('p').html();
                            //Replace the title

                            var $templink = $(this).parent().parent().find('.node__title a').attr("href");
                            //console.log( $templink);

                            $(this).parent().parent().find('.node__title').html('<a href="'+$templink+'">'+$temptit+'</a>');

                        });
                    }

                    //Make Related Sources Link
                    $( ".srcrelated article" ).each(function() {
                        var $htmlhold = $(this).find('.node__links a').attr("href");
                        $(this).find('.field--name-field-source-thumbnail img').wrap('<a href="'+$htmlhold+'" target="_blank"></a>');

                        //Move the Header in the Related Sources to below the content
                        $(this).find('.node__content').after($(this).find('header').detach());
                    });

                });
            }

            //Timeline
            if( $('.node-type-timeline').length) {
                $( ".srcimg article" ).each(function() {
                    var $htmlhold = $(this).find('.node__links a').attr("href");
                    $(this).find('.field--name-field-source-thumbnail img').wrap('<a href="'+$htmlhold+'" aria-hidden="true" tabindex="-1"></a>');
                });
            }

            //Archive Landing Page
            if( $('.page-node-7').length) {
             //   $('option[value="16"], option[value="18"], option[value="19"], option[value="20"], option[value="22"], option[value="23"], option[value="24"], option[value="25"], option[value="48"], option[value="49"], option[value="50"], option[value="51"], option[value="74"], option[value="75"], option[value="76"], option[value="77"]').hide();
            }

            //If there's a videowrap
            if( $('.videowrapper').length) {
                var mp4hold = $('.videowrapper .mp4src').html();
                var movhold = $('.videowrapper .movsrc').html();
                var ogghold = $('.videowrapper .oggsrc').html();

                if(mp4hold != "" || movhold!= "" || ogghold!=""){
                    $('.videowrapper').html('<video controls><source src="'+mp4hold+'" type="video/mp4"><source src="'+movhold+'" type="video/mov"><source src="'+ogghold+'" type="video/ogg">Your browser does not support the video tag.</video>');
                }
            }


        }
    };
})(jQuery);
