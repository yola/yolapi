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

/* Display a bootstrap alert */
function bootstrapAlert(message, type) {
	if (typeof(type) === 'undefined') {
		type = '';
	} else {
		type = 'alert-' + type;
	}
	$('.navbar').after(
		'<div class="alert ' + type + '">'
		+ '<button type="button" class="close" data-dismiss="alert">&times;</button>'
		+ message
		+ '</div>');
}

/* Perform an AJAX request and display the returned data in an alert */
function queryAndAlert(url, method) {
	if (typeof(method) === 'undefined')
		method = 'POST';

	$.ajax({
		type: method,
		url: url,
		success: function(data) {
			bootstrapAlert(data, 'success');
		},
		error: function(jqXHR, data, errorThrown) {
			bootstrapAlert(errorThrown, 'error');
		}
	});
}

$(document).ready(function() {
	var csrftoken = getCookie('csrftoken');
	$.ajaxSetup({
		crossDomain: false,
		beforeSend: function(xhr, settings) {
			if (!csrfSafeMethod(settings.type)) {
				xhr.setRequestHeader("X-CSRFToken", csrftoken);
			}
		}
	});

	$('a.post').click(function() {
		bootstrapAlert($(this).attr('data-started'), 'info');
		queryAndAlert($(this).attr('data-url'));
	});

	$('a.delete').click(function() {
		var delete_ = $(this);

		$('#confirm-deletion .package').html(delete_.attr('data-package'));
		$('#confirm-deletion .version').html(delete_.attr('data-version'));
		$('#confirm-deletion .filetype').html(delete_.attr('data-filetype'));
		$('#confirm-deletion .pyversion').html(delete_.attr('data-pyversion'));

		$('#confirm-deletion .btn-primary').one('click', function() {
			queryAndAlert(delete_.attr('data-url'), 'DELETE');
			$('#confirm-deletion').modal('hide');
		});
		$('#confirm-deletion').modal('show');
	});
});
