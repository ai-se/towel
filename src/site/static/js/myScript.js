initialization();

function initialization() {
    current_node = document.getElementById("elasticinput");
    my_mask = [];
    voc = [];
    coef = [];
    dual_coef = [];
    changed = false;
    certain_prob = [];
    certain = [];
    uncertain_prob = [];
    uncertain = [];
    search_result = {};
    support = [];
    turnover_prob = [];
    turnover = [];
    determinant = [];
    determinant_dist = [];
    addon = [];
    term = -1;
    search_key = "";
    display_limit = 50;

    $.ajax({
        type: "POST",
        url: "/init",
        async: true,

        data: {},
        success: init_receive
    });
}

function init_receive(response) {
    display_num_labeled(response.num_labeled, response.num_pos);
    display_train_round(response.the_round);
    display_num_control(response.num_control, response.control_pos);
}

function display_num_control(num_control,control_pos){
    document.getElementById("num_control").innerText="Control Set: "+control_pos.toString()+" / "+num_control.toString();
}

function display_num_labeled(num_labeled, num_pos) {
    document.getElementById("num_labeled").innerText = "Documents Labeled: " + num_pos.toString() + " / " + num_labeled.toString();
}

function display_train_round(the_round, prec, rec, Fscore) {
    if (the_round >= 1) {
        document.getElementsByName("plot_button")[0].disabled = false;
        document.getElementById("Precision").innerText = "Precision: " + prec.toString();
        document.getElementById("Recall").innerText = "Recall: " + rec.toString();
        document.getElementById("F_score").innerText = "F_score: " + Fscore.toString();
    }
    document.getElementById("the_round").innerText = "Training Round: " + the_round.toString();

}

function search_send(what) {
    search_key = what.elastic.value;
    $.ajax({
        type: "POST",
        url: "/search",
        async: true,
        data: {elastic: search_key},
        success: search_receive
    });
}

function search_receive(results) {
    search_result = results.hits.hits;
    var olnode = document.getElementById("search_result");
    while (olnode.firstChild) {
        olnode.removeChild(olnode.firstChild);
    }

    for (var i = 0; i < Math.min(search_result.length, display_limit); i++) {
        var tmp = search_result[i];
        var newli = document.createElement("li");
        var node = document.createTextNode(tmp._source.title + " (" + tmp._score + ")");

        newli.appendChild(node);
        newli.setAttribute("value", i);
        newli.setAttribute("onclick", "show_send(this,\"search\")");
        olnode.appendChild(newli);
    }

    show_send(olnode.firstChild, "search");
}

function show_send(what, which) {
    $("ol li").css("color", "white");
    $(what).css("color", "yellow");
    current_node = what;
    document.getElementById("send_label").removeAttribute('disabled');
    var tmp = {};
    if (which == "search") {
        tmp = search_result;
    }
    else if (which == "certain") {
        tmp = certain;
    }
    else if (which == "uncertain") {
        tmp = uncertain;
    }
    else if (which == "support") {
        tmp = support;
    }
    else if (which == "turnover") {
        tmp = turnover;
    }
    else if (which == "determinant") {
        tmp = determinant;
    }
    document.getElementById("which_part").value = which;
    document.getElementById("display").labeling.value = tmp[what.value]._source.label;
    document.getElementById("displaydoc_id").value = tmp[what.value]._id;
    // document.getElementById("displaydoc").innerHTML = tmp[what.value]._source.text;
    $("#displaydoc").html(highlight(tmp[what.value], which));
    $("#displaytag").html(tmp[what.value]._source.tags.join("; "));
}


function labeling_send(what) {
    if (document.getElementById("which_part").value=="turnover"){
        $.ajax({
            type: "POST",
            url: "/labelingControl",
            async: true,
            data: {
                id: document.getElementById("displaydoc_id").value,
                label: what.labeling.value
            },
            success: labelingControl_receive
        });
    }
    else{
        $.ajax({
            type: "POST",
            url: "/labeling",
            async: true,
            data: {
                id: document.getElementById("displaydoc_id").value,
                label: what.labeling.value
            },
            success: labeling_receive
        });
    }
}

function labeling_receive(response) {

    if (response != "none") {
        display_num_labeled(response.num_labeled, response.num_pos);
    }
    nextnode = current_node.nextSibling;
    prevnode = current_node.previousSibling;
    current_node.remove();
    if (nextnode) {
        show_send(nextnode, document.getElementById("which_part").value);
    }
    else if (prevnode) {
        show_send(prevnode, document.getElementById("which_part").value);
    }
    else {
        document.getElementById("displaydoc_id").value = "none";
        document.getElementById("displaydoc").innerHTML = "Done! Can start a new search or learn.";
        document.getElementById("send_label").setAttribute("disabled", "disabled");
    }
}

