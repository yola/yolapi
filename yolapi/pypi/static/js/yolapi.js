/* Boilerplate from https://docs.djangoproject.com/en/dev/ref/contrib/csrf/
 */
function getCookie(name) {
	var cookieValue = null;
	if (document.cookie && document.cookie != '') {
		var cookies = document.cookie.split(';');
		for (var i = 0; i < cookies.length; i++) {
			var cookie = jQuery.trim(cookies[i]);
			// Does this cookie string begin with the name we want?
			if (cookie.substring(0, name.length + 1) == (name + '=')) {
				cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
				break;
			}
		}
	}
	return cookieValue;
}

function csrfSafeMethod(method) {
	// these HTTP methods do not require CSRF protection
	return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
}

function bootstrapAlert(message, type) {
	if (typeof(type) === 'undefined') {
		type = '';
	} else {
		type = 'alert-' + type;
	}
	$('.navbar').after(
		'<div class="alert ' + type + '">'
		+ '<button type="button" class="close" data-dismiss="alert">×</button>'
		+ message
		+ '</div>');
}

$(document).ready(function() {
	var csrftoken = getCookie('csrftoken');

	$.ajaxSetup({
		crossDomain: false, // obviates need for sameOrigin test
		beforeSend: function(xhr, settings) {
			if (!csrfSafeMethod(settings.type)) {
				xhr.setRequestHeader("X-CSRFToken", csrftoken);
			}
		}
	});

	$('a.post').click(function() {
		bootstrapAlert($(this).attr('data-started'), 'info');
		$.ajax({
			type: 'POST',
			url: $(this).attr('data-url'),
			success: function(data) {
				bootstrapAlert(data, 'success');
			},
			error: function(jqXHR, data, errorThrown) {
				bootstrapAlert(errorThrown, 'error');
			}
		});
	});
});
