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
    var is_manager_checked = document.getElementById(`id_workflow_set-${counter}-is_manager`).checked;
    return is_manager_checked;
}

// disable position and employee by: amira date: 20/4/2021
function disable_position_employee(position, employee){
    position.disabled = true;
    employee.disabled = true;
}

// enable position and employee by: amira date: 20/4/2021
function enable_position_employee(position, employee){
    position.disabled = false;
    employee.disabled = false;
    position.required = true;
}

// check manager to disable position, employee by: amira date: 20/4/2021
function change_position_employee_elements(counter=0){

    var is_manager = check_manager_value(counter=counter);
    var position = document.getElementById(`id_workflow_set-${counter}-position`);
    var employee = document.getElementById(`id_workflow_set-${counter}-employee`);
    if(is_manager){
        disable_position_employee(position, employee);
    }else{
        enable_position_employee(position, employee);
    }

}

// document ready disable if manager is true by: amira date: 20/4/2021
$(document).ready(function() {
     change_position_employee_elements();
//     disable_add_seq_button("id_workflow_set-0-operation_options");
});


// add sequence on click
$('#add_seq').click(function() {
    var form_idx = $('#id_workflow_set-TOTAL_FORMS').val();
    $('#batch_form_set').append($('#empty_form').html().replace(/__prefix__/g, form_idx));

    // check on click by: amira date: 20/4/2021
    change_position_employee_elements(counter=form_idx);

    $('#id_workflow_set-TOTAL_FORMS').val(parseInt(form_idx) + 1);
//    $('#add_seq').attr('disabled', true); // disable button after adding new form set by: amira date: 21/4/2021
 });

// // disable button if operation option value not and or or by: amira date: 21/4/2021
// function disable_add_seq_button(operation_id){
//    var option_value = document.getElementById(`${operation_id}`).value;
//    if(option_value != 'or' && option_value != 'and' ){
//        $('#add_seq').attr('disabled', true);
//    }else{
//        $('#add_seq').attr('disabled', false);
//    }
// }
//
//// every time operation options is changed it checks to disable or enable button by: amira date: 21/4/2021
//function change_and_or_value(object){
//    disable_add_seq_button(object.id);
// }


// slice id sequence number by: amira date: 21/4/2021
function slice_counter(element_id){
    counter_start = element_id.indexOf('-') + 1;
    counter_end = element_id.lastIndexOf('-');
    counter = element_id.slice(counter_start, counter_end);
    return counter;
}


// fires on is manager change by: amira date: 21/4/2021
function change_is_manager_value(object){
    counter = slice_counter(object.id);
    change_position_employee_elements(counter=counter);
}


// get is notify element by: amira date: 22/4/2021
function get_is_notify(counter){
    var is_notify = document.getElementById(`id_workflow_set-${counter}-is_notify`);
    return is_notify;
}

// enable is notify  by: amira date: 22/4/2021
function enable_is_notify(counter){
    var is_notify = get_is_notify(counter);
    is_notify.disabled = false;
}

// enable is notify  by: amira date: 22/4/2021
function dim_is_notify(counter){
    var is_notify = get_is_notify(counter);
    is_notify.disabled = true;
}

// get is action element by: amira date: 22/4/2021
function get_is_action(counter){
    var is_action = document.getElementById(`id_workflow_set-${counter}-is_action`);
    return is_action;
}

// enable is action  by: amira date: 22/4/2021
function enable_is_action(counter){
    var is_action = get_is_action(counter);
    is_action.disabled = false;
}

// enable is action  by: amira date: 22/4/2021
function dim_is_action(counter){
    var is_action = get_is_action(counter);
    is_action.disabled = true;
}


// on choose action disable notify by: amira date: 22/4/2021
function change_is_action(object){
    counter = slice_counter(object.id)
    if(object.checked){
        dim_is_notify(counter)
    }else{
        enable_is_notify(counter)
    }
}

// on choose action disable action by: amira date: 22/4/2021
function change_is_notify(object){
    console.log(object.id)
    counter = slice_counter(object.id)
    if(object.checked){
        dim_is_action(counter)
    }else{
        enable_is_action(counter)
    }


}

// when choosing notify disable action condition by: amira date: 22/4/2021
function disable_action_condition(){

}