function labelingControl_receive(response) {
    if (response != "none") {
        display_num_control(response.num_control, response.control_pos);
        turnover_prob = response.turnover_prob.split(',').map(Number);
        turnover = response.turnover;
        display_train_round(response.the_round, response.pos.Prec, response.pos.Sen, response.pos.F1);
        control_selection(document.getElementById("control_options"));
    }
}

function train_send() {
    changed = false;
    $.ajax({
        type: "POST",
        url: "/train",
        async: true,
        data: {mask: JSON.stringify(my_mask), addon: JSON.stringify(addon)},
        success: train_receive
    });
}

function train_receive(response) {
    if (response.train_res == "error") {
        window.alert("Not enough training examples!!!");
        return
    }

    coef = response.coef.split(',').map(Number);
    support = response.support;
    certain_prob = response.certain_prob.split(',').map(Number);
    uncertain_prob = response.uncertain_prob.split(',').map(Number);
    dual_coef = response.dual_coef.split(',').map(Number);
    certain = response.certain;
    uncertain = response.uncertain;
    voc = response.vocab;
    turnover_prob =  response.turnover_prob.split(',').map(Number);
    turnover = response.turnover;
    more_coef = response.more_coef;


    display_train_round(response.the_round,response.pos.Prec,response.pos.Sen,response.pos.F1);

    control_selection(document.getElementById("control_options"));
    view_selection(document.getElementById("view_options"));

}

function featurization_send() {
    $.ajax({
        type: "POST",
        url: "/feature",
        async: true,
        data: {},
        success: check_response
    });
}


function feature_selection(what, which) {
    if (which == "mask") {
        if (what.value<voc.length){
            my_mask.push(what.value);
        }
        else{
            addon.splice(what.value-voc.length,1);
        }
        what.remove();
        changed = true;
    }
    else if (which == "unmask") {
        what.remove();
        var tmp_index = my_mask.indexOf(what.value);
        if (tmp_index > -1) {
            my_mask.splice(tmp_index, 1);
        }
        changed = true;
    }
}

function view_selection(what) {
    if (changed) {
        train_send();
    }
    else {
        switch (parseInt(what.selectedIndex)) {
            case 0:
                view_certain();
                break;
            case 1:
                view_uncertain();
                break;
            case 2:
                view_support();
                break;
            case 3:
                view_coef();
                break;
            case 4:
                edit_coef();
                break;
            case 5:
                edit_addons();
        }
    }
}


function view_certain() {

    if (voc) {

        var olnode = document.getElementById("learn_result");
        while (olnode.firstChild) {
            olnode.removeChild(olnode.firstChild);
        }
        for (var i = 0; i < certain.length; ++i) {

            var newli = document.createElement("li");
            var node = document.createTextNode(certain[i]._source.title + " (" + certain_prob[i].toString() + ")");
            newli.appendChild(node);
            newli.setAttribute("value", i);
            newli.setAttribute("onclick", "show_send(this,\"certain\")");
            olnode.appendChild(newli);
        }
    }
}

function view_uncertain() {
    if (voc) {

        var olnode = document.getElementById("learn_result");
        while (olnode.firstChild) {
            olnode.removeChild(olnode.firstChild);
        }

        for (var i = 0; i < uncertain.length; ++i) {

            var newli = document.createElement("li");
            var node = document.createTextNode(uncertain[i]._source.title + " (" + uncertain_prob[i].toString() + ")");
            newli.appendChild(node);
            newli.setAttribute("value", i);
            newli.setAttribute("onclick", "show_send(this,\"uncertain\")");
            olnode.appendChild(newli);
        }
    }
}

function view_support() {
    if (voc) {

        var olnode = document.getElementById("learn_result");
        while (olnode.firstChild) {
            olnode.removeChild(olnode.firstChild);
        }

        for (var i = 0; i < support.length; ++i) {

            var newli = document.createElement("li");
            var node = document.createTextNode(support[i]._source.title + " (" + dual_coef[i].toString() + ")");
            newli.appendChild(node);
            newli.setAttribute("value", i);
            newli.setAttribute("onclick", "show_send(this,\"support\")");
            olnode.appendChild(newli);
        }
    }
}

function view_coef() {
    if (voc) {
        var olnode = document.getElementById("learn_result");
        while (olnode.firstChild) {
            olnode.removeChild(olnode.firstChild);
        }

        var ind = [];
        for (var i = 0; i < coef.length; ++i) {
            ind.push(i);
        }
        ind.sort(function (a, b) {
            return Math.abs(coef[b]) - Math.abs(coef[a])
        });
        for (var i = 0; i < Math.min(coef.length, display_limit); ++i) {

            var newli = document.createElement("li");
            if (ind[i]>= voc.length){
                var word = "";
                addon[ind[i]-voc.length].forEach(function (item){
                    word=word+voc[item]+"+";
                });
                word = word.slice(0,-1);
                var node = document.createTextNode(word + " (" + coef[ind[i]].toString() + ")"); 
            }
            else{
                var node = document.createTextNode(voc[ind[i]] + " (" + coef[ind[i]].toString() + ")");
            }            
            newli.appendChild(node);
            newli.setAttribute("value", ind[i]);
            newli.setAttribute("onclick", "feature_selection(this,\"mask\")");
            olnode.appendChild(newli);
        }

    }
}

function edit_coef() {
    if (voc) {
        var olnode = document.getElementById("learn_result");
        while (olnode.firstChild) {
            olnode.removeChild(olnode.firstChild);
        }

        for (var i = 0; i < my_mask.length; ++i) {
            
            var newli = document.createElement("li");
            var node = document.createTextNode(voc[my_mask[i]]);
            newli.appendChild(node);
            newli.setAttribute("value", my_mask[i]);
            newli.setAttribute("onclick", "feature_selection(this,\"unmask\")");
            olnode.appendChild(newli);
        }
    }
}

function edit_addons() {
    if (voc) {
        var olnode = document.getElementById("learn_result");
        while (olnode.firstChild) {
            olnode.removeChild(olnode.firstChild);
        }

        for (var i = 0; i < addon.length; ++i) {
            
            var newli = document.createElement("li");
            var word = "";
            addon[i].forEach(function (item){
                word=word+voc[item]+"+";
            });
            word = word.slice(0,-1);
            var node = document.createTextNode(word);
            newli.appendChild(node);
            newli.setAttribute("value", i);
            newli.setAttribute("onclick", "remove_addon(this)");
            olnode.appendChild(newli);
        }
    }
}

function remove_addon(li){
    var word = li.innerText.split('+');
    var what = [];
    word.forEach(function(item){
       what.push(voc.indexOf(item)); 
    });
    edit_addon(what);
    li.remove();    
}


function control_selection(what) {

    switch (parseInt(what.selectedIndex)) {
        case 0:
            control_turnover();
            break;
        case 1:
            control_determinant(false);
    }
}

function control_turnover(){
    if (voc) {
        
        var olnode = document.getElementById("control_result");
        while (olnode.firstChild) {
            olnode.removeChild(olnode.firstChild);
        }
        for (var i = 0; i < turnover.length; ++i) {

            var newli = document.createElement("li");
            var node = document.createTextNode(turnover[i]._source.title + " (" + turnover_prob[i].toString() + ")");
            newli.appendChild(node);
            newli.setAttribute("value", i);
            newli.setAttribute("onclick", "show_send(this,\"turnover\")");
            newli.setAttribute("ondblclick", "control_determinant(this)");
            olnode.appendChild(newli);
        }
    }
}

function control_determinant(what){
    if(what){
        document.getElementById("control_options").selectedIndex = 1;
        
        response = $.ajax({
            type: "POST",
            url: "/determinant",
            async: false,
            // success: train_receive,
            data: {id: what.value}            
        });
        
        determinant = JSON.parse(response.responseText).determinant;
        determinant_dist = JSON.parse(response.responseText).dist;
        
        var olnode = document.getElementById("control_result");
        while (olnode.firstChild) {
            olnode.removeChild(olnode.firstChild);
        }
        for (var i = 0; i < determinant.length; ++i) {
    
            var newli = document.createElement("li");
            var node = document.createTextNode(determinant[i]._source.title + " (" + determinant_dist[i].toString() + ")");
            newli.appendChild(node);
            newli.setAttribute("value", i);
            newli.setAttribute("onclick", "show_send(this,\"determinant\")");
            olnode.appendChild(newli);
        }
    }
}

function restart_send() {
    $.ajax({
        type: "POST",
        url: "/restart",
        async: true,
        data: {},
        success: restart_receive
    });
}

function restart_receive(response) {
    if (check_response(response)) {
        initialization();
    }
}

function plot_send() {
    $.ajax({
        type: "POST",
        url: "/plot",
        async: true,
        data: {},
        success: plot_get
    });
}

function plot_get() {
    $.ajax({
        type: "POST",
        url: "/plotdata",
        async: true,
        data: {},
        success: plot_receive
    });}

function plot_receive(){}


function check_response(response) {
    my_SVM = response;
    if (response == "done") {
        window.alert("Done!");
        return true
    }
}

function autoreview() {
    var type = parseInt(document.getElementById("review_options").selectedIndex);
    var queue = [];
    switch (type) {
        case 0:
            queue = ["random"];
            break;
        case 1:
            queue = search_result.slice(0, display_limit);
            break;
        case 2:
            queue = certain;
            break;
        case 3:
            queue = uncertain;
            break;
        case 4:
            queue = ["smart"];
            break;
        default:
            queue = ["smart"];
            break;
    }

    $.ajax({
        type: "POST",
        url: "/autoreview",
        async: true,
        data: {"queue": JSON.stringify(queue)},
        success: autoreview_receive
    });
}

