exports.views = {
    code: {
        map: function (doc) {
            if(doc.type == "code"){
                emit(doc.time, doc);
            }
        }
    }
};

exports.filters = {
    "code": function(doc, req) {
        if(doc.type == "code"){
            return true;
        }
        else{
            return false;
        }
    }
};
