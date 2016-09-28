// custom javascript

queue()
    .defer(d3.json, '/plotdata')
    .await(renderMyCharts);

function renderMyCharts(error, data_dict) {

    function uniqByKey(a, key) {
        var seen = {};
        return a.filter(function (item) {
            var k = key(item);
            return seen.hasOwnProperty(k) ? false : (seen[k] = true);
        })
    }

    var data = uniqByKey(data_dict.result, JSON.stringify);
    f1ScoreVsTrainingRound(error, data);
    turnoversVsTrainingRound(error, data);
    completeDataTable(error, data);
    wordBubble(error, data);
}

// Get JQuery to post data
$.ajax({
    type: "POST",
    url: "/init",
    async: true,
    data: {},
    success: renderMyMetrics
});

function renderMyMetrics(response) {
    document.getElementById("d3-metric-train").innerText = "Responsive: " + response.num_pos.toString() + ". Total: " + response.num_labeled.toString();
    document.getElementById("d3-metric-control").innerText = "Responsive: " + response.control_pos.toString() + ". Total:  " + response.num_control.toString();
}

function wordBubble(error, data0) {

    var margin = {"top": 30, "right": 20, "bottom": 30, "left": 50};
    var width = 480 - margin.left - margin.right;
    var height = 360 - margin.top - margin.bottom;
    var format = d3.format(",d"),
        colour = d3.scale.linear()
            .domain([-1, 0, 1])
            .range(['red', 'green']),
        sizeOfRadius = d3.scale.pow().domain([5, 5]).range([-50, 50]);
    var totalRounds = d3.max(data0, function (d) { return d.the_round; });
    var data = data0[totalRounds-1].key_terms
        .reverse()
        .slice(0,49);
    
    // Configure the bubble
    var bubble = d3.layout.pack()
        .sort(null)
        .size([width, height])
        .padding(1)
        .radius(function (d) {
            return 20 + (sizeOfRadius(d) * 60);
        });

    // Create an SVG canvas
    var svg = d3.select("#d3-key-terms").append("svg")
        .attr("width", width)
        .attr("height", height)
        .attr("class", bubble);

    // Tooltip config
    var tooltip = d3.select("d3-key-terms")
        .append("div")
        .style("position", "absolute")
        .style("z-index", "10")
        .style("visibility", "hidden")
        .style("color", "white")
        .style("padding", '8px')
        .style("background-color", "rgba(0,0,0,0.66)")
        .style("border-radius", "6px")
        .style("font", "12px sans-serif")
        .text("tooltip");

    // Work on data
    var node = svg.selectAll(".node")
        .data(bubble.node(data))
        .enter().append("g")
        .attr("class", "node")
        .attr("transform", function (d) {
            return "translate(" + d.x + d.y + ")";
        });

    node.append("circle")
        .attr("r", function (d) {
            return d.r;
        })
        .style('fill', function (d) {
            return color(d.coef_val);
        })
        .on("mouseover", function (d) {
            tooltip.text(d.coef_name + ": " + d.coef_val);
            tooltip.style("visibility", "visible");
        })
        .on("mousemove", function (d) {
            return tooltip.style("top", (d3.event.pageY - 10) + "px").style("left", (d3.event.pageX + 10) + "px");
        })
        .on("mouseout", function (d) {
            return tooltip.style("visibility", "visible");
        });

    node.append('text')
        .attr("dy", ".3em")
        .style('text-anchor', 'middle')
        .text(function (d) {
            return d.coef_name;
        });
}

function f1ScoreVsTrainingRound(error, data) {

    // Set dimensions of data
    var margin = {"top": 30, "right": 20, "bottom": 30, "left": 50};
    var width = 480 - margin.left - margin.right;
    var height = 360 - margin.top - margin.bottom;
    console.log(data);


    // Find scaling ranges
    var x = d3.scale.linear()
        .range([0, width]);

    var y = d3.scale.linear()
        .domain([0, 1])
        .range([height, 0]);

    // Define Axes
    var xAxis = d3.svg.axis()
        .scale(x)
        .orient("bottom");

    var yAxis = d3.svg.axis()
        .scale(y)
        .orient("left")
        .ticks(5);

    // Define a line
    var myLine = d3.svg.line()
        .x(function (d) {
            return x(d.the_round);
        })
        .y(function (d) {
            return y(d.fscore.F1);
        });

    // Create an SVG canvas
    var svg = d3.select("#d3-fscores")
        .append("svg")
        .attr("width", width + margin.left + margin.right)
        .attr("height", height + margin.top + margin.bottom)
        .append("g")
        .attr("transform", "translate(" + margin.left + "," + margin.top + ")");


    data.forEach(function (d) {
        d.fscore.F1 = +d.fscore.F1;
        d.the_round = +d.the_round;
    });

    var totalRounds = d3.max(data, function (d) {
        return d.the_round;
    });

    svg.append("text")
        .attr("class", "xlabel")
        .attr("text-anchor", "end")
        .attr("x", width)
        .attr("y", height - 6)
        .text("Training Round");


    // Update X's domain info.
    x.domain([0.5, totalRounds]);

    // Set ticks on X Axis
    xAxis.ticks(totalRounds);

    // Define path the line must take
    svg.append("path")
        .attr("class", "line")
        .attr("d", myLine(data));

    // Add the X Axis
    svg.append("g")
        .attr("class", "x axis")
        .attr("transform", "translate(" + "0," + height + ")")
        .call(xAxis);

    svg.append("g")
        .attr("class", "y axis")
        .call(yAxis);

    // });
}

