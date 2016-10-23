$(document).ready(function(){
	//$('#q').css('display', 'inline');
	$('#search').css('display', 'inline');
    //console.log('Hello World');
    $('#search').submit(function(e) {
		//alert('here');
		console.log('submit');
		e.preventDefault();
		//return false;
	});
});
