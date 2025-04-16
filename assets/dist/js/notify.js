var notify_badge_class;
var notify_menu_class;
var notify_api_url;
var notify_fetch_count;
var notify_unread_url;
var notify_mark_all_unread_url;
var notify_refresh_period = 50000;
var consecutive_misfires = 0;
var registered_functions = [];


// for now
var messages = '<li class="bg-light">'
                    +'<div class="message-center">'
                        +'<a href="javascript:void(0)">'
                            +'<div class="mail-contnet">'
                                +'<h5 class="text-center text-dark m-4"> No New Notifications</h5>'
                            +'</div>'
                        +'</a>'
                    +'</div>'
                +'</li>';
$(".live_notify_list").after(messages);
$(".all_notify_list").show();
$(".notify").hide();


function fill_notification_badge(data) {
    if(data.unread_count > 0){
        $('.notify').show();
        $('.notify .badge').html(data.unread_count);
        if(data.unread_count > 5){
            $(".all_notify_list").show();
        }else{
            $(".all_notify_list").remove();
        }
    }else{
        $('.notify').hide();
    }
}

function fill_notification_list(data) {
    if(data.unread_list.length == 0){
        var messages = '<li class="bg-light">'
                            +'<div class="message-center">'
                                +'<a href="javascript:void(0)">'
                                    +'<div class="mail-contnet">'
                                        +'<h5 class="text-center text-dark m-4"> No New Notifications</h5>'
                                    +'</div>'
                                +'</a>'
                            +'</div>'
                        +'</li>';
    }else{
        var messages = data.unread_list.map(function (item) {
            
            if(item.action_url === null){ item.action_url = 'href="javascript:void(0)"'; }
            else{ item.action_url = 'href="' + item.action_url + '" target="_blank"'; }

            return '<li data-id="' + item.slug + '">'
                    +'<div class="message-center">'
                        +'<a ' + item.action_url + '>'
                            +'<div class="mail-contnet">'
                                +'<h6>' + item.verb + '</h6>'
                                +'<span class="mail-desc">' + item.description + '</span>'
                                +'<span class="time">' + item.timesince + 's ago</span>'
                            +'</div>'
                        +'</a>'
                    +'</div>'
                +'</li>';
            }
        ).join('')
    }
    
    

    $(".notify_list li").each(function(index, item){
        if($(item).hasClass("live_notify_list") || $(item).hasClass("all_notify_list")){
            // pass
        }else{
            $(item).remove();
        }
    })

    $(".live_notify_list").after(messages);
}

function register_notifier(func) {
    registered_functions.push(func);
}

function fetch_api_data() {
    if (registered_functions.length > 0) {
        //only fetch data if a function is setup
        var r = new XMLHttpRequest();
        r.addEventListener('readystatechange', function(event){
            if (this.readyState === 4){
                if (this.status === 200){
                    consecutive_misfires = 0;
                    var data = JSON.parse(r.responseText);
                    registered_functions.forEach(function (func) { func(data); });
                }else{
                    consecutive_misfires++;
                }
            }
        })
        r.open("GET", notify_api_url+'?max='+notify_fetch_count, true);
        r.send();
    }
    if (consecutive_misfires < 10) {
        setTimeout(fetch_api_data,notify_refresh_period);
    } else {
        var badges = document.getElementsByClassName(notify_badge_class);
        if (badges) {
            for (var i = 0; i < badges.length; i++){
                badges[i].innerHTML = "!";
                badges[i].title = "Connection lost!"
            }
        }
    }
}

setTimeout(fetch_api_data, 1000);


$("body").on("click", '.notify_list li, .notify_list_item', function(){
    let notification_slug = $(this).data("id");
    $.ajax({
        url: "/inbox/notifications/mark-as-read/"+notification_slug+"/",
        type: "GET",
        dataType: 'json',
        success: function (data) {
            fetch_api_data()
        },
    });
})