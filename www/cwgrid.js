$('ready', init_cw);

var focus_fired = false;
var active_words = [];

function init_cw() {
    var inputs = $('#grid').find('input');

    inputs.bind('focus', function(e) {
	    var current_square = $(this);
	    focus_fired = true;
	});

    inputs.bind('mousedown', function(e) {
	    focus_fired = false;
	});
    
    inputs.bind('mouseup', function(e) {
	    var current_square = $(this);
	    val = current_square.attr("value");
	    id = current_square.attr("id");
	    rc = id.match(/col-(\d+)\-(\d+)/);
	    sym_square = $('#col-' + (16-rc[1]) + '-' + (16-rc[2]));
	    if(val == "x") {
		current_square.attr("value", "");
		current_square.attr("style", "background-color: white");
		if(sym_square != current_square) {
		    sym_square.attr("value", "");
		    sym_square.attr("style", "background-color: white");
		}
	    } else {
		current_square.attr("value", "x");
		current_square.attr("style", "background-color: black");
		if(sym_square != current_square) {
		    sym_square.attr("value", "x");
		    sym_square.attr("style", "background-color: black");
		}
	    }		
	});

    inputs.bind('keyup', function(e) {
	    var key = e.keyCode || e.charCode;
	});

    function is_letter(key) {
	return (64 < key && key < 91) || (96 < key && key < 123) || key == 32;
    }
    

    $('#usegrid').bind('click', function(e) {
	    var form = $(this).closest('form');
	    form.attr('action','/usegrid/');
	    form.attr('target','_self');
	    form.submit();
	});

}

