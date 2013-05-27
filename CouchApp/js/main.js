var $ = require('jquery');
var db = require('db').current();
//var pricedb = require('db').use("http://bitbot.iriscouch.com:5984/bitcoin-live-data");
var defaultCodeDoc = {
    type: "code",
    name: "derp",
    time: 0,
    code: "Your Python Code Here!"
};
var latestCode = "Your Python Code Here Please!";
var myCodeMirror = null;
var autoSave = false;


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


db.info(function(err, response){
    //console.log(err);
    //console.log(response);
});

function saveCodeToDB(){
    myCodeMirror.save();
    latestCode = $("#Codemirror").val();
    db.getView("bitbot-couchapp", "code", {limit: 1, descending: true}, function(err, response){
        var saveNew = true;
        if(response && response.rows[0].value.code && latestCode == response.rows[0].value.code){
            saveNew = false;
        }
        if(saveNew){
            defaultCodeDoc.code = latestCode;
            defaultCodeDoc.time = new Date().getTime() * 1000;
            db.saveDoc(defaultCodeDoc, function(err, response){
                //console.log(response);
            });
        }

    });
}

$("#saveCode").click(function(eventObj){
    eventObj.preventDefault();
    saveCodeToDB();
});

db.changes({}, function(err, response){
    console.log(response);
});



