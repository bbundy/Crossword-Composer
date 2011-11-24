$('ready', init_cw);
//$('ready', load_from_cookie);

var focus_fired = false;
var active_words = [];

function init_cw() {
    var inputs = $('#grid').find('input');
    var all_words = $('#grid div');

    inputs.bind('focus', function(e) {
	    var current_letter = $(this);
	    focus_fired = true;
	    if (!in_active_word(current_letter)) {
		var intersecting_letter = getIntersectingLetter(current_letter);
		this.select();
		activate_word(current_letter);
	    }
	});

    function in_active_word(letter) {
	var in_active = false;
	var this_word = letter.closest('div');
	$.each(active_words, function() {
		if (this_word.attr('id') === this.attr('id')) {
		    in_active = true;
		}
	    });
	return in_active;
    }

    function is_first_letter(letter) {
	return letter.closest('div').find('input:first').attr('id') === letter.attr('id');
    }

    inputs.bind('mousedown', function(e) {
	    focus_fired = false;
	});
    
    inputs.bind('mouseup', function(e) {
	    var current_letter = $(this);
	    var word = current_letter.closest('div');
	    var intersecting_letter = getIntersectingLetter(current_letter);
	    if (intersecting_letter && !focus_fired) {
		intersecting_letter.focus();
	    }
	});

    inputs.bind('keyup', function(e) {
	    var key = e.keyCode || e.charCode;
	    if (is_letter(key)) {
		$(e.target).val(String.fromCharCode(key).toLowerCase());
		copyChangeToIntersectingLetter($(e.target));
		focusOnNextInput($(e.target));
	    }
	});

    function is_letter(key) {
	return (64 < key && key < 91) || (96 < key && key < 123) || key == 32;
    }
    
    inputs.bind('keydown', 'tab', function(e) {
	    if ($(e.target).closest('div').nextAll('div:first')) {
		$(e.target).closest('div').nextAll('div:first').find('input:first').focus();
	    }
	    return false;
	});
    inputs.bind('keydown', 'Shift+tab', function(e) {
	    if ($(e.target).closest('div').prevAll('div:first')) {
		$(e.target).closest('div').prevAll('div:first').find('input:first').focus();
	    }
	    return false;
	});
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
    inputs.bind('keyup', 'backspace', function(e) {
	    copyChangeToIntersectingLetter($(e.target));
	    focusOnPreviousInput($(e.target));
	});
    inputs.bind('keyup', 'del', function(e) {
	    copyChangeToIntersectingLetter($(e.target));
	    return false;
	});
    inputs.bind('keydown', 'esc', function(e) {
	    copyChangeToIntersectingLetter($(e.target));
	    return false;
	});

    function move_back(e, direction) {
	var letter = $(e.target);
	if (letter.attr('id').indexOf(direction) !== -1) {
	    focusOnPreviousInput(letter);
	} else {
	    if (getIntersectingLetter(letter)) {
		focusOnPreviousInput(getIntersectingLetter(letter));
	    }
	}
    }
    function move_forward(e, direction) {
	var letter = $(e.target);
	if (letter.attr('id').indexOf(direction) !== -1) {
	    focusOnNextInput(letter);
	} else {
	    if (getIntersectingLetter(letter)) {
		focusOnNextInput(getIntersectingLetter(letter));
	    }
	}
    }
    
    $('label').bind('click', function(e) {
	    if (has_numbers && !text_is_highlighted()) {
		word = $('#' + $(e.target).closest('label').attr('for'));
		activate_word(word);
		word.find('input:first').focus();
		return false;
	    }
	});
    
    function text_is_highlighted() {
	return (selection() && selection().toString() != '') || (range() && range().text != '')
	    }

    function do_save(req_change) {
	$("#word-suggestions").empty();
	var form_values = $('form').serialize();
	var saved_state = form_values.replace(/(\d+)-across-(\d+)=/g, '$1a$2').replace(/(\d+)-down-(\d+)=/g, '$1d$2').replace(/(\d+)-across-input=/g, '$1ai').replace(/(\d+)-down-input=/g, '$1di');
	$.cookie('crossword', saved_state, { expires: 365 });
	if (window.XMLHttpRequest) {
	    req = new XMLHttpRequest();
	    if (req_change) {
		req.onreadystatechange = req_change;
	    }
	    req.open("POST", "/save/", true);
	    req.setRequestHeader("Content-type","application/x-www-form-urlencoded");
	    req.send(form_values);
	}	
    }


    $('#update-clue').bind('click', function(e) {
	    var clue = $('#active-clue-edit').find('input:first').attr('value');
	    clue_for(active_words[0]).empty();
	    clue_for(active_words[0]).append(clue);
	    input_for(active_words[0]).attr('value', clue);
	    $(active_words[0]).find('input:first').focus();
	});    

    $('#save').bind('click', function(e) {
	    do_save(saveReqChange);
	});
    
    $('#clear').bind('click', function(e) {
	    deleteAllCookies();
	    window.location='/';
	});
    
    $('#retrieve').bind('click', function(e) {
	    var form = $(this).closest('form');
	    form.attr('action','/retrieve/');
	    form.attr('target','_self');
	    form.submit();
	});

    $('#solve').bind('click', function(e) {
	    var form = $(this).closest('form');
	    form.attr('action','/solve/');
	    form.attr('target','_self');
	    form.submit();
	});

    $('#show').bind('click', function(e) {
	    var form = $(this).closest('form');
	    $("#buttons-horizontal").empty();
	    form.attr('action','/retrieve/');
	    form.attr('target','_self');
	    form.submit();
	});

    $('#rankedwords').bind('click', function(e) {
	    $("#word-suggestions").empty();
	    $("#buttons-horizontal").hide();
	    if (active_words[0]) {
		active = $(active_words[0]).find('input:first').attr('id');
		$("#word-suggestions").append('<input id="active" name="active" type="hidden" value="' + active + '">');
		var form = $(this).closest('form');
		loadXMLPost('/rankedwords/', form.serialize());
	    }
	});

    $('#words').bind('click', function(e) {
	    $("#word-suggestions").empty();
	    $("#buttons-horizontal").hide();
	    var pattern = get_pattern(active_words[0].find('input'));
	    loadXMLDoc('/words/?pattern=' + pattern);
	});

    $('#print').bind('click', function(e) {
	    do_save(null);
	    var form = $(this).closest('form');
	    form.attr('action','/print/');
	    form.attr('target','_blank');
	    form.submit();
	});

    $('#printall').bind('click', function(e) {
	    do_save(null);
	    var form = $(this).closest('form');
	    $("#buttons-horizontal").append('<input id="printall" name="printall" type="hidden" value="true">');
	    form.attr('action','/print/');
	    form.attr('target','_blank');
	    form.submit();
	});

    $('#toxpf').bind('click', function(e) {
	    var form = $(this).closest('form');
	    $("#word-suggestions").empty();
	    form.attr('action','/toxpf/');
	    form.attr('target','_blank');
	    form.submit();
	});

    $('#doc').bind('click', function(e) {
	    do_save(null);
	    var form = $(this).closest('form');
	    form.attr('action','/doc/');
	    form.attr('target','_blank');
	    form.submit();
	});

    $('#gridedit').bind('click', function(e) {
	    var form = $(this).closest('form');
	    form.attr('action','/gridedit/');
	    form.attr('target','_blank');
	    form.submit();
	});

    $('#newus').bind('click', function(e) {
	    deleteAllCookies();
	    window.location='/newus/';
	});

    $('#newcryptic').bind('click', function(e) {
	    deleteAllCookies();
	    window.location='/newcryptic/';
	});

    $('#fromxpf').bind('click', function(e) {
	    deleteAllCookies();
	    $("#file-load").append('<br><input id="xpfurl" name="xpfurl" type=text" size=100 value=""/> <input id="xpf-load-submit" type=button value="Load XPF"/>');
	    $('#xpf-load-submit').bind('click', function(e) {
		    var form = $(this).closest('form');
		    form.attr('action','/fromxpf/');
		    form.attr('target','_blank');
		    form.submit();
		});
	});

    $('#frompuz').bind('click', function(e) {
	    deleteAllCookies();
	    $("#file-load").append('<br><input id="puzurl" name="puzurl" type=text" size=100 value=""/> <input id="puz-load-submit" type=button value="Load PUZ"/>');
	    $('#puz-load-submit').bind('click', function(e) {
		    var form = $(this).closest('form');
		    form.attr('action','/frompuz/');
		    form.attr('target','_blank');
		    form.submit();
		});
	});

    $('#active-clue-edit:not(.no-number)').hide();    
    $('#word-suggestions').hide();    

    $('#active-clue-edit:not(.no-number)').bind('keyup', function(e) {
	    if (e.keyCode === 13) {
		var clue = $('#active-clue-edit').find('input:first').attr('value');
		clue_for(active_words[0]).empty();
		clue_for(active_words[0]).append(clue);
		input_for(active_words[0]).attr('value', clue);
		$(active_words[0]).find('input:first').focus();
	    }
	});
}

function deleteAllCookies() {
    $.cookie('crossword', '', {expires: "Thu, 01 Jan 1970 00:00:00 GMT"})
}

function load_from_cookie() {
    var saved_state = $.cookie('crossword');
    if (saved_state) {
	saved_state=decodeURIComponent(saved_state);
	var form_values = saved_state.replace(/(\d+)a(\d+)/g, '$1-across-$2=').replace(/(\d+)d(\d+)/g, '$1-down-$2=').replace(/(\d+)ai/g, '$1-across-input=').replace(/(\d+)di/g, '$1-down-input=');
	$(form_values.split('&')).each(function(index, pair) {
		var name_value = pair.split('=');
		if (name_value[0].indexOf('input') > 0) {
		    val = decodeURI(name_value[1]).replace(/\+/g, ' ');
		    $('#' + name_value[0]).attr('value', val);
		    var clue = name_value[0].replace('input', 'clue');
		    $('#' + clue).empty();
		    $('#' + clue).append(val);
		} else {
		    $('#' + name_value[0]).val(name_value[1]);
		}
	    });
    }
}

function selection() {
    if (window.getSelection) {
	return window.getSelection();
    }
}

function range() {
    if (document.selection) {
	return document.selection.createRange();
    }
}

function focusOnNextInput(element) {
    var nextClue = element.parent().next();
    if(nextClue && nextClue.length > 0) {
	nextClue.find('input').focus();
    } else {
	var word = element.closest('div');
	var this_word_was_last_word = false;
	$.each(active_words, function() {
		if (this_word_was_last_word) {
		    this.find('input:first').focus();
		}
		if (this.attr('id') === word.attr('id')) {
		    this_word_was_last_word = true;
		    $('#active-clue-edit').find('input:first').get(0).setSelectionRange(0,0);
		    $('#active-clue-edit').find('input:first').focus();
		} else {
		    this_word_was_last_word = false;
		}
	    });
    }
}

function focusOnPreviousInput(element) {
    var previousClue = element.parent().prev();
    if(previousClue) {
	previousClue.find('input').focus();
    }
}

function getIntersectingLetter(letter) {
    if(intersections[letter.attr('id')]) {
	return $('#' + intersections[letter.attr('id')]);
    }
    return null;
}


function copyChangeToIntersectingLetter(letter) {
    var intersect = getIntersectingLetter(letter);
    if (intersect) {
	intersect.val(letter.val());
    }
}

function clue_for(word) {
    return $('#' + word.attr('id') + '-clue');
}

function input_for(word) {
    return $('#' + word.attr('id') + '-input');
}

function activate_word(letter) {
    $.each(active_words, deactivate_word);
    active_words = words_for_letter(letter);
    $.each(active_words, function() {
	    this.css("z-index","999");
	    this.addClass('active');
	    if (has_numbers) {
		clue_for(this).addClass('active');
	    }
	});
    $('#active-clue:not(.no-number)').append(clue_for(active_words[0]).contents().clone());
    $('#active-clue-edit:not(.no-number)').find('input:first').attr('value', clue_for(active_words[0]).text());
    $('#active-clue-edit:not(.no-number)').show();    
}

function words_for_letter(letter) {
    var word = letter.closest('div');
    words = words_for_clue[word.attr('id')]
	if (words) {
	    the_words = $.map(words, function(id) { return $('#' + id); });
	} else {
	    the_words = [word]
		}
    return the_words
	}

function deactivate_word() {
    this.removeClass('active');
    var clueNum = this.find('span').text();
    this.css("z-index", clueNum);
    $('#' + this.attr('id') + '-clue').removeClass('active');
    $('#active-clue').empty();
    $('#active-clue-edit:not(.no-number)').find('input:first').attr('value', '');
    $('#active-clue-edit:not(.no-number)').hide();    
    $("#word-suggestions").empty();
    $("#word-suggestions").hide();
}

function get_pattern(inputs) {
    var pattern = '';
    inputs.each(function() {
	    var square = $(this);
	    if (square.val() === '' || square.val() === ' ') {
		pattern = pattern.concat('0');
	    } else {
		pattern = pattern.concat(square.val());
	    }
	});
    return pattern;
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

function loadXMLPost(url, body) 
{
    if (window.XMLHttpRequest) {
        req = new XMLHttpRequest();
        req.onreadystatechange = processReqChange;
        req.open("POST", url, true);
        req.send(body);
    }
}

function processReqChange() 
{
    // only if req shows "complete"
    if (req.readyState == 4) {
        // only if "OK"
        if (req.status == 200) {
	    var words = req.response.split('&');
	    $("#word-suggestions").empty();
	    if(words[0] == "toomanymatches") {
		alert("Too many words match this query. Try working on a part of the puzzle with longer words or more filled squares\n");
	    } else {
		for (i=0; i<words.length; i++) {
		    $("#word-suggestions").append('<input id="iw' + i + '" type=button value="' + words[i] + '"/>');
		    $('#iw' + i).bind('click', function(e) {
			    set_word(active_words[0].find('input'), $(e.target).attr('value'));
			});
		}
	    }
	    $("#word-suggestions").show();
        } else {
            alert("There was a problem retrieving the XML data:\n" + req.statusText);
        }
	$("#buttons-horizontal").show();
    }
}

function saveReqChange()
{
    // only if req shows "complete"
    if (req.readyState == 4) {
        // only if "OK"
        if (req.status == 200) {
	    var form = $(this).closest('form');
	    form.attr('action','/retrieve/');
	    form.attr('target','_self');
	    form.submit();
        } else {
            alert("There was a problem saving your puzzle:\n" + req.statusText);
        }
    }
}