function turnoversVsTrainingRound(error, data) {

    // Set dimensions of data
    var margin = {"top": 30, "right": 20, "bottom": 30, "left": 50};
    var width = 480 - margin.left - margin.right;
    var height = 360 - margin.top - margin.bottom;
    console.log('this');


    // Find scaling ranges
    var x = d3.scale.linear()
        .range([0, width]);

    var y = d3.scale.linear()
        .range([height, 0]);

    // Define Axes
    var xAxis = d3.svg.axis()
        .scale(x)
        .orient("bottom");

    var yAxis = d3.svg.axis()
        .scale(y)
        .orient("left")
        .ticks(5);

    // Define a line
    var myLine = d3.svg.line()
        .x(function (d) {
            return x(d.the_round);
        })
        .y(function (d) {
            return y(d.num_turnovers);
        });

    // Create an SVG canvas
    var svg = d3.select("#d3-turnovers")
        .append("svg")
        .attr("width", width + margin.left + margin.right)
        .attr("height", height + margin.top + margin.bottom)
        .append("g")
        .attr("transform", "translate(" + margin.left + "," + margin.top + ")");


    // d3.json("/plotdata", function (error, data_dict) {


    data.forEach(function (d) {
        d.num_turnovers = +d.num_turnovers;
        d.the_round = +d.the_round;
    });

    var totalRounds = d3.max(data, function (d) {
        return d.the_round;
    });

    // Update X's domain info.
    x.domain([0.5, totalRounds]);

    // Update Y's domain info.
    y.domain([0.5, d3.max(data, function (d) {
        return d.num_turnovers + 10;
    })]);

    // Set ticks on X Axis
    xAxis.ticks(totalRounds);

    svg.append("text")
        .attr("class", "xlabel")
        .attr("text-anchor", "end")
        .attr("x", width)
        .attr("y", height - 6)
        .text("Training Round");

    // Define path the line must take
    svg.append("path")
        .attr("class", "line")
        .attr("d", myLine(data));

    // Add the X Axis
    svg.append("g")
        .attr("class", "x axis")
        .attr("transform", "translate(" + "0," + height + ")")
        .call(xAxis);

    svg.append("g")
        .attr("class", "y axis")
        .call(yAxis);

    // });
}

function completeDataTable(error, data) {
    var margin = {"top": 30, "right": 20, "bottom": 30, "left": 50};
    var columns = [
        {
            title: "Training Round",
            key: "the_round"
        },
        {
            title: "Recall",
            key: "Sen"
        },
        {
            title: "Precision",
            key: "Prec"
        },
        {
            title: "F1 Score",
            key: "F1"
        },
        {
            title: "Overturns",
            key: "num_turnovers"
        },
        {
            title: "Consistent?",
            key: "consistency"
        }
    ];
    var table = d3.select("#d3-data-table")
            .attr("style", "margin-left: " + margin.right.toString() + "px"),
        thead = table.append("thead"),
        tbody = table.append("tbody");

    // append the header row
    thead.append("tr")
        .selectAll("th")
        .data(columns)
        .enter()
        .append("th")
        .text(function (column) {
            return column.title;
        });

    // d3.json('/plotdata', function (error, data_dict) {

    // create a row per element in the data
    var rows = tbody.selectAll("tr")
        .data(data)
        .enter()
        .append("tr");
    var d3_format = d3.format("0.2f");
    // create a cell per row and column
    var cells = rows.selectAll("td")
        .data(function (row) {
            return columns.map(function (column) {
                if (column.key == 'F1')
                    return {
                        column: column,
                        value: d3_format(row['fscore'][column.key])
                    };

                if (column.key == 'Prec')
                    return {
                        column: column,
                        value: d3_format(row['fscore'][column.key])
                    };

                if (column.key == 'Sen')
                    return {
                        column: column,
                        value: d3_format(row['fscore'][column.key])
                    };

                if (column.key == 'consistency')
                    return {
                        column: column,
                        value: row[column.key].toFixed(2)
                    };

                else
                    return {column: column, value: row[column.key]};

            })
        })
        .enter()
        .append("td")
        .attr("style", "font-family: Courier")
        .html(function (d) {
            return d.value;
        });
}

