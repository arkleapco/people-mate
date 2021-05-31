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

// get manager object by: amira date: 25/4/2021
function get_manager(counter){
    var manager = document.getElementById(`id_workflow_set-${counter}-is_manager`)
    return manager
}


// check manager_value by: amira date: 20/4/2021
function check_manager_value(counter){
    var manager = get_manager(counter)
    var is_manager_checked = manager.checked;
    return is_manager_checked;
}

// disable position and employee by: amira date: 20/4/2021
function disable_position_employee(position, employee){
    if(position.value || employee.value){
        position.value = ""
        employee.value = ""
    }
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
    is_notify.checked = true;
}

// enable is notify  by: amira date: 22/4/2021
function dim_is_notify(counter){
    var is_notify = get_is_notify(counter);
    is_notify.checked = false;
}

// get is action element by: amira date: 22/4/2021
function get_is_action(counter){
    var is_action = document.getElementById(`id_workflow_set-${counter}-is_action`);
    return is_action;
}

// enable is action  by: amira date: 22/4/2021
function enable_is_action(counter){
    var is_action = get_is_action(counter);
    is_action.checked = true;
}

// enable is action  by: amira date: 22/4/2021
function dim_is_action(counter){
    var is_action = get_is_action(counter);
    // if(is_action.checked){
    //     is_action.checked = false;
    // }
    // is_action.disabled = true;
    is_action.checked = false
}


// on choose action disable notify by: amira date: 22/4/2021
function change_is_action(object){
    counter = slice_counter(object.id)
    if(object.checked){
        dim_is_notify(counter)
        enable_action_condition(counter)
    }else{
        enable_is_notify(counter)
        disable_action_condition(counter)
    }
}

// on choose notify disable action by: amira date: 22/4/2021
function change_is_notify(object){
    counter = slice_counter(object.id)
    if(object.checked){
        dim_is_action(counter)
        disable_action_condition(counter)
    }else{
        enable_is_action(counter)
//        enable_action_condition(counter)
    }
}

// get action condition options by: amira date: 25/4/2021
function get_action_condition(counter){
    var action_condition = document.getElementById(`id_workflow_set-${counter}-operation_options`);
    return action_condition
}

// when choosing notify disable action condition by: amira date: 22/4/2021
function disable_action_condition(counter){
    action_condition = get_action_condition(counter)
    action_condition.disabled = false;
}


// when choosing notify disable action condition by: amira date: 22/4/2021
function enable_action_condition(counter){
    action_condition = get_action_condition(counter)
    action_condition.disabled = false;
}


//disable manager by:amira date:25/4/2021
function disable_manager(counter){
    var manager = get_manager(counter)
    if(manager.checked){
        manager.checked = false;
    }
    manager.disabled = true;
}

//enable manager by:amira date:25/4/2021
function enable_manager(counter){
    var manager = get_manager(counter)
    manager.disabled = false;
}

//send ajax to get employees by: amira date:25/4/2021
function send_ajax_get_employees(url, position_id, counter){
    $.ajax({
        url: url,
        data: {
            'position': position_id
        },
        success: function(result){
            $(`#id_workflow_set-${counter}-employee`).html(result);
        },
        error: function(result){
            console.log('error occurred')
        }
    });

}


// load employees ajax by: amira date: 22/4/2021
function select_position_employees(object){

    var url = $('#myform').attr('data-employees-url');
    var position_id = object.value;
    var counter = slice_counter(object.id)

    if(position_id){
        disable_manager(counter)
        send_ajax_get_employees(url, position_id, counter)
    }else{
        enable_manager(counter)
    }
};






