$(function () {
    "use strict";
    $(function () {
        $(".preloader").fadeOut();
    });
    jQuery(document).on('click', '.mega-dropdown', function (e) {
        e.stopPropagation()
    });
    // ==============================================================
    // This is for the top header part and sidebar part
    // ==============================================================
    var set = function () {
        var width = (window.innerWidth > 0) ? window.innerWidth : this.screen.width;
        var topOffset = $(".top-navbar").height() - 10;
        if (width < 1170) {
            $("body").addClass("mini-sidebar");
            $('.navbar-brand span').hide();
            // $(".sidebartoggler i").addClass("ti-menu");
        }
        else {
            $("body").removeClass("mini-sidebar");
            $('.navbar-brand span').show();
       }
         var height = ((window.innerHeight > 0) ? window.innerHeight : this.screen.height) - 1;
        height = height - topOffset;
        if (height < 1) height = 1;
        if (height > topOffset) {
            $(".page-wrapper").css("min-height", (height) + "px");
        }
    };
    $(window).ready(set);
    $(window).on("resize", set);
    // ==============================================================
    // Theme options
    // ==============================================================
    $(".sidebartoggler").on('click', function () {
        if ($("body").hasClass("mini-sidebar")) {
            $("body").trigger("resize");
            $("body").removeClass("mini-sidebar");
            $('.navbar-brand span').show();
        }
        else {
            $("body").trigger("resize");
            $("body").addClass("mini-sidebar");
            $('.navbar-brand span').hide();
        }
    });
    // this is for close icon when navigation open in mobile view
    $(".nav-toggler").click(function () {
        $("body").toggleClass("show-sidebar");
        // $(".nav-toggler i").toggleClass("ti-menu");
        // $(".nav-toggler i").addClass("ti-close");
    });
    $(".search-box a, .search-box .app-search .srh-btn").on('click', function () {
        $(".app-search").toggle(200);
    });
    // ==============================================================
    // Right sidebar options
    // ==============================================================
    $(".right-side-toggle").click(function () {
        $(".right-sidebar").slideDown(50);
        $(".right-sidebar").toggleClass("shw-rside");
    });
    // ==============================================================
    // This is for the floating labels
    // ==============================================================
    $('.floating-labels .form-control').on('focus blur', function (e) {
        $(this).parents('.form-group').toggleClass('focused', (e.type === 'focus' || this.value.length > 0));
    }).trigger('blur');

    $('body').on('keyup', '.floating-labels .form-control', function (e) {
        $(this).parents('.form-group').toggleClass('focused', (e.type === 'focus' || this.value.length > 0));
    }).trigger('blur');
    // ==============================================================
    //tooltip
    // ==============================================================
    $(function () {
            $('[data-toggle="tooltip"]').tooltip()
        })
    // ==============================================================
    //Popover
    // ==============================================================
    $(function () {
         $('[data-toggle="popover"]').popover()
    })

    // ==============================================================
    // Perfact scrollbar
    // ==============================================================
    $('.right-side-panel, .message-center, .right-sidebar').perfectScrollbar();
	$('#chat, #msg, #comment, #todo').perfectScrollbar(); 
    // ==============================================================
    // Resize all elements
    // ==============================================================
    $("body").trigger("resize");
    // ==============================================================
    // To do list
    // ==============================================================
    $(".list-task li label").click(function () {
        $(this).toggleClass("task-done");
    });
    // ==============================================================
    // Collapsable cards
    // ==============================================================
    $('a[data-action="collapse"]').on('click', function (e) {
        e.preventDefault();
        $(this).closest('.card').find('[data-action="collapse"] i').toggleClass('fas fa-angle-up fas fa-angle-down');
        $(this).closest('.card').children('.card-body').collapse('toggle');
    });
    // Toggle fullscreen
    $('a[data-action="expand"]').on('click', function (e) {
        e.preventDefault();
        $(this).closest('.card').find('[data-action="expand"] i').toggleClass('mdi-arrow-expand mdi-arrow-compress');
        $(this).closest('.card').toggleClass('card-fullscreen');
    });
    // Close Card
    $('a[data-action="close"]').on('click', function () {
        $(this).closest('.card').removeClass().slideUp('fast');
    });
    // ==============================================================
    // fixed navigattion while scrolll
    // ==============================================================
    function collapseNavbar() {
        if ($(window).scrollTop() > 10) {
            $("body").addClass("fixed-sidebar");
            $(".left-sidebar").addClass("animated slideInDown");

        } else {
            $("body").removeClass("fixed-sidebar");
            $(".left-sidebar").removeClass("animated slideInDown");
        }
    }
    $(window).scroll(collapseNavbar);
    collapseNavbar()
    // ==============================================================
    // Color variation
    // ==============================================================

    var mySkins = [
        "skin-default",
        "skin-green",
        "skin-red",
        "skin-blue",
        "skin-purple",
        "skin-megna",
        "skin-default-dark",
        "skin-green-dark",
        "skin-red-dark",
        "skin-blue-dark",
        "skin-purple-dark",
        "skin-megna-dark"
    ]
        /**
         * Get a prestored setting
         *
         * @param String name Name of of the setting
         * @returns String The value of the setting | null
         */
    function get(name) {
        if (typeof (Storage) !== 'undefined') {
            return localStorage.getItem(name)
        }
        else {
            window.alert('Please use a modern browser to properly view this template!')
        }
    }
    /**
     * Store a new settings in the browser
     *
     * @param String name Name of the setting
     * @param String val Value of the setting
     * @returns void
     */
    function store(name, val) {
        if (typeof (Storage) !== 'undefined') {
            localStorage.setItem(name, val)
        }
        else {
            window.alert('Please use a modern browser to properly view this template!')
        }
    }

    /**
     * Replaces the old skin with the new skin
     * @param String cls the new skin class
     * @returns Boolean false to prevent link's default action
     */
    function changeSkin(cls) {
        $.each(mySkins, function (i) {
            $('body').removeClass(mySkins[i])
        })
        $('body').addClass(cls)
        store('skin', cls)
        return false
    }

    function setup() {
        var tmp = get('skin')
        if (tmp && $.inArray(tmp, mySkins)) changeSkin(tmp)
            // Add the change skin listener
        $('[data-skin]').on('click', function (e) {
            if ($(this).hasClass('knob')) return
            e.preventDefault()
            changeSkin($(this).data('skin'))
        })
    }
    setup()
    $("#themecolors").on("click", "a", function () {
        $("#themecolors li a").removeClass("working"),
        $(this).addClass("working")
    })

    // For Custom File Input
    $('.custom-file-input').on('change',function(){
        //get the file name
        var fileName = $(this).val();
        //replace the "Choose a file" label
        $(this).next('.custom-file-label').html(fileName);
    })
    let elements = jQuery("[required]"), i;
    for(i=0;i<elements.length;i++){
        if($(elements[i]).siblings('.required').length < 1){
            jQuery("[required]").before("<p class='required'>*</p>");
        }
    }
    //jQuery("[required]").before("<p class='required'>*</p>");
});