function autoreview_receive(response) {
    if (response != "none") {
        display_num_labeled(response.num_labeled, response.num_pos);
    }
}

function highlight(what, which) {
    var text=what._source.text;
    if (which == "search") {
        try {
            text=what.highlight["text._analyzed"];
        }
        catch(err){
            text=what._source.text;
        }
        return text;
    }
    else {
        var ind = [];
        for (var i = 0; i < coef.length; ++i) {
            ind.push(i);
        }
        ind.sort(function (a, b) {
            return Math.abs(coef[b]) - Math.abs(coef[a])
        });
        var redones = [];
        var greenones = [];
        for (var i = 0; i < Math.min(display_limit, voc.length); ++i) {
            if (coef[ind[i]] > 0) {
                if(ind[i]<voc.length){
                    greenones.push(voc[ind[i]]);
                }                
            }
            else if (coef[ind[i]] < 0) {
                if(ind[i]<voc.length){
                    redones.push(voc[ind[i]]);
                }          
            }
        }
        var exp = /(\w+)/g;

        function redorgreen(match) {
            if (greenones.indexOf(stemmer(match.toLowerCase())) > -1) {
                var color=parseInt(greenones.indexOf(stemmer(match.toLowerCase()))/greenones.length*100);
                var term = voc.indexOf(stemmer(match.toLowerCase()));
                return "<span data-term="+term.toString()+" class='tooltip' onclick='get_concurrency(this)' style='background-color: rgb("+color.toString()+","+(color+150).toString()+","+color.toString()+")'>" + match + "<span class='tooltiptext'>" + "coef: " + coef[term].toFixed(3) + "<br> stats: " + more_coef[term].pos + "/" + more_coef[term].all + "</span></span>";
            }
            else if (redones.indexOf(stemmer(match.toLowerCase())) > -1) {
                var color=parseInt(redones.indexOf(stemmer(match.toLowerCase()))/redones.length*100);
                var term = voc.indexOf(stemmer(match.toLowerCase()));
                return "<span data-term="+term.toString()+" class='tooltip' onclick='get_concurrency(this)' style='background-color: rgb("+(color+150).toString()+","+color.toString()+","+color.toString()+")'>" + match + "<span class='tooltiptext'>" + "coef: " + coef[term].toFixed(3) + "<br> stats: " + more_coef[term].pos + "/" + more_coef[term].all + "</span></span>";
            }
            else {
                return match;
            }
        }

        return text.replace(exp, redorgreen);
    }
}

window.onclick = function(event) {
    if (event.target == document.getElementById('myModal')) {
        document.getElementById('myModal').style.display = "none";
    }
};

function get_concurrency(obj){
    term=Number(obj.getAttribute("data-term"));
    $.ajax({
        type: "POST",
        url: "/get_concurrency",
        async: true,
        data: {
            term: term
        },
        success: show_concurrency
    });
}

function show_concurrency(res){
    term=res.term;
    concurrency = res.concurrency;
    var concurrency_scores = res.concurrency_scores;
    document.getElementById('myModal').style.display = "block";
    var olnode = document.getElementById("terms");
    while (olnode.firstChild) {
        olnode.removeChild(olnode.firstChild);
    }
    for (var i = 0; i < concurrency.length; ++i) {
        if (concurrency[i]>=voc.length) continue;
        var newli = document.createElement("li");
        var node = document.createTextNode(voc[term]+" + "+voc[concurrency[i]]+": "+concurrency_scores[i].toString());
        var what = [term, concurrency[i]];
        newli.appendChild(node);
        newli.setAttribute("value", i);
        newli.setAttribute("onclick", "add_on(this)");

        if (indexof(addon,what)>-1){
            newli.setAttribute("style", "color: yellow");
        }

        olnode.appendChild(newli);
    }
}

function add_on(li){
    var what = [term, concurrency[li.value]];
    var flag = edit_addon(what);
    if (flag){
        li.setAttribute("style", "color: yellow");
    }
    else{
        li.setAttribute("style", "color: white");
    }
}



function indexof(a,b){
    
    function setsEqual(a,b){
        if (a.size !== b.size)
            return false;
        return a.filter(function(i){return b.indexOf(i)<0}).length==0;
    }
    
    for (var i = 0; i < a.length; ++i){
        if (setsEqual(b,a[i])){
            return i;
        }
    }
    return -1;
}    

function edit_addon(what){
    
    var tmp_index = indexof(addon,what);
    if (tmp_index > -1) {
        addon.splice(tmp_index, 1);
        return false;
    }
    else{
        addon.push(what);
        return true;
    }
}

