function is_payslip_created(){
  is_payslip_created = false;

  salary_month = $('#id_salary_month').val()
  salary_year = $('#id_salary_year').val()
  assignment_batch = $('#id_assignment_batch').val()
  var is_payslip_created;
  var url = $('#myform').attr("validate-payslip-data-url")
  $.ajax({
    type: 'get',
    async:false,
    url: url,
    dataType : "json",
    contentType: "application/json",
    data: {
      'assignment_batch': assignment_batch,
      'salary_month': salary_month,
      'salary_year': salary_year
    },
    success: function(result){
      console.log('success: ', result.payslip_created)
      is_payslip_created = result.payslip_created
    },
    error: function(result){
      console.log('error')
    }
  })
  return is_payslip_created;
}


function submit_payslip_form(e) {
  e.preventDefault()

  is_payslip_created = is_payslip_created();
  console.log('validate_payslip: ', is_payslip_created)


  if (is_payslip_created) {
    console.log('From if')
    $("#delete-payslip-modal").modal('show');
  }
  else {
    console.log('From else')
    // var url = $('#myform').attr("validate-payslip-data-url")
    // var dataString = '&salary_month=' + $('input[name=id_salary_month]').val() +
    //                  '&salary_year=' + $('input[name=id_salary_year]').val() +
    // $.ajax({
    //     type: "POST",
    //     url: url,
    //     data: dataString,
    //     success: function(data) {
    //         alert(data);
    //     }
    //  });
    //  return false;
  }
}
