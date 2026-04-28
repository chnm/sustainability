/**
 * Created by JetBrains PhpStorm.
 * User: james.mccartney
 * Date: 9/30/16
 * Time: 11:15 AM
 * To change this template use File | Settings | File Templates.
 */

(function($) {
    //var base = '/dev/arlington/';
    var base = '/';

    //var base = '/futl/';
    Drupal.behaviors.arlingtonUtility = {
        attach: function(context, settings) {

            //if User is guest



            //if dashboard
            if ($('.page-node-99').length){
                $('.delete-class').on('click', function () {
                    return confirm('Are you sure you want to permanently remove this class?');
                });

                $('.delete-module').on('click', function () {
                    return confirm('Are you sure you want to permanently remove this module?');
                });
            }

            //Delete Student
            if ($('.page-content-studentwork').length){
                $('.delete-student').on('click', function () {
                    return confirm('Are you sure you want to permanently remove this student?');
                });
            }


            if ($('#create-students').length) {
                $.post(base + 'utility/op/getCreateStudentsForm/', {
                }, function(data) {
                    $('#create-students').html(data);
                    var vars = getUrlVars();
                    $('#hidden-group').val(vars['gid']);
                    var count = 0;
                    $('#hidden-count').val(count);
                    $('#add-another').click(function(){
                        count++;
                        console.log(count);
                        var markup = $("#student-0").html();
                        markup = markup.replace(/0/g,count.toString());
                        markup = '<fieldset id="student-'+count+'" class="student-field">' + markup + '</fieldset>';
                        $( markup ).insertBefore( "#submit" );
                        $('#hidden-count').val(count);
                    });
                });
            }


            if ($('#create-module').length) {
                var vars = getUrlVars();
                var theGroup = vars['gid'];
                $.post(base + 'utility/op/getModuleForm/', { group: theGroup
                }, function(data) {
                    $('#create-module').html(data);
                    $( "#datepicker" ).datepicker();
                    var vars = getUrlVars();
                    $('#hidden-group').val(theGroup);
                });
            }

            if ($('#create-class').length) {
                $.post(base + 'utility/op/getCreateClassForm/', {
                }, function(data) {
                    $('#create-class').html(data);
                });
            }

            //*****************
            //update student password page ************************************************************
            //******************
            if ($('.page-node-745').length) {
                console.log('update password page');
              //  $('.l-header .pane-page-title').prepend( $('.headerwrap h2').detach() );
                var vars = getUrlVars();
                console.log(vars);
                $.post(base + 'utility/op/getUpdateStudentPasswordForm/', {
                }, function(data) {
                    console.log(data);
                    $('.pane-page-content').html(data);
                }).done(function(){
                    $('#parsley-form').attr("action", base + 'utility/op/updatePassword/' + vars['uid']);
                });
            }


        }//end attach
    };//end drupal behavior

    var studentClickFunction = function(){

    };

    function getUrlVars() {
        var vars = {};
        var parts = window.location.href.replace(/[?&]+([^=&]+)=([^&]*)/gi, function(m,key,value) {
            vars[key] = value;
        });
        return vars;
    }

}(jQuery));