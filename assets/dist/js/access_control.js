$("#designation,#department").change(function () {
    $('#user_role,#user').val("");
    $("#user_role,#user").select2();
});

$("#user_role").change(function () {
    $('#designation,#user,#department').val("");
    $("#designation,#user,#department").select2();
});

function check_uncheck_module_menu(module_no) {
    var isChecked = $(".checkModule_" + module_no).prop('checked');
    if (isChecked) {
            $(".module_menu_" + module_no).prop('checked', false);
            $(".moduleView_" + module_no).prop('checked', false);
            $(".moduleInsert_" + module_no).prop('checked', false);
            $(".moduleUpdate_" + module_no).prop('checked', false);
            $(".moduleDelete_" + module_no).prop('checked', false);

        } else {
            $(".module_menu_" + module_no).prop('checked', true);
            $(".moduleView_" + module_no).prop('checked', true);
            $(".moduleInsert_" + module_no).prop('checked', true);
            $(".moduleUpdate_" + module_no).prop('checked', true);
            $(".moduleDelete_" + module_no).prop('checked', true);
        }
}
function check_uncheck_menu(menu_no) {
    var isChecked = $(".menu_" + menu_no).prop('checked');

    if (isChecked) {
        $(".view_chkbox_" + menu_no).prop('checked', true);
        $(".insert_chkbox_" + menu_no).prop('checked', true);
        $(".update_chkbox_" + menu_no).prop('checked', true);
        $(".delete_chkbox_" + menu_no).prop('checked', true);
        $(".menu_" + menu_no).prop('checked', true);
    }
    else {
        $(".view_chkbox_" + menu_no).prop('checked', false);
        $(".insert_chkbox_" + menu_no).prop('checked', false);
        $(".update_chkbox_" + menu_no).prop('checked', false);
        $(".delete_chkbox_" + menu_no).prop('checked', false);
        $(".menu_" + menu_no).prop('checked', false);
    }
}


$("#checkAllView").click(function () {
    var isChecked = $(this).prop('checked');
    if (isChecked) $(".lblView").prop('checked', true);
    else $(".lblView").prop('checked', false);
});

$("#checkAllInsert").click(function () {
    var isChecked = $(this).prop('checked');
    if (isChecked) $(".lblInsert").prop('checked', true);
    else $(".lblInsert").prop('checked', false);
});

$("#checkAllUpdate").click(function () {
    var isChecked = $(this).prop('checked');
    if (isChecked) $(".lblUpdate").prop('checked', true);
    else $(".lblUpdate").prop('checked', false);
});

$("#checkAllDelete").click(function () {
    var isChecked = $(this).prop('checked');
    if (isChecked) $(".lblDelete").prop('checked', true);
    else $(".lblDelete").prop('checked', false);
});

$("#checkAllMenu").click(function () {
    var isChecked = $(this).prop('checked');
    if (isChecked) {
        $(".allModule").prop('checked', true);
        $(".allMenu").prop('checked', true);
        $(".lblView").prop('checked', true);
        $("#checkAllView").prop('checked', true);

    } else {
        $(".allModule").prop('checked', false);
        $(".allMenu").prop('checked', false);
        $(".lblView").prop('checked', false);
        $("#checkAllView").prop('checked', false);
    }
});

function deletePermission(menu_no) {
    Swal.fire({
        text: "Do you want to delete this access permission?",
        type: 'question',
        showCancelButton: true,
        confirmButtonText: 'Yes',
        confirmButtonColor: "#00c292",
        cancelButtonText: 'No',
        cancelButtonColor: "#e46a76",
        reverseButtons: false
    }).then((result) => {
        if (result.value) {

            var id_url = "/user/access-control/"+menu_no+"/delete/";
            $.ajax({
                url: id_url,
                type: 'POST',
                dataType: 'json',
                async: false,
                data: {
                    csrfmiddlewaretoken: '{{ csrf_token }}'
                },
                success: function (data) {
                    
                    var msg = data;
                    if (data == "success"){
                        $("#"+menu_no.toString()).remove();
                        Swal.fire({
                            type: 'success',
                            title: 'Permission Deleted',
                            text: "User access control successfully deleted.",
                        });
                    } 
                    else{
                        Swal.fire({
                            type: 'warning',
                            title: 'Access Denied',
                            text: data,
                        });
                    } 
                    
                },
                error: function (data) {
                    Swal.fire({
                    type: 'error',
                    title: 'Something Went Wrong!',
                    text: data,
                })
                }
            });
        } 
    });
}