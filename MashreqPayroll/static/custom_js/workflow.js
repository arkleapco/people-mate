// check if form change or not empty when click back
isDirty = true
x = false
//console.log(isDirty)
document.getElementById("myform").onchange = function() {myFunction()};

function myFunction() {
    x= true
}

function change_x(){
    isDirty = false
//    console.log(isDirty)
}

window.onbeforeunload = function () {
     if (isDirty && x ) {
         return "There are unsaved data.";
//         console.log(isDirty)
     }
     return undefined;
 }

// check manager_value by: amira date: 20/4/2021
function check_manager_value(counter){
    var is_manager_checked = document.getElementById(`id_workflow_set-${counter}-is_manager`).checked
    return is_manager_checked
}

// disable position and employee by: amira date: 20/4/2021
function disable_position_employee(position, employee){
    position.disabled = true
    employee.disabled = true
}

// enable position and employee by: amira date: 20/4/2021
function enable_position_employee(position, employee){
    position.disabled = false
    employee.disabled = false
}

// check manager to disable position, employee by: amira date: 20/4/2021
function change_position_employee_elements(counter=0){

    var is_manager = check_manager_value(counter=counter)
    var position = document.getElementById(`id_workflow_set-${counter}-position`)
    var employee = document.getElementById(`id_workflow_set-${counter}-employee`)
    if(is_manager){
        disable_position_employee(position, employee)
    }else{
        enable_position_employee(position, employee)
    }

}

// document ready disable if manager is true by: amira date: 20/4/2021
$(document).ready(function() {
     change_position_employee_elements()
});


// add sequence on click
$('#add_seq').click(function() {
    var form_idx = $('#id_workflow_set-TOTAL_FORMS').val();
    $('#batch_form_set').append($('#empty_form').html().replace(/__prefix__/g, form_idx));

    // check on click by: amira date: 20/4/2021
    change_position_employee_elements(counter=form_idx)

    $('#id_workflow_set-TOTAL_FORMS').val(parseInt(form_idx) + 1);
 });


// slice id sequence number by: amira date: 21/4/2021
function slice_counter(manager_id){
    counter_start = manager_id.indexOf('-') + 1
    counter_end = manager_id.lastIndexOf('-')
    counter = manager_id.slice(counter_start, counter_end)
    return counter
}


// fires on is manager change by: amira date: 21/4/2021
function change_is_manager_value(object){
    counter = slice_counter(object.id)
    change_position_employee_elements(counter=counter)
}




