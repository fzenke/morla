function set_label(artid, label) {
	$.get('/papers/ajax_set_label/', {article_id: artid, label: label}, function(data){
			var label_ref = '#label' + data['article_id'];
			// alert('ID number: ' + data['article_id'] + data['result']);
			$(label_ref).html(data['result']);
	});
}

$("button[name=btnSubmitPlus]").click(function(){
	var artid;
	artid = $(this).attr("data-artid");
	label = 1
	set_label(artid,label);
});

$("button[name=btnSubmitZero]").click(function(){
	var artid;
	artid = $(this).attr("data-artid");
	label = 0 
	set_label(artid,label);
});

$("button[name=btnSubmitMinus]").click(function(){
	var artid;
	artid = $(this).attr("data-artid");
	label = -1
	set_label(artid,label);
});

$("button[name=btnSubmitStar]").click(function(){
	var artid = $(this).attr("data-artid");
	$.get('/papers/ajax_toggle_star/', {article_id: artid}, function(data){
			var html_ref = '#star' + data['article_id'];
			if (data['result']==0) 
				$(html_ref).html("<span class=\"glyphicon glyphicon-star-empty\"></span>");
			else
				$(html_ref).html("<span class=\"glyphicon glyphicon-star\"></span>");
	});
});
