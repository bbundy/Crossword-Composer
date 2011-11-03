$('ready', init_cw);

var focus_fired = false;
var active_words = [];
var numsq = 7;

function init_cw() {
    var inputs = $('#grid').find('input');

    populate_buttons()
    inputs.bind('keyup', function(e) {
	    var key = e.keyCode || e.charCode;
	    if (is_letter(key)) {
		$(e.target).val(String.fromCharCode(key).toLowerCase());
	    }
	});

    function is_letter(key) {
	return (64 < key && key < 91) || (96 < key && key < 123) || key == 32;
    }
    
    inputs.bind('keyup', 'left', function(e) {
	    move_back(e, 'across');
	    return false;
	});
    inputs.bind('keyup', 'up', function(e) {
	    move_back(e, 'down');
	    return false;
	});
    inputs.bind('keyup', 'right', function(e) {
	    move_forward(e, 'across');
	    return false;
	});
    inputs.bind('keyup', 'down', function(e) {
	    move_forward(e, 'down');
	    return false;
	});

    $('#lookup').bind('click', function(e) {
	    var inp = $('#grid').find('input');
	    var pattern = get_pattern(inp);
	    $("#word-suggestions").empty();
	    loadXMLDoc('/words/?pattern=' + pattern);
	});
	
    $('#addsq').bind('click', function(e) {
	    numsq += 1;
	    populate_buttons()
	});

    $('#subsq').bind('click', function(e) {
	    numsq -= 1;
	    populate_buttons()
	});
}

function populate_buttons() {
    $("#1-across").empty();
    for (i = 0; i < numsq; i++) {
	$("#1-across").append('<li><input id="l' + i + '" name="l' + i + '" maxlength="1" class=" "/></li>');
    }
}


function get_pattern(inputs) {
    var pattern = '';
    inputs.each(function() {
	    var square = $(this);
	    if (square.val() === '') {
		pattern = pattern.concat('0');
	    } else {
		pattern = pattern.concat(square.val());
	    }
	});
    return pattern.toLowerCase();
}

function set_word(inputs, word) {
    var idx = 0;
    word = word.replace(/[ \-]+/g, '').toLowerCase();
    inputs.each(function() {
	    var square = $(this);
	    square.val(word.substr(idx,1));
	    copyChangeToIntersectingLetter($(this));
	    idx = idx + 1;
	});
}

function loadXMLDoc(url) 
{
    if (window.XMLHttpRequest) {
        req = new XMLHttpRequest();
        req.onreadystatechange = processReqChange;
        req.open("GET", url, true);
        req.send(null);
    }
}

function processReqChange() 
{
    // only if req shows "complete"
    if (req.readyState == 4) {
        // only if "OK"
        if (req.status == 200) {
	    var words = req.response.split('&');
	    alert("response:\n" + req.response);
	    $("#word-suggestions").empty();
	    for (i=0; i<words.length; i++) {
		$("#word-suggestions").append('<input id="iw' + i + '" type=button value="' + words[i] + '" />');
		$('#iw' + i).bind('click', function(e) {
			window.location='http://google.com/search?q=' + $(e.target).attr('value');
		});
	    }
	    $("#word-suggestions").show();
        } else {
            alert("There was a problem retrieving the XML data:\n" + req.statusText);
        }
    }
    alert("response:\n" + req.readyState);
}
