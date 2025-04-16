
function expand_td(issue) {
  $("." + issue + "_show").prop("hidden", true);
  $("." + issue + "_hide").show();
}

function close_td(issue) {
  $("." + issue + "_hide").hide();
  $("." + issue + "_show").prop("hidden", false);
}

function assignResolver(issue) {
  if ($("#resolver_" + issue.toString()).val()) {
    Swal.fire({
          title: "Do you want to assign " + $("#resolver_" + issue.toString()).select2('data')[0].text + " for this issue?",
          //text: "You won't be able to revert this!",
          type: 'warning',
          showCancelButton: true,
          confirmButtonText: 'Yes',
          confirmButtonColor: "#00c292",
          cancelButtonText: 'No',
          cancelButtonColor: "#e46a76",
          reverseButtons: false
      }).then((result) => {
          if (result.value) {
            $.ajax({
              url: "/helpdesk/issue-assign/",
              type: "POST", // http method
              data: {
                assign_note: $("#note").val(),
                issue: issue,
                assigned_to: $("#resolver_" + issue.toString()).val(),
              },
              dataType: 'json',
              success: function (data) {
                Swal.fire("Resolver Assign", data);
                $("#row_" + issue.toString()).remove();
              },
            });
          } else {
              swalWithBootstrapButtons.fire(
                  'Cancelled',
                  'Not Assign',
                  'error'
              )
          }
          $('#complete').modal('hide');
          $("#note").val(''); 
          $("#btnIssueDone").html('');
      })
    }  
  else {
    Swal.fire({
        type: 'warning',
        title: 'Invalid Resolver',
        text: 'Please select resolver!',
    })
  }
}

function cancelIssue(issue) {
    $.ajax({
      url: "/helpdesk/issue-cancel/",
      type: "POST", // http method
      data: {
        canceled_note: $("#note").val(),
        issue: issue,
      },
      dataType: 'json',
      success: function (data) {
        Swal.fire("Issue Canceled", data);
        $("#row_" + issue.toString()).remove();
        $('#complete').modal('hide');
        $("#note").val(''); 
        $("#btnIssueDone").html('');
      },
    });
  } 

function issueResolve(issue, status) {
  var msg_status = "start";
  var note = $("#note").val();
  if (status == "4") 
  {
      msg_status = "complete";
      $.ajax({
        url: "/helpdesk/issue-resolve/",
        type: "POST", // http method
        data: {
          issue: issue,
          note: note,
          status: status,
        },
        dataType: 'json',
        success: function (data) {
          Swal.fire("Issue Resolve", data);
          $('#complete').modal('hide');
          $("#row_" + issue.toString()).remove();
          $("#note").val(''); 
          $("#btnIssueDone").html('');
          location.reload(); //reload after starting the issue
        },
      });
    }
    else{
      Swal.fire({
          title: "Do you want to " + msg_status + " this issue?",
          //text: "You won't be able to revert this!",
          type: 'warning',
          showCancelButton: true,
          confirmButtonText: 'Yes',
          confirmButtonColor: "#00c292",
          cancelButtonText: 'No',
          cancelButtonColor: "#e46a76",
          reverseButtons: false
      }).then((result) => {
          if (result.value) {
              $.ajax({
                url: "/helpdesk/issue-resolve/",
                type: "POST", // http method
                data: {
                  issue: issue,
                  note: note,
                  status: status,
                },
                dataType: 'json',
                success: function (data) {
                  Swal.fire("Issue Start", data);
                  // $("#my_issue-table tbody").prepend(
                  //   $("#row_" + issue.toString()).html()
                  // );
                  $("#row_" + issue.toString()).remove();
                  // $("#btnResolve_"+ issue.toString()).html(`
                  //     <button type="submit" class="btn waves-effect waves-light btn-rounded btn-outline-success" onClick="issueFeedbackModal('`+ issue.toString() + `')">Feedback
                  //     </button>
                  //     <button type="submit" class="btn waves-effect waves-light btn-rounded btn-outline-success" onClick="issueCompleteModal('`+ issue.toString() + `')">Done
                  //     </button>
                  //   `);
                    
                  // $("#assigned_date_" + issue.toString()).html(new Date());
                  location.reload(); //reload after starting the issue
                },
              });
          } else {
              swalWithBootstrapButtons.fire(
                  'Cancelled',
                  'Not Started',
                  'error'
              )
          }
      })
    }
}