function toast_msg(header,msg,icon,duration){
    $.toast({
        heading: header,
        text: msg,
        position: 'top-right',
        loaderBg:'#fff',
        icon: icon,
        hideAfter : duration,
        stack: false
    });
}

function class_sum_validation(class_name, valided_input){ //this function can use to compare validation for an input/value on multiple inputs value. just pass input class names & valided input 
    var is_valid = true;
    var qty_sum = 0;
    $("."+class_name).each(function(i){
      if($(this).val()) qty_sum += parseFloat($(this).val());
    });
    if(parseFloat(qty_sum) > valided_input){
      toast_msg('Invalid Input!',"Required is "+valided_input+" & your input is "+parseFloat(qty_sum)+"!",'warning',false);
      is_valid  = false;
    }
    return is_valid
  }

function input_validation(el) {
    if (el.value != "") {
        if (parseFloat(el.value) > parseFloat(el.max)) {
        el.value = el.max;
        $.toast({
            heading: "Invalid Input",
            text: "Can't exceed the maximum input. The maximum input is "+el.max.toString()+" but inputted "+el.value.toString(),
            position: 'top-right',
            loaderBg: '#fff',
            icon: 'warning',
            hideAfter: 10000,
            stack: true
        });
        }
        else if (parseFloat(el.value) < parseFloat(el.min)) {
        el.value = el.min;
        $.toast({
            heading: "Invalid Input",
            text: "The minimum input must be greater than "+el.min.toString(),
            position: 'top-right',
            loaderBg: '#fff',
            icon: 'warning',
            hideAfter: 10000,
            stack: true
        });
        }
        // else{

        // }
    }
}

function checkNumber(el) {  
    $(el).keypress(function(e){         
      var keyCode = e.which;         
      /* 48-57 - (0-9)Numbers
      46 - (.)
      */    // Not allow special 
      if (!((keyCode >= 48 && keyCode <= 57))) {
        e.preventDefault();
      }
    });
}

function checkNumberWithPoint(el) {  
    $(el).keypress(function(e){         
      var keyCode = e.which;         
      /* 48-57 - (0-9)Numbers
      46 - (.)
      */    // Not allow special 
      if (!((keyCode >= 48 && keyCode <= 57)) 
        && keyCode != 46 ) {
        e.preventDefault();
      }
    });
}

function itemSearch(class_name,item_type) {  //Bind select2 by typing select2 with additional parameters by the class name
    //the select input must have item_type attribute with one of this value fabric/flat_fabric/accessories
    $("."+class_name).select2({
        minimumInputLength: 2,
        placeholder: $(this).attr("data-title"),
        ajax: {
            url: "/mnm/item-search/",
            dataType: "json",
            data: function(term, page) {
                term["item_type"] = item_type // item type may be fabric/flat_fabric/accessories
                return {
                    q: term,
                };
            },
            processResults: function (data) {
                return {
                    results: data
                };
            }
        },
        tags: false,
        closeOnSelect: true,
    });
}

