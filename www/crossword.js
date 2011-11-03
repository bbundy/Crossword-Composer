var jQ = jQuery.noConflict();

jQ('ready', crossword_init);
jQ('ready', load_from_cookie);

var focus_event_fired_during_click = false;
var active_words = [];

function crossword_init() {
	var inputs = jQ('#grid').find('input');
	var all_words = jQ('#grid div');

	inputs.bind('focus', function(e) {
		var current_letter = jQ(this);
		focus_event_fired_during_click = true;
		if (!in_active_word(current_letter)) {
			var intersecting_letter = getIntersectingLetter(current_letter);
			if (intersecting_letter && !is_first_letter(current_letter) && is_first_letter(intersecting_letter)) {
				intersecting_letter.select();
				activate_word(intersecting_letter);
			} else {
				this.select();
				activate_word(current_letter);
			}
		}
	});

	function in_active_word(letter) {
		var in_active = false;
		var this_word = letter.closest('div');
		jQ.each(active_words, function() {
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
		focus_event_fired_during_click = false;
	});

	inputs.bind('mouseup', function(e) {
		var current_letter = jQ(this);
		var word = current_letter.closest('div');
		var intersecting_letter = getIntersectingLetter(current_letter);
		if (intersecting_letter && !focus_event_fired_during_click) {
			intersecting_letter.focus();
		}
	});

	inputs.bind('keyup', function(e) {
		var key = e.keyCode || e.charCode;
		if (is_letter(key)) {
			jQ(e.target).val(String.fromCharCode(key).toLowerCase());
			copyChangeToIntersectingLetter(jQ(e.target));
			focusOnNextInput(jQ(e.target));
		}
		check_complete_for_letter(jQ(e.target));
	});
	function is_letter(key) {
		return (64 < key && key < 91) || (96 < key && key < 123) || key == 32;
	}

	inputs.bind('keydown', 'tab', function(e) {
		if (jQ(e.target).closest('div').nextAll('div:first')) {
			jQ(e.target).closest('div').nextAll('div:first').find('input:first').focus();
		}
		return false;
	});
	inputs.bind('keydown', 'Shift+tab', function(e) {
		if (jQ(e.target).closest('div').prevAll('div:first')) {
			jQ(e.target).closest('div').prevAll('div:first').find('input:first').focus();
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
		copyChangeToIntersectingLetter(jQ(e.target));
		focusOnPreviousInput(jQ(e.target));
		check_complete_for_letter(jQ(e.target));
	});
	inputs.bind('keyup', 'del', function(e) {
		copyChangeToIntersectingLetter(jQ(e.target));
		check_complete_for_letter(jQ(e.target));
		// Capture action to stop moving cursor
		return false;
	});
	inputs.bind('keydown', 'esc', function(e) {
		copyChangeToIntersectingLetter(jQ(e.target));
		// Capture action to IE clearing the entire crossword
		return false;
	});

	function move_back(e, direction) {
		var letter = jQ(e.target);
		if (letter.attr('id').indexOf(direction) !== -1) {
			focusOnPreviousInput(letter);
		} else {
			if (getIntersectingLetter(letter)) {
				focusOnPreviousInput(getIntersectingLetter(letter));
			}
		}
	}
	function move_forward(e, direction) {
		var letter = jQ(e.target);
		if (letter.attr('id').indexOf(direction) !== -1) {
			focusOnNextInput(letter);
		} else {
			if (getIntersectingLetter(letter)) {
				focusOnNextInput(getIntersectingLetter(letter));
			}
		}
	}

	jQ('label').bind('click', function(e) {
		if (has_numbers && !text_is_highlighted()) {
			word = jQ('#' + jQ(e.target).closest('label').attr('for'));
			activate_word(word);
			word.find('input:first').focus();
			return false;
		}
	});

	function text_is_highlighted() {
		return (selection() && selection().toString() != '') || (range() && range().text != '')
	}

	jQ('#check').bind('click', function(e) {
		jQuery.each(active_words, function () {
			check(this.find('input'));
		});
		check_complete(all_words);
	});

	jQ('#check-all').bind('click', function(e) {
		check(inputs);
		check_complete(all_words);
	});

	jQ('#cheat').bind('click', function(e) {
		jQuery.each(active_words, function () {
			populate_solution_for(this.find('input'));
		});
		check_complete(all_words);
	});

	jQ('#solution').bind('click', function(e) {
		if (confirm('Are you sure you want to see the full solution for this crossword?')) {
			populate_solution_for(inputs);
			check_complete(all_words);
		}
	});

	jQ('#clear').bind('click', function(e) {
		jQuery.each(active_words, function () {
			clear(this.find('input'));
		});
		check_complete(all_words);
	});

	jQ('#save').bind('click', function(e) {
		var form_values = jQ(this).closest('form').serialize();
		var saved_state = 'id=' + crossword_identifier + ';' + form_values.replace(/(\d+)-across-(\d+)=/g, '$1a$2').replace(/(\d+)-down-(\d+)=/g, '$1d$2');
		jQ.cookie('crossword', saved_state, { expires: 365 });
	});

	jQ('#revert-to-saved').bind('click', function(e) {
		load_from_cookie();
		check_complete(all_words);
	});
}

function load_from_cookie() {
	var saved_state = jQ.cookie('crossword');
	if (!saved_state) {
		saved_state = jQ.cookie(crossword_identifier);
	}
	if (saved_state) {
        var valid_cookie = true;
        var match = saved_state.match(/id=(.*);/);
        if (match) {
            valid_cookie = (match[1] === crossword_identifier);
            saved_state = saved_state.replace(/id=.*;/, '');
        }
        if (valid_cookie) {
            var form_values = saved_state.replace(/(\d+)a(\d+)/g, '$1-across-$2=').replace(/(\d+)d(\d+)/g, '$1-down-$2=');
            jQ(form_values.split('&')).each(function(index, pair) {
                var name_value = pair.split('=');
                jQ('#' + name_value[0]).val(name_value[1]);
            });
        }
	}
}

jQ('ready', bind_activate);
function bind_activate() {
	jQ('#anagrams').bind('click', function(e) {
		if (active_words.length > 0) {
			var the_range = selection() ? selection().toString() != '' ? selection().getRangeAt(0) : null : range();
			var possible_letters = '';
			if (the_range && the_range.startContainer === undefined) {
				possible_letters = the_range.text;
			} else if (the_range && jQ(the_range.startContainer).closest('label').attr('id') === clue_for(active_words[0]).attr('id')) {
				possible_letters = selection().toString();
			}
			possible_letters = possible_letters.replace(/\W/g, '').toLowerCase();
			var existing_letters = "";
			jQuery.each(active_words, function() { this.find('input').each(function() {
				var letter = jQ(this);
				if (letter.val()) {
					existing_letters += letter.val();
					possible_letters = possible_letters.replace(letter.val(), '');
				} else {
					existing_letters += '_';
				}
			})});
			var width = existing_letters.length * 33;
			var height = width * 0.8 + 100;
			if (width < 280) { width = 280; }
			if (height < 250) { height = 250; }
			window.open('http://bundy.org/xw/anagram?existing_letters=' + existing_letters + '&amp;possible_letters=' + possible_letters, 'anagrams', 'toolbar=false,menubar=false,status=false,height=' + height + ',width=' + width);
		}
	});
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
		jQuery.each(active_words, function() {
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
		return jQ('#' + intersections[letter.attr('id')]);
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
	return jQ('#' + word.attr('id') + '-clue');
}

function activate_word(letter) {
	jQuery.each(active_words, deactivate_word);
	active_words = words_for_letter(letter);
	jQuery.each(active_words, function() {
		this.css("z-index","999");
		this.addClass('active');
		if (has_numbers) {
			clue_for(this).addClass('active');
		}
	});
	jQ('#active-clue:not(.no-number)').append(clue_for(active_words[0]).contents().clone());
}

function words_for_letter(letter) {
	var word = letter.closest('div');
	words = words_for_clue[word.attr('id')]
    if (words) {
        the_words = jQuery.map(words, function(id) { return jQ('#' + id); });
    } else {
        the_words = [word]
    }
	return the_words
}

function deactivate_word() {
	this.removeClass('active');
	var clueNum = this.find('span').text();
	this.css("z-index", clueNum);
	jQ('#' + this.attr('id') + '-clue').removeClass('active');
	jQ('#active-clue').empty();
}

function check_complete_for_letter(letter) {
	check_complete(words_for_letter(letter));
	var intersect = getIntersectingLetter(letter);
    if (intersect) {
		check_complete(words_for_letter(intersect));
	}
}

function check_complete(words) {
	if (all_complete(words)) {
		jQuery.each(words, function() {
//			clue_for(jQ(this)).addClass('complete');
		});
	} else {
		jQuery.each(words, function() {
 //           clue_for(jQ(this)).removeClass('complete');
        });
	}
}


function all_complete(words) {
	var all_are_complete = true;
	jQuery.each(words, function() {
		if (!is_complete(jQ(this))) {
			all_are_complete = false;
		}
	});
	return all_are_complete;
}

function is_complete(word) {
	var complete = true;
	word.find('input').each(function() {
		if (jQ(this).val() == '' || jQ(this).val() == ' ') {
			complete = false;
		}
	});
	return complete;
}

function insert_from_anagram(letter_array) {
	var i = 0;
	jQuery.each(active_words, function() { this.find('input').each(function() {
		jQ(this).val(letter_array[i++]);
		copyChangeToIntersectingLetter(jQ(this));
	})});
	check_complete(all_words);
}

function clear(inputs) {
	inputs.each(function() {
		var square = jQ(this);
		square.val('');
		copyChangeToIntersectingLetter(square);
	});
}

function populate_solution_for(inputs) {
	inputs.each(function() {
		var square = jQ(this);
		square.val(solutions[square.attr('id')].toLowerCase());
		copyChangeToIntersectingLetter(square);
	});
}

function check(inputs) {
	inputs.each(function() {
		var square = jQ(this);
		if (square.val().toLowerCase() != solutions[square.attr('id')].toLowerCase()) {
			square.val('');
			copyChangeToIntersectingLetter(square);
		}
	});
}