function issueFeedback(issue) {
      $.ajax({
      url: "/helpdesk/issue-feedback/",
      type: "POST", // http method
      data: {
        issue: issue,
        note: $("#note").val(),
      },
      dataType: 'json',
      success: function (data) {
        Swal.fire("Issue Feedback", data);
        $('#complete').modal('hide');
        $("#btnIssueDone").html('');
        $("#resolver_note_"+issue.toString()).html("<b>Note: </b>"+$("#note").val());
        $("#note").val('');
        
      },
    });
}

function assessmentApprove(assessment, status, action) {
  $.ajax({
    url: "/helpdesk/device-assessment-approve/",
    type: "POST", // http method
    data: {
      assessment: assessment,
      note: $("#note").val(),
      status: status,
      action: action,
    },
    dataType: 'json',
    success: function (data) {
      Swal.fire("Assessment Approve", data);
      $('#approve').modal('hide');
      $("#assess_row_" + assessment.toString()).remove();
      $("#note").val(''); 
      $("#btnAssessmentApprove").html(''); 
    },
  });
} 


function issueCompleteModal(issue) {
  $('#issueModalTitle').html('Issue Complete');
  $('#complete').modal('show');
  $("#btnIssueDone").html(`
      <button type="submit" class="btn waves-effect waves-light btn-rounded btn-success" style="width:50%" onClick="issueResolve('`+ issue.toString() + `','4')">Done
      </button>
    `);
}

function issueFeedbackModal(issue) {
  $('#issueModalTitle').html('Issue Feedback');
  $('#complete').modal('show');
  $("#btnIssueDone").html(`
      <button type="submit" class="btn waves-effect waves-light btn-rounded btn-success" style="width:50%" onClick="issueFeedback('`+ issue.toString() + `')">Send
      </button>
    `);
}

function issueAssignModal(issue) {
  if ($("#resolver_" + issue.toString()).val()) {
  $('#issueModalTitle').html('Issue Assign');
  $('#complete').modal('show');
  $("#btnIssueDone").html(`
      <button type="submit" class="btn waves-effect waves-light btn-rounded btn-success" style="width:50%" onClick="assignResolver('`+ issue.toString() + `','4')">Assign
      </button>
    `);
  }  
  else {
    Swal.fire({
        type: 'warning',
        title: 'Invalid Resolver',
        text: 'Please select resolver!',
    })
  }
}

function issueCancelModal(issue) {
  Swal.fire({
    title: "Do you want to cancel this issue?",
    type: 'warning',
    showCancelButton: true,
    confirmButtonText: 'Yes',
    confirmButtonColor: "#00c292",
    cancelButtonText: 'No',
    cancelButtonColor: "#e46a76",
    reverseButtons: false
  }).then((result) => {
      if (result.value) {
    $('#issueModalTitle').html('Issue Cancel');
    $('#complete').modal('show');
    $("#btnIssueDone").html(`
        <button type="submit" class="btn waves-effect waves-light btn-rounded btn-success" style="width:50%" onClick="cancelIssue('`+ issue.toString() + `','1')">Cancel
        </button>
      `);
    } 
  });
}

$("body").on('change', '#issue_type, #resolver_issue_type', function () {
  $("#issue_filter").submit();
});

$("#btnIssueSubmit").click(function () {
  if($("#description").val().length > 0) {
    
    Swal.fire({
        title: "Do you want to submit the issue?",
        //text: "You won't be able to revert this!",
        type: 'warning',
        showCancelButton: true,
        confirmButtonText: 'Yes',
        confirmButtonColor: "#00c292",
        cancelButtonText: 'No',
        cancelButtonColor: "#e46a76",
        reverseButtons: false
    }).then((result) => {
        if (result.value) {
          $("#issueForm").submit();
        } else {
            swalWithBootstrapButtons.fire(
                'Cancelled',
                'Not submitted',
                'error'
            )
        }
          $('#complete').modal('hide');
          $("#note").val(''); 
          $("#btnIssueDone").html('');
    })
  }
  else {
      Swal.fire({
        type: 'warning',
        title: 'Invalid Input',
        text: 'Please fillup the required field!',
    })
  }
});


$("body").on('click', '.user_info', function() {

  $.ajax({
        url: "/helpdesk/get-user/",
        type: "POST", // http method
        data: {
          emp_id: $(this).data('id'),
        },
        dataType: 'json',
        success: function (data) {
          if (data['photo'] != "None") $("#emp_photo").attr("src", "/assets/uploads/"+data['photo']);
          else $("#emp_photo").attr("src", "/assets/images/users/user.png");
          $("#emp_photo").addClass("img-fluid");
          $("#user_profile").show();
          $("#myModalLabel").html(data['user'][0].name);
          $("#emp_name").html(data['user'][0].name+"("+data['user'][0].employee_id+")");
          $("#location").html(data['user'][0].company__name+"("+data['location']+")");
          $("#department").html(data['user'][0].department__name);
          $("#designation").html(data['user'][0].designation__name);
          $("#email").html(
            `
            <a href="callto:`+data['user'][0].email+`" style="color:blue">
            <img src="https://www.onmsft.com/wp-content/uploads/2020/03/microsoftteamsnew.jpg" alt="Teams" width="30" ></a>
            | <a href="mailto:`+data['user'][0].email+`" style="color:blue">`+data['user'][0].email+`</a>
            `
          );
          $("#phone").html(
            `
            <a href="tel:`+data['phone']+`" style="color:blue">`+data['phone']+`</a>
            `
          );
          
        },
      });
});

$(".assessment_view").click(function() {

  $.ajax({
        url: "/helpdesk/device-assessment-view/",
        type: "POST", // http method
        data: {
          assessment_id: $(this).data('id'),
        },
        dataType: 'json',
        success: function (data) {
          if(data.issuer_dpt_approve_at) var issuer_dpt_approve_at = moment(data.issuer_dpt_approve_at).format('D-MM-YYYY, h:mm:ss a');
          else var issuer_dpt_approve_at = "N/A";
          if(data.issuer_dpt_head_note) var issuer_dpt_head_note = data.issuer_dpt_head_note
          else var issuer_dpt_head_note = "N/A";

          if(data.ict_dpt_approve_at) var ict_dpt_approve_at = moment(data.ict_dpt_approve_at).format('D-MM-YYYY, h:mm:ss a');
          else var ict_dpt_approve_at = "N/A";
          if(data.ict_head_note) var ict_head_note = data.ict_head_note
          else var ict_head_note = "N/A";
          
          // if(data.ed_approve_at) var ed_approve_at = moment(data.ed_approve_at).format('D-MM-YYYY, h:mm:ss a');
          // else var ed_approve_at = "N/A";
          // if(data.ed_note) var ed_note = data.ed_note
          // else var ed_note = "N/A";

          if(data.ceo_approve_at) var ceo_approve_at = moment(data.ceo_approve_at).format('D-MM-YYYY, h:mm:ss a');
          else var ceo_approve_at = "N/A";
          if(data.ceo_note) var ceo_note = data.ceo_note
          else var ceo_note = "N/A";
          
          var cancel_tr = ``;
          if(data.canceled_at) {
            var canceled_at = moment(data.canceled_at).format('D-MM-YYYY, h:mm:ss a');
            
            var cancel_tr = `
            <tr>
              <td>Canceled By `+data.canceled_by+`</td><td>`+canceled_at+`</td> <td>`+data.canceled_note+`</td>
            </tr>
            `
          }
          
          $("#review").html(
            `
              <tr>
                <td>Employee Dept. Head</td><td>`+issuer_dpt_approve_at+`</td> <td>`+issuer_dpt_head_note+`</td>
              </tr>
              <tr>
                <td>ICT Dept. Head</td><td>`+ict_dpt_approve_at+`</td> <td>`+ict_head_note+`</td>
              </tr>
              <tr>
                <td>CEO</td><td>`+ceo_approve_at+`</td> <td>`+ceo_note+`</td>
              </tr>
            `+cancel_tr
          );
          
          $("#assessmentView").modal('show');
        },
    });
});

