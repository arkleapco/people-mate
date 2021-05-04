  isDirty = true
  x = false
  console.log(isDirty)
  document.getElementById("myform").onchange = function() {myFunction()};

 function myFunction() {
   x= true
 }

  function change_x()
  {isDirty = false
 console.log(isDirty)}

  window.onbeforeunload = function () {
             if (isDirty && x ) {
                 return "There are unsaved data.";
                 console.log(isDirty)
             }
             return undefined;
         }

var total_balance = $('#balance-data').attr("total-balance-data");
var absence_days = $('#balance-data').attr('#absence-days-data');


function get_leave_type_value(){
console.log('inside leave type value')
  leave_type_id = $('#id_leavetype').val()
  var leave_days_val;
  var url = $('#leave-type-id').attr("leave-type-data-url")
  $.ajax({
    type: 'get',
    url: url,
    async: false,
    dataType : "json",
    contentType: "application/json",
    data: {'leave_id': leave_type_id},
    success: function(result){
      console.log('success: ', result.leave_value)
      leave_days_val = result.leave_value
    },
    error: function(result){
      console.log('error')
    }
  })
  return leave_days_val
}

function calculate_days(){
    var start_date = new Date($('#id_startdate').val());
    var end_date = new Date($('#id_enddate').val());
    var end_start_dates_difference = end_date.getTime() - start_date.getTime();
    var diff_days = Math.ceil(end_start_dates_difference / (1000 * 3600 * 24));
    return diff_days
}

function eligible_user_leave(){
    var have_balance;
    var diff_days = calculate_days();


    if(diff_days > total_balance){
        console.log('your requested leaves are more than your total balance');
        have_balance = false;
    }else{
        console.log('horay have a nice leave ;)');
        have_balance = true;
    }
    return have_balance
}

function draw_modal(){
//    $('#exampleModal').modal('hide')
    var diff_days = calculate_days();
    var absence = diff_days - total_balance;
    var list_leave_url = $('#balance-data').attr("list-leave-url-data");

    console.log('absence ', absence)
    var modal_body = `
        <div class="modal fade" id="exampleModal" tabindex="-1" role="dialog" aria-labelledby="exampleModalLabel" aria-hidden="true">
          <div class="modal-dialog" role="document">
            <div class="modal-content">
              <div class="modal-header">
                <h5 class="modal-title text-warning" id="exampleModalLabel">Leaves Warning</h5>
                <button type="button" class="close" data-dismiss="modal" aria-label="Close">
                  <span aria-hidden="true">&times;</span>
                </button>
              </div>
              <div class="modal-body">
                <p><b>Your Balance: </b>${total_balance} days</p>
                <p><b>Your Request: </b>${diff_days} days</p>
                <p><b>Your Absence will be: </b>${absence} days</p>
                <h3 class="text-primary">Do you want to proceed your leave request?</h3>
              </div>
              <div class="modal-footer">
                <button type="button" class="btn btn-outline-secondary" data-dismiss="modal">Yes😌</button>
                <a href=${list_leave_url} type="button" class="btn btn-outline-primary">No😯</a>
              </div>
            </div>
          </div>
        </div>
       </div>
    `

    $('body').append(modal_body)
    $('#exampleModal').modal('show')

}




function change_end_date(){

    var have_balance;
    var leave_value = get_leave_type_value()

    if(leave_value > 0){
        have_balance = eligible_user_leave()
        if(have_balance == false){
            draw_modal()
        }
    }

}