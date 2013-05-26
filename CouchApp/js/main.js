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

db.info(function(err, response){
    console.log(response);
});

var name = db.guessCurrent().design_doc;

db.getView(name, "code", {limit: 1, descending: true}, function(err, response){
    //console.log(response);
    if(response && response.rows[0].value.code){
        latestCode = response.rows[0].value.code;
        console.log(latestCode);
    }
    $("#Codemirror").val(latestCode);
    myCodeMirror = CodeMirror.fromTextArea($("#Codemirror")[0], {theme: "twilight"});
});

$("#saveCode").click(function(eventObj){
    myCodeMirror.save();
    latestCode = $("#Codemirror").val()
    defaultCodeDoc.code = latestCode;
    db.saveDoc(defaultCodeDoc, function(err, response){
        console.log(response);
    });
});


