var svenjs = svenjs || {};

//TODO: use a more robust pattern for object creation
svenjs.Sven = function(url){

    this.url = url;
    return this;

};


$(document).ajaxSend(function(event, xhr, settings) {
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
    function sameOrigin(url) {
        // url could be relative or scheme relative or absolute
        var host = document.location.host; // host + port
        var protocol = document.location.protocol;
        var sr_origin = '//' + host;
        var origin = protocol + sr_origin;
        // Allow absolute or scheme relative URLs to same origin
        return (url == origin || url.slice(0, origin.length + 1) == origin + '/') ||
            (url == sr_origin || url.slice(0, sr_origin.length + 1) == sr_origin + '/') ||
            // or any other URL that isn't scheme relative or absolute i.e relative.
            !(/^(\/\/|http:|https:).*/.test(url));
    }
    function safeMethod(method) {
        return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
    }

    if (!safeMethod(settings.type) && sameOrigin(settings.url)) {
        xhr.setRequestHeader("X-CSRFToken", getCookie('csrftoken'));
    }
});


/* get documents */
svenjs.Sven.prototype.getDocuments = function(successCallback, args){
	
    //var url = this.url + "/sketch/query/" + this.database + "/" + collection + "/" + command + "/";
    var url = this.url + "/anta/api/documents/?indent=true";
	
	var args = args || { };
	args.corpus = 1;
    
    $.ajax({
        type: 'GET',
        url: url,
        data: args,
        complete: function(){
        	console.log(this.url);
    		},
        success: successCallback,
        error: successCallback,
        dataType: 'json'
    });

};

/* get document */
svenjs.Sven.prototype.getDocument = function(id, successCallback, args){

		
    //var url = this.url + "/sketch/query/" + this.database + "/" + collection + "/" + command + "/";
    var url = this.url + "/anta/api/documents/" + id + "/" + "?indent=true";

	var args = args || { };
	args.corpus = 1;

    $.ajax({
        type: 'GET',
        url: url,
        data: args,
        success: successCallback,
        error: successCallback,
        complete: function(){
        	console.log(this.url);
    		},
        dataType: 'json'
    });
    
    
};

/* get relations */
svenjs.Sven.prototype.getRelations = function(successCallback, args){
	
    var url = this.url + "/anta/api/relations/?indent=true";
	
    
    $.ajax({
        type: 'GET',
        url: url,
        data: args,
        complete: function(){
        	console.log(this.url);
    		},
        success: successCallback,
        error: successCallback,
        dataType: 'json'
    });

};

/* get relation */
svenjs.Sven.prototype.getRelation = function(id, successCallback, args){

		
    //var url = this.url + "/sketch/query/" + this.database + "/" + collection + "/" + command + "/";
    var url = this.url + "/anta/api/relations/" + id + "/" + "?indent=true";

    $.ajax({
        type: 'GET',
        url: url,
        data: args,
        success: successCallback,
        error: successCallback,
        complete: function(){
        	console.log(this.url);
    		},
        dataType: 'json'
    });
    
    
};

/* add relation */
svenjs.Sven.prototype.addRelation = function(successCallback, args){
	
    var url = this.url + "/anta/api/relations/?method=POST&indent=true";
	
    
    $.ajax({
        type: 'GET',
        url: url,
        data: args,
        complete: function(){
        	console.log(this.url);
    		},
        success: successCallback,
        error: successCallback,
        dataType: 'json'
    });

};

/* delete relation */
svenjs.Sven.prototype.deleteRelation = function(id, successCallback){
	
    var url = this.url + "/anta/api/relations/" + id + "/" + "?method=DELETE&indent=true";
	
    
    $.ajax({
        type: 'GET',
        url: url,
        complete: function(){
        	console.log(this.url);
    		},
        success: successCallback,
        error: successCallback,
        dataType: 'json'
    });

};

/* download */
svenjs.Sven.prototype.download = function(id, successCallback, args){

		
    //var url = this.url + "/sketch/query/" + this.database + "/" + collection + "/" + command + "/";
    var url = this.url + "/anta/api/download/document/" + id;

    $.ajax({
        type: 'GET',
        url: url,
        data: args,
        success: successCallback,
        error: successCallback,
        complete: function(){
        	//console.log(this.url);
    		},
        dataType: 'json'
    });
    
};

/* graph */
svenjs.Sven.prototype.graph = function(id, successCallback, args){
		
    //var url = this.url + "/sketch/query/" + this.database + "/" + collection + "/" + command + "/";
    var url = this.url + "/anta/api/relations/graph/corpus/" + id + "/?filters={}";

    $.ajax({
        type: 'GET',
        url: url,
        data: args,
        success: successCallback,
        error: successCallback,
        complete: function(){
        	//console.log(this.url);
    		},
        dataType: 'json'
    });
    
};


/* streamgraph */
svenjs.Sven.prototype.streamgraph = function(id, successCallback, args){
		
    //var url = this.url + "/sketch/query/" + this.database + "/" + collection + "/" + command + "/";
    var url = this.url + "/anta/api/streamgraph/corpus/" + id + "/?filters={}";

    $.ajax({
        type: 'GET',
        url: url,
        data: args,
        success: successCallback,
        error: successCallback,
        dataType: 'json'
    });
    
};