function itemSearchForModalBackup(class_name,item_type) { 
    //the select input must have item_type attribute with one of this value fabric/flat_fabric/accessories
    $("."+class_name).select2({
        dropdownParent: $($("."+class_name).attr("data-counter")),
        minimumInputLength: 3,
        placeholder: $(this).attr("data-title"),
        ajax: {
            url: "/mnm/item-search/",
            dataType: "json",
            data: function(term, page) {
            },
            processResults: function (data) {
            }
        },
        tags: false,
        closeOnSelect: true,
    }); //Bind select2 by typing select2 with additional parameters by the class name
}

function itemSearchForModal(class_name,item_type) {  //Bind select2 by typing select2 with additional parameters by the class name
    //the select input must have item_type attribute with one of this value fabric/flat_fabric/accessories
    $("."+class_name).each(function(index, item) {
        $('#'+$(item).attr("id")).select2({
            dropdownParent: $($("."+class_name).attr("data-counter")),
            minimumInputLength: 2,
            placeholder: $($("."+class_name).attr("data-title")),
            ajax: {
                url: "/mnm/item-search/",
                dataType: "json",
                data: function(term, page) {
                    term["item_type"] = item_type // item type may be fabric/flat_fabric/accessories
                    return {
                        q: term,
                    };
                },
                processResults: function (data) {
                    return {
                        results: data
                    };
                }
            },
            tags: false,
            closeOnSelect: true,
        });
    });
}

function validateSize(input,max_size) {
    const fileSize = input.files[0].size / 1024 / 1024; // in MiB
    if (parseInt(fileSize) > parseInt(max_size)) {
      Swal.fire({
        type: 'warning',
        title: 'Invalid Selection',
        text: "Maximum file size is "+max_size.toFixed(0).toString()+"MB, Your uploaded file size is "+fileSize.toFixed(0).toString()+"MB. Please select another file!",
      })
      input.value = null;
      $("[for="+$(input).attr("id")+"]").html($(input).attr("data-title"))
    } 
}

// consumption with wastage calculation..
function consumptionWithWastage(consumption, wastage){
    let cww = 0
    if(consumption && wastage){
        cww = parseFloat(consumption)/((100-parseFloat(wastage))/100)
    }else{
        if(consumption){
            cww = parseFloat(consumption)
        }
    }
    return (cww).toFixed(6)
}

// const icon_array = ['info','success','primary','warning','danger'];

function kg_to_yards_conversion(kg, width, gsm){
    let result =(1000*kg)/(gsm*width*0.009144);
    return parseFloat(result).toFixed(6)
}
function yards_to_kg_conversion(yards, width, gsm){
    let result =(yards*gsm*width*0.009144)/1000;
    return parseFloat(result).toFixed(6)
}

function check_duplicacy(dict,value_data){
    let duplicate = 0;
    for ( i = 0;i<dict.length;i++){
        if(dict[i].value == value_data){
            duplicate = 1;
            return duplicate;
        }
    }
}
// consumption with wastage forward calculation..
function forwardConsumptionWithWastage(consumption, wastage){
    let cww = 0
    if(consumption && wastage){
        cww = parseFloat(consumption) + (((parseFloat(wastage))/100) * parseFloat(consumption))
    }else{
        if(consumption){
            cww = parseFloat(consumption)
        }
    }
    return (cww).toFixed(6)
}


function colorSearch(class_name,item_type) {  //Bind select2 by typing select2 with additional parameters by the class name
    //the select input must have item_type attribute with one of this value fabric/flat_fabric/accessories
    $("."+class_name).select2({
        minimumInputLength: 2,
        placeholder: $(this).attr("data-title"),
        ajax: {
            url: "/mnm/color-search/",
            dataType: "json",
            data: function(term, page) {
                term["item_type"] = item_type // item type may be fabric/flat_fabric/accessories
                return {
                    q: term,
                };
            },
            processResults: function (data) {
                return {
                    results: data
                };
            }
        },
        tags: false,
        closeOnSelect: true,
    });
}


function foWiseFileSearch(class_name,item_type) {  //Bind select2 by typing select2 with additional parameters by the class name
    //the select input must have item_type attribute with one of this value fabric/flat_fabric/accessories
    $("."+class_name).select2({
        minimumInputLength: 3,
        placeholder: "FO No/Style No/File No",
        ajax: {
            url: "/tracker/get-fo-wise-file/",
            dataType: "json",
            data: function(term, page) {
                term["item_type"] = item_type // item type may be fabric/flat_fabric/accessories
                return {
                    q: term,
                };
            },
            processResults: function (data) {
                return {
                    results: data
                };
            }
        },
        tags: false,
        closeOnSelect: true,
    });
}

