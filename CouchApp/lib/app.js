exports.views = {
    code: {
        map: function (doc) {
            if(doc.type == "code"){
                emit(doc.time, doc);
            }
        }
    }
};
