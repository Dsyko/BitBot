var $ = require('jquery');
var db = require('db').current();
var defaultCodeDoc = {
    type: "code",
    name: "derp",
    time: 0,
    code: "Your Python Code Here!"
};
var latestCode = "Your Python Code Here Please!";
var myCodeMirror = null;

//Get Codemirror Scripts then apply to textarea
$.getScript("lib/codemirror.js", function(){
    $.getScript("mode/python/python.js", function(){
        //var designDogName = db.guessCurrent().design_doc;
        db.getView("bitbot-couchapp", "code", {limit: 1, descending: true}, function(err, response){
            //console.log(response);
            if(response && response.rows[0].value.code){
                latestCode = response.rows[0].value.code;
            }
            $("#Codemirror").val(latestCode);
            myCodeMirror = CodeMirror.fromTextArea($("#Codemirror")[0], {theme: "twilight"});
        });
    });
});



/*
db.info(function(err, response){
    console.log(response);
});
*/



$("#saveCode").click(function(eventObj){
    myCodeMirror.save();
    latestCode = $("#Codemirror").val()
    defaultCodeDoc.code = latestCode;
    defaultCodeDoc.time = new Date().getTime() * 1000;
    db.saveDoc(defaultCodeDoc, function(err, response){
        console.log(response);
    });
});


