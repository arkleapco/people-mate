function is_payslip_created(){
  payslip_created_bool = false;

  data = {
    'assignment_batch': $('#id_assignment_batch').val(),
    'salary_month': $('#id_salary_month').val(),
    'salary_year': $('#id_salary_year').val(),
  }
  var payslip_created_bool;
  var url = $('#myform').attr("validate-payslip-data-url")
  $.ajax({
    type: 'get',
    async:false,
    url: url,
    dataType : "json",
    contentType: "application/json",
    data: data,
    success: function(result){
      console.log('success: ', result.payslip_created)
      payslip_created_bool = result.payslip_created
    },
    error: function(result){
      console.log('error')
    }
  })
  return payslip_created_bool;
}


function submit_payslip_form(e) {
  payslip_created_bool = is_payslip_created();

  if (payslip_created_bool) {
    e.preventDefault()
    $("#delete-payslip-modal").modal('show');
  }
}

function delete_confrimed(){
  deleted = false
  data = {
    'assignment_batch': $('#id_assignment_batch').val(),
    'salary_month': $('#id_salary_month').val(),
    'salary_year': $('#id_salary_year').val(),
    'elements_type_to_run': $('#id_elements_type_to_run').val()
  }
  var url = $('#myform').attr("delete-payslip-data-url")
  $.ajax({
    type: 'get',
    async:false,
    url: url,
    dataType : "json",
    contentType: "application/json",
    data: data,
    success: function(result){
      deleted = result.deleted
    },
    error: function(jqXHR, exception){
      console.log('error')
      console.log(jqXHR.status)
      console.log(exception)
    }
  })
  $("#delete-payslip-modal").modal('hide');
}
