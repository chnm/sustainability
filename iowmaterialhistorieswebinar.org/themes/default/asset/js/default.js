var Omeka = {};

(function($) {
    function fixIframeAspect() {
        $('iframe').each(function () {
            var aspect = $(this).attr('height') / $(this).attr('width');
            $(this).height($(this).width() * aspect);
        });
    }

    function framerateCallback(callback) {
        var waiting = false;
        callback = callback.bind(this);
        return function () {
            if (!waiting) {
                waiting = true;
                window.requestAnimationFrame(function () {
                    callback();
                    waiting = false;
                });
            }
        }
    }

    $(document).ready(function() {
        // Below 800px the theme collapses the navigation and draws a hamburger
        // as `header nav:before`. Upstream listened for a click on the <nav>
        // itself, which is not focusable and announces nothing -- so a keyboard
        // could not open the menu, and assistive technology was never told
        // there was one (WCAG 2.1.1, 4.1.2). The chrome now carries a real
        // <button>; the pseudo-element is suppressed in a11y.css.
        var nav = $('header nav');
        var toggle = $('#menu-toggle');

        nav.addClass('closed');

        toggle.on('click', function() {
            var open = nav.hasClass('open');
            nav.toggleClass('open', !open).toggleClass('closed', open);
            toggle.attr('aria-expanded', String(!open));
        });

        // Escape closes it and returns focus to the control that opened it.
        nav.on('keydown', function(e) {
            if (e.key === 'Escape' && nav.hasClass('open')) {
                nav.removeClass('open').addClass('closed');
                toggle.attr('aria-expanded', 'false').trigger('focus');
            }
        });

        var expandString = Omeka.jsTranslate('Expand');
        var collapseString = Omeka.jsTranslate('Collapse');

        $('header nav ul ul').each(function(){
          var childMenu = $(this);
          var parentItem = childMenu.parent('li');
          var toggleButton = $('<button type="button" class="child-toggle"></button>');
          toggleButton.attr('aria-label', expandString);
          parentItem.addClass('parent');
          parentItem.children('a').first().wrap('<div class="parent-link"></div>');
          parentItem.find('.parent-link').append(toggleButton);
        });

        $('header nav').on('click', '.child-toggle', function(e) {
          e.stopPropagation();
          var childToggle = $(this);
          var childMenu = childToggle.parents('.parent').first().find('ul').first();
          childMenu.toggleClass('open');
          if (childMenu.hasClass('open')) {
            childToggle.attr('aria-label', collapseString);
          } else {
            childToggle.attr('aria-label', expandString);
          }
        });

        // Maintain iframe aspect ratios
        $(window).on('load resize', framerateCallback(fixIframeAspect));
        fixIframeAspect();
    });
})(jQuery);
