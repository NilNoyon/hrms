/*
Template Name: Admin Template
Author: Wrappixel

File: js
*/
// ============================================================== 
// Auto select left navbar
// ============================================================== 
$(function () {
    var url = window.location;
    var element = $('ul#sidebarnav a').filter(function () {
        return this.href == url;
    }).addClass('active').parent().addClass('active');
    while (true) {
        if (element.is('li')) {
            element = element.parent().addClass('in').parent().addClass('active').children('a').addClass('active');
            
        }
        else {
            break; 
        }
    }
    $('#sidebarnav a').on('click', function (e) {
        if (!$(this).hasClass("active")) {
            // hide any open menus and remove all other classes
            $("ul", $(this).parents("ul:first")).removeClass("in");
            $("a", $(this).parents("ul:first")).removeClass("active");
            
            // open our new menu and add the open class
            $(this).next("ul").addClass("in");
            $(this).addClass("active");
            
        }
        else if ($(this).hasClass("active")) {
            $(this).removeClass("active");
            $(this).parents("ul:first").removeClass("active");
            $(this).next("ul").removeClass("in");
        }
    })
    $('#sidebarnav >li >a.has-arrow').on('click', function (e) {
        e.preventDefault();
    });

    $(document).ready(function () {
       
        // for mega menu
        $(".megaMainMenu a").removeClass('active');
        $(".mega-dropdown").removeClass('active');
        $(".mega-dropdown a").removeClass('active');
        $("#helpdesk").removeClass('active');

        $('.megaMainMenu a').click(function () { 
            if($("#"+$(this).attr("data-module")).css("display") == "block") {
                $("#"+$(this).attr("data-module")).hide(); 
                $(".megaMenu").removeClass('border');
            }
            else {
                $(".sub-mega-menu").hide();
                $(".megaMainMenu a").removeClass('active');
                $(".megaMainMenu a").removeClass('menuIcon');
                $("#"+$(this).attr("data-module")).addClass('active');
                $(this).addClass('active');
                $(this).css('active');
                $(this).addClass('menuIcon')              
                $(".megaMenu").removeClass('border');
                $("#"+$(this).attr("data-module")).closest("li").addClass('border');
                $("#"+$(this).attr("data-module")).show();  
        
            }
           
        });
       
        // navbar under line
        $('#helpdesk').on('click',function(){
            $('#sidebarnav .nav-link ').parent().removeClass('active');
            $('#sidebarnav .nav-link ').removeClass('show');          
            $("#helpdesk").addClass('active');
        });
        $('#sidebarnav .nav-link.dropdown-toggle>a').on('click',function(){        
            $('#helpdesk').removeClass('active');
            $('.nav-link.dropdown-toggle').parent().removeClass('active');      
          
            $(this).parent().addClass('active');
        });

        $(".access").on('click', function(event){
            $('.bounceInDown').removeClass('show')
            event.preventDefault();
            Swal.fire({
                title: 'Access restricted',
                type: 'info',
                html: 'Please contact with Admin',    
                showCloseButton: false,
                showCancelButton: false,
                focusConfirm: false,
                confirmButtonText: '<i class="fa fa-thumbs-up"></i> OK',
            })
        })

    });
});