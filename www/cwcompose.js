$('ready', init_cw);

var focus_fired = false;
var active_words = [];
var active_tab = 'file';
var fill_type = 0;

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
		if (active_tab != 'word') {
		    setActionTab('word');
		}
		$(e.target).val(String.fromCharCode(key).toLowerCase());
		copyChangeToIntersectingLetter($(e.target));
		focusOnNextInput($(e.target));
		adjust_find_define()
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
	    adjust_find_define();
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
	return (selection() && selection().toString() != '') || (range() && range().text != '');
    }

    function adjust_find_define() {
	var pattern = get_pattern(active_words[0].find('input'));
	if (pattern.indexOf("0") == -1) {
	    $('#definition').show();
	    $('#examples').show();
	    $('#clues').show();
	    $('#rankedwords').hide();
	    $('#pubwords').hide();
	    $('#listwords').hide();
	} else {
	    $('#definition').hide();
	    $('#examples').hide();
	    $('#clues').hide();
	    $('#rankedwords').show();
	    $('#pubwords').show();
	    $('#listwords').show();
	}
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
	    $('#clue-intro').hide();
	});    

    $('#save').bind('click', function(e) {
	    do_save(saveReqChange);
	    $("#save-progress").show();
	});
    
    $('#clear').bind('click', function(e) {
	    deleteAllCookies();
	    window.location='/';
	});
    
    $('#auto-clue').bind('click', function(e) {
	var form = $(this).closest('form');
	$("#auto-clue").hide();
	loadXMLPost('/autoclue/', form.serialize(), clueReqChange);
	});
    
    $('#clearwd').bind('click', function(e) {
	var acted = false;
	$("#word-intro").hide();
	inputs = active_words[0].find('input');
	input_for(active_words[0]).attr('value', '');
	clue_for(active_words[0]).empty();
	$.each(inputs, function() {
	    var letter = $(this);
	    var intersecting_letter = getIntersectingLetter(letter);
	    var intersecting_word = words_for_letter(intersecting_letter);
	    var pattern = get_pattern(intersecting_word[0].find('input'));
	    if (pattern.indexOf("0") != -1 && letter.attr('value') != '') {
		input_for(intersecting_word[0]).attr('value', '');
		clue_for(intersecting_word[0]).empty();
		letter.attr('value', '');
		intersecting_letter.attr('value', '');
		acted = true;
	    }
	});
	if (!acted) {
	    $.each(inputs, function() {
		var letter = $(this);
		var intersecting_letter = getIntersectingLetter(letter);
		var intersecting_word = words_for_letter(intersecting_letter);
		var pattern = get_pattern(intersecting_word[0].find('input'));
		input_for(intersecting_word[0]).attr('value', '');
		clue_for(intersecting_word[0]).empty();
		letter.attr('value', '');
		intersecting_letter.attr('value', '');
	    });
	}
	inputs[0].focus();
	adjust_find_define();
	});
    
    $('#revwd').bind('click', function(e) {
	var i = 0;
	inputs = active_words[0].find('input');
	ans = solutions[active_words[0].attr('id')];
	$.each(inputs, function() {
	    var letter = $(this);
	    var intersecting_letter = getIntersectingLetter(letter);
	    var intersecting_word = words_for_letter(intersecting_letter);
	    var letr = ans.substring(i, i+1);
	    letter.attr('value', letr);
	    intersecting_letter.attr('value', letr);
	    i += 1;
	});
	inputs[0].focus();
	adjust_find_define();
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
	    form.attr('target','_blank');
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
	    $("#word-intro").hide();
	    $("#word-suggestions").empty();
	    $("#buttons-horizontal").hide();
	    if (active_words[0]) {
		active = $(active_words[0]).find('input:first').attr('id');
		$("#word-suggestions").append('<input id="active" name="active" type="hidden" value="' + active + '">');
		$("#word-suggestions").append("Looking for dictionary matches...");
		$("#word-suggestions").show();
		var form = $(this).closest('form');
		loadXMLPost('/rankedwords/', form.serialize(), processReqChange);
	    }
	});

    $('#pubwords').bind('click', function(e) {
	    $("#word-intro").hide();
	    $("#word-suggestions").empty();
	    $("#buttons-horizontal").hide();
	    if (active_words[0]) {
		active = $(active_words[0]).find('input:first').attr('id');
		$("#word-suggestions").append('<input id="active" name="active" type="hidden" value="' + active + '">');
		$("#word-suggestions").append("Looking for published matches...");
		$("#word-suggestions").show();
		var form = $(this).closest('form');
		loadXMLPost('/pubwords/', form.serialize(), processReqChange);
	    }
	});

    $('#auto-fill').bind('click', function(e) {
	    var form = $(this).closest('form');
            fill_type = 1;
	    $("#auto-fill").hide();
	    $("#guided-fill").hide();
	    $("#stop-fill").show();
	    $("#skip-fill").hide();
	    $("#pop-fill").hide();
	    $("#clear-fill").hide();
	    loadXMLPost('/fill/', form.serialize(), fillReqChange);
	});

    $('#step-fill').bind('click', function(e) {
	    var form = $(this).closest('form');
	    $("#stop-fill").hide();
	    $("#step-fill").hide();
	    $("#auto-fill").hide();
	    $("#guided-fill").hide();
	    $("#skip-fill").hide();
	    $("#pop-fill").hide();
	    $("#clear-fill").hide();
            fill_type = 0;
	    loadXMLPost('/fill/', form.serialize(), fillReqChange);
	});

    $('#guided-fill').bind('click', function(e) {
	    $("#word-suggestions").empty();
	    if (active_words[0]) {
		active = $(active_words[0]).find('input:first').attr('id');
		$("#word-suggestions").append('<input id="active" name="active" type="hidden" value="' + active + '">');
		var form = $(this).closest('form');
		$("#stop-fill").hide();
		$("#step-fill").hide();
		$("#guided-fill").hide();
		$("#auto-fill").hide();
		$("#skip-fill").hide();
		$("#pop-fill").hide();
		$("#clear-fill").hide();
		fill_type = 0;
		$('#fill-guide').attr('value', 'on');
		loadXMLPost('/fill/', form.serialize(), fillReqChange);
		$('#fill-guide').attr('value', '');
	    }
	});

    $('#stop-fill').bind('click', function(e) {
	    var form = $(this).closest('form');
	    $("#stop-fill").hide();
            fill_type = 0;
	    loadXMLPost('/fill/', form.serialize(), fillReqChange);
	});

    $('#skip-fill').bind('click', function(e) {
	var stack = $('#fill-stack').attr('value').split(',');
	var top = stack.pop().split('&');
	if (top.length > 2) {
	    var inputs = $('#' + top[0]).find('input');
	    activate_word($(inputs[0]));
	    set_word(inputs, top[2]);
	    top.splice(2,1); 
	}
	stack.push(top.join('&'));
	stackstr = stack.join(',')
	$('#fill-stack').attr('value', stackstr);
	showFillStack(stackstr)
    });

    $('#pop-fill').bind('click', function(e) {
	var stack = $('#fill-stack').attr('value').split(',');
	var top = stack.pop().split('&');
	var inputs = $('#' + top[0]).find('input');
	activate_word($(inputs[0]));
	set_word(inputs, top[1]);
	$('#' + top[0] + "-clue").empty()
	if (stack.length > 0) {
	    top = stack[stack.length - 1].split('&');
	    inputs = $('#' + top[0]).find('input');
	    activate_word($(inputs[0]));
	}
	stackstr = stack.join(',')
	$('#fill-stack').attr('value', stackstr);
	showFillStack(stackstr)
    });

    $('#clear-fill').bind('click', function(e) {
	$('#fill-stack').attr('value', '');
	$("#fill-stack-disp").empty();
	showFillStack('')
    });

    $('#listwords').bind('click', function(e) {
	    $("#word-intro").hide();
	    $("#word-suggestions").empty();
	    $("#buttons-horizontal").hide();
	    if (active_words[0]) {
		active = $(active_words[0]).find('input:first').attr('id');
		$("#word-suggestions").append('<input id="active" name="active" type="hidden" value="' + active + '">');
		$("#word-suggestions").append("Looking for list matches...");
		$("#word-suggestions").show();
		var form = $(this).closest('form');
		loadXMLPost('/pubwords/', form.serialize(), processReqChange);
	    }
	});

    $('#definition').bind('click', function(e) {
	    $("#word-intro").hide();
	    $("#word-suggestions").empty();
	    $("#buttons-horizontal").hide();
	    if (active_words[0]) {
		active = $(active_words[0]).find('input:first').attr('id');
		$("#word-suggestions").append('<input id="active" name="active" type="hidden" value="' + active + '">');
		$("#word-suggestions").append("Looking for definitions...");
		$("#word-suggestions").show();
		var form = $(this).closest('form');
		loadXMLPost('/definition/', form.serialize(), defReqChange);
	    }
	});

    $('#examples').bind('click', function(e) {
	    $("#word-intro").hide();
	    $("#word-suggestions").empty();
	    $("#buttons-horizontal").hide();
	    if (active_words[0]) {
		active = $(active_words[0]).find('input:first').attr('id');
		$("#word-suggestions").append('<input id="active" name="active" type="hidden" value="' + active + '">');
		$("#word-suggestions").append("Looking for examples...");
		$("#word-suggestions").show();
		var form = $(this).closest('form');
		loadXMLPost('/examples/', form.serialize(), defReqChange);
	    }
	});

    $('#clues').bind('click', function(e) {
	    $("#word-intro").hide();
	    $("#word-suggestions").empty();
	    $("#buttons-horizontal").hide();
	    if (active_words[0]) {
		active = $(active_words[0]).find('input:first').attr('id');
		$("#word-suggestions").append('<input id="active" name="active" type="hidden" value="' + active + '">');
		$("#word-suggestions").append("Looking for clues...");
		$("#word-suggestions").show();
		var form = $(this).closest('form');
		loadXMLPost('/clues/', form.serialize(), defReqChange);
	    }
	});

    $('#words').bind('click', function(e) {
	    $("#word-suggestions").empty();
	    $("#buttons-horizontal").hide();
	    var pattern = get_pattern(active_words[0].find('input'));
	    loadXMLDoc('/words/?pattern=' + pattern);
	});

    $('#print').bind('click', function(e) {
	    var form = $(this).closest('form');
	    form.attr('action','/print/');
	    form.attr('target','_blank');
	    form.submit();
	});

    $('#printall').bind('click', function(e) {
	    do_save(saveReqChange);
	    $("#save-progress").show();
	    var form = $(this).closest('form');
	    form.attr('action','/printall/');
	    form.attr('target','_blank');
	    form.submit();
	});

    $('#toxpf').bind('click', function(e) {
	    var form = $(this).closest('form');
	    form.attr('action','/toxpf/');
	    form.attr('target','_blank');
	    form.submit();
	});

    $('#topuz').bind('click', function(e) {
	    var form = $(this).closest('form');
	    form.attr('action','/topuz/');
	    form.attr('target','_self');
	    form.submit();
	});

    $('#gridedit').bind('click', function(e) {
	    var form = $(this).closest('form');
	    form.attr('action','/gridedit/');
	    form.attr('target','_blank');
	    form.submit();
	});

    $('#file-tab').bind('click', function(e) {
	setActionTab('file');
	});

    $('#word-tab').bind('click', function(e) {
	setActionTab('word');
	});

    $('#clue-tab').bind('click', function(e) {
	setActionTab('clue');
	});

    $('#wl-tab').bind('click', function(e) {
	setActionTab('wl');
	});

    $('#stat-tab').bind('click', function(e) {
	setActionTab('stat');
	});

    $('#rebus-tab').bind('click', function(e) {
	setActionTab('rebus');
	});

    $('#fill-tab').bind('click', function(e) {
	setActionTab('fill');
	});

    $('#help-tab').bind('click', function(e) {
	setActionTab('help');
	});

    $('#contact-tab').bind('click', function(e) {
	setActionTab('contact');
	});

    $('#forum-tab').bind('click', function(e) {
	window.open('http://groups.google.com/group/crosswordcomposer');
	});

    $('#file-tab').bind('mouseover', function(e) {
	$(e.target).attr('style', 'background-color: #222288;color: white');
	});

    $('#word-tab').bind('mouseover', function(e) {
	$(e.target).attr('style', 'background-color: #222288;color: white');
	});

    $('#clue-tab').bind('mouseover', function(e) {
	$(e.target).attr('style', 'background-color: #222288;color: white');
	});

    $('#wl-tab').bind('mouseover', function(e) {
	$(e.target).attr('style', 'background-color: #222288;color: white');
	});

    $('#stat-tab').bind('mouseover', function(e) {
	$(e.target).attr('style', 'background-color: #222288;color: white');
	});

    $('#rebus-tab').bind('mouseover', function(e) {
	$(e.target).attr('style', 'background-color: #222288;color: white');
	});

    $('#fill-tab').bind('mouseover', function(e) {
	$(e.target).attr('style', 'background-color: #222288;color: white');
	});

    $('#contact-tab').bind('mouseover', function(e) {
	$(e.target).attr('style', 'background-color: #222288;color: white');
	});

    $('#forum-tab').bind('mouseover', function(e) {
	$(e.target).attr('style', 'background-color: #222288;color: white');
	});

    $('#file-tab').bind('mouseout', function(e) {
	if ($(e.target).attr('active') != "true") {
	    $(e.target).attr('style', 'background-color: #eeeeff;color: black');
	}
	});

    $('#word-tab').bind('mouseout', function(e) {
	if ($(e.target).attr('active') != "true") {
	    $(e.target).attr('style', 'background-color: #eeeeff;color: black');
	}
	});

    $('#clue-tab').bind('mouseout', function(e) {
	if ($(e.target).attr('active') != "true") {
	    $(e.target).attr('style', 'background-color: #eeeeff;color: black');
	}
	});

    $('#wl-tab').bind('mouseout', function(e) {
	if ($(e.target).attr('active') != "true") {
	    $(e.target).attr('style', 'background-color: #eeeeff;color: black');
	}
	});

    $('#stat-tab').bind('mouseout', function(e) {
	if ($(e.target).attr('active') != "true") {
	    $(e.target).attr('style', 'background-color: #eeeeff;color: black');
	}
	});

    $('#rebus-tab').bind('mouseout', function(e) {
	if ($(e.target).attr('active') != "true") {
	    $(e.target).attr('style', 'background-color: #eeeeff;color: black');
	}
	});

    $('#fill-tab').bind('mouseout', function(e) {
	if ($(e.target).attr('active') != "true") {
	    $(e.target).attr('style', 'background-color: #eeeeff;color: black');
	}
	});

    $('#help-tab').bind('mouseout', function(e) {
	if ($(e.target).attr('active') != "true") {
	    $(e.target).attr('style', 'background-color: #eeeeff;color: black');
	}
	});

    $('#contact-tab').bind('mouseout', function(e) {
	if ($(e.target).attr('active') != "true") {
	    $(e.target).attr('style', 'background-color: #eeeeff;color: black');
	}
	});

    $('#forum-tab').bind('mouseout', function(e) {
	if ($(e.target).attr('active') != "true") {
	    $(e.target).attr('style', 'background-color: #eeeeff;color: black');
	}
	});

    $('#newus').bind('click', function(e) {
	    deleteAllCookies();
	    window.location='/newus/';
	});

    $('#newus21').bind('click', function(e) {
	    deleteAllCookies();
	    window.location='/newus/?size=21';
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
	    $("#file-load").append('<br><input id="puzurl" name="puzurl" type="text" size=100 value=""/> <input id="puz-load-submit" type=button value="Load PUZ from URL"/>');
	    $('#puz-load-submit').bind('click', function(e) {
		    var form = $(this).closest('form');
		    form.attr('action','/frompuz/');
		    form.attr('target','_blank');
		    form.submit();
		});
	});

    $('#frompuzlocal').bind('click', function(e) {
	    deleteAllCookies();
	    $("#file-load").append('<br><input id="puzfile" name="puzfile" type="file"/> <input id="puz-load-submit" type=button value="Load local PUZ"/>');
	    $('#puz-load-submit').bind('click', function(e) {
		    var form = $(this).closest('form');
		    form.attr('action','/frompuz/');
		    form.attr('target','_blank');
		    form.submit();
		});
	});

    $('#word-suggestions').hide();    
    $('#definition').hide();
    $('#examples').hide();
    $('#clues').hide();
    $('#rankedwords').hide();
    $('#pubwords').hide();
    $('#listwords').hide();
    $('#clearwd').hide();
    $("#stop-fill").hide();
    $("#skip-fill").hide();
    $("#pop-fill").hide();
    $("#clear-fill").hide();

    $('#active-clue-edit:not(.no-number)').bind('keyup', function(e) {
	    if (e.keyCode === 13) {
		var clue = $('#active-clue-edit').find('input:first').attr('value');
		clue_for(active_words[0]).empty();
		clue_for(active_words[0]).append(clue);
		input_for(active_words[0]).attr('value', clue);
		$(active_words[0]).find('input:first').focus();
	    }
	});
    $('#grid').find('input:first').focus();
    setActionTab('file');
}

function setActionTab(tabname) {
    active_tab = tabname;
    setTabInactive('file');
    setTabInactive('word');
    setTabInactive('clue');
    setTabInactive('wl');
    setTabInactive('rebus');
    setTabInactive('fill');
    setTabInactive('help');
    setTabInactive('contact');
    setTabInactive('stat');
    setTabActive(tabname);
}

function setTabInactive(ctl) {
    $('#' + ctl + '-content').hide();
    $('#' + ctl + '-tab').attr('style', 'background-color: #eeeeff;color: black');
    $('#' + ctl + '-tab').attr('active', 'false');
}

function setTabActive(ctl) {
    $('#' + ctl + '-content').show();
    $('#' + ctl + '-tab').attr('style', 'background-color: #222288; color: white');
    $('#' + ctl + '-tab').attr('active', 'true');
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
    var pattern = get_pattern(active_words[0].find('input'));
    if (pattern.indexOf("0") == -1) {
	$('#definition').show();
	$('#examples').show();
	$('#clues').show();
	$('#rankedwords').hide();
	$('#pubwords').hide();
	$('#listwords').hide();
    } else {
	$('#definition').hide();
	$('#examples').hide();
	$('#clues').hide();
	$('#rankedwords').show();
	$('#pubwords').show();
	$('#listwords').show();
    }
    $('#clearwd').show();
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
    $('#definition').hide();
    $('#examples').hide();
    $('#clues').hide();
    $('#rankedwords').hide();
    $('#pubwords').hide();
    $('#listwords').hide();
    $('#clearword').hide();
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
 	var letter = word.substr(idx,1);
	if (letter == "?") {
	    square.val("");
	} else {
	    square.val(letter);
	}
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

function loadXMLPost(url, body, reqChange) 
{
    if (window.XMLHttpRequest) {
        req = new XMLHttpRequest();
        req.onreadystatechange = reqChange;
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
	    if(words[0] == "") {
		$("#word-suggestions").append('No matching results found.');
	    } else {
		for (i=0; i<words.length; i++) {
		    $("#word-suggestions").append('<input id="iw' + i + '" type=button value="' + words[i] + '"/>');
		    $('#iw' + i).bind('click', function(e) {
			    set_word(active_words[0].find('input'), $(e.target).attr('value'));
			$('#definition').show();
			$('#examples').show();
			$('#clues').show();
			$('#rankedwords').hide();
			$('#pubwords').hide();
			$('#listwords').hide();
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

function defReqChange() 
{
    // only if req shows "complete"
    if (req.readyState == 4) {
        // only if "OK"
        if (req.status == 200) {
	    $("#word-suggestions").empty();
	    $("#word-suggestions").append(req.response);
	    $("#word-suggestions").show();
        } else {
            alert("There was a problem retrieving the XML data:\n" + req.statusText);
        }
	$("#buttons-horizontal").show();
    }
}

function showFillStack(stack_str)
{
    $("#fill-stack-disp").empty();
    var tbl_str = "<table border=1 bordercolor=#339933 cellspacing=0 style='border-collapse:collapse'>";
    var sstr = stack_str.split(',');
    for (i=sstr.length - 1; i>=0; i--) {
	var wds = sstr[i].split('&');
	tbl_str += "<tr>";
	for (j=0; j<Math.min(wds.length,10); j++) {
	    tbl_str += "<td>";
	    tbl_str += wds[j];
	    tbl_str += "</td>";
	}
	if (wds.length > 10) {
	    tbl_str += "<td>";
	    tbl_str += (wds.length -10) + " more...";
	    tbl_str += "</td>";
	}
	    
	tbl_str += "</tr>";
    }	
    tbl_str += "</table>";
    $("#fill-stack-disp").append(tbl_str);
}

function fillReqChange() 
{
    // only if req shows "complete"
    if (req.readyState == 4) {
        // only if "OK"
        if (req.status == 200) {
	    var resp = req.response;
	    if (resp == '') {
		alert("Fill Complete");
		$('#fill-stack').attr('value', "");
		$("#step-fill").show();
		$("#auto-fill").show();
		$("#stop-fill").hide();
		showFillStack("");
		return;
	    } else if (resp == 'unfillable') {
		alert("Unfillable Grid");
		$("#step-fill").show();
		$("#auto-fill").show();
		$("#guided-fill").show();
		$("#skip-fill").show();
		$("#pop-fill").show();
		$("#clear-fill").show();
		return;
	    } else {
		resp = resp.split(':');
		var set = resp[0].split('/');
		for (i=0; i<set.length; i++) {
		    var wset = set[i].split('&');
		    var inputs = $('#' + wset[0]).find('input');
		    activate_word($(inputs[0]));
		    set_word(inputs, wset[1]);
		    input_for(active_words[0]).attr('value', '');
		    clue_for(active_words[0]).empty();
		}
		$('#fill-stack').attr('value', resp[1]);
	    }
	    showFillStack(resp[1]);
	    if (fill_type == 1) {
		loadXMLPost('/fill/', $('form').serialize(), fillReqChange);
	    } else {
		$("#step-fill").show();
		$("#auto-fill").show();
		$("#guided-fill").show();
		$("#skip-fill").show();
		$("#pop-fill").show();
		$("#clear-fill").show();
	    }
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
	    $("#save-progress").hide();
        } else {
            alert("There was a problem saving your puzzle:\n" + req.statusText);
	    $("#save-progress").hide();
        }
    }
}

function clueReqChange()
{
    // only if req shows "complete"
    if (req.readyState == 4) {
        // only if "OK"
        if (req.status == 200) {
	    var resp = req.response;
	    var pairs = resp.split('~');
	    for (i=0; i<pairs.length; i++) {
		cset = pairs[i].split('|');
		$('#' + cset[0] + '-clue').empty();
		$('#' + cset[0] + '-clue').append(cset[1]);
		$('#' + cset[0] + '-input').attr('value', cset[1]);
	    }
	    $("#auto-clue").show();
        }
    }
}