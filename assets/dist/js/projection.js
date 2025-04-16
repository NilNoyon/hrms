
$("#btnProjectionMasterSave, #btnProjectionMasterSubmit").click(function () {
  var valid = true;
  $("#projectionMaster :input[required]:visible").each(function() {
    if(valid && !$(this).val()){
      valid = false;
      if($(this).hasClass("select2")) $(this).select2('open');
      else $(this).focus();
      $.toast({
        heading: "Invalid",
        text: $(this).data("title")+" is required field",
        position: 'top-right',
        loaderBg: '#fff',
        icon: 'warning',
        hideAfter: false,
        stack: true
      });
    }

  });
    if(valid){
      var formData = new FormData(document.getElementById("projectionMaster"));
      $.ajax({
        cache: false,
        url: "/mnm/projection-entry/",
        type: "POST",
        processData: false,
        contentType: false,
        data: formData,
        success: function (data) {
          if(data["icon"] == "success") {
            $("#order_pk").val(data["cost_master"]);
          }
          $.toast({
            heading: "Projection Order Saving",
            text: data["msg"],
            position: 'top-right',
            loaderBg: '#fff',
            icon: data["icon"],
            hideAfter: 5000,
            stack: false
          });
        },
        error: function (xhr, desc, err) {
          // errorMsg(err)
        }
      });
    }
});
