/**
 * Created by Natasha on 01-02-2016.
 */

google.charts.load("current", {packages:['corechart']});
google.charts.setOnLoadCallback(function() {drawChart([])});

var chartData = [];

function drawChart(dataArray, userArray, logArray) {
    var data = google.visualization.arrayToDataTable(dataArray);

    var view = new google.visualization.DataView(data);
    view.setColumns([0, 1,
                    { calc: "stringify",
                        sourceColumn: 1,
                        type: "string",
                        role: "annotation" }, 2,
                    { calc: "stringify",
                        sourceColumn: 2,
                        type: "string",
                        role: "annotation" },
                    3]);

    var options = {
        title: "Duration of "+ dataArray[0][0] +" in Days",
        width: 700,
        height: 500,
        animation:{
            duration:1000,
            startup: true
        }
    };
    var pieData = google.visualization.arrayToDataTable(userArray);
    var optionsPieChart = {
        legend: {position: 'labeled'},
        is3D: false,
        pieHole: 0,
        chartArea:{width:'92%',height:'92%'},
        pieSliceText: 'value'
    };
    var piechart = new google.visualization.PieChart(document.getElementById("piechart_values"));
    piechart.draw(pieData, optionsPieChart);

    var pieLogData = google.visualization.arrayToDataTable(logArray);
    var optionsLogPieChart = {
        legend: {position: 'labeled'},
        is3D: false,
        pieHole: 0,
        chartArea:{width:'92%',height:'92%'},
        pieSliceText: 'value'
    };
    var logPiechart = new google.visualization.PieChart(document.getElementById("piechart_users"));
    logPiechart.draw(pieLogData, optionsLogPieChart);

    var chart = new google.visualization.ColumnChart(document.getElementById("columnchart_values"));
    var runFirstTime = google.visualization.events.addListener(chart, 'ready', function(){
        google.visualization.events.removeListener(runFirstTime);
        chart.draw(data, options);
    });
    chart.draw(data, options);
}


//Doesn't need to be a seperate function, but now I know how callbacks work!
function getDataFromServer(project, sequence, shot, callback){
    $.ajax({
        type:"POST",
        url: "/load_chart",
        data: {
            project: project,
            sequence: sequence,
            shot: shot
        },
        dataType: 'json',
        success:function(data){
            callback(data);
        },
        error: function(){
            $("#loader").hide();
            $("#fail").show();
        }
    });
}

$("#projects").change(function() {
    $.ajax({
        type: "POST",
        url: "/change_sequence",
        data: {
            project: $("#projects").val()
        },
        success: function (data) {
            $("#sequences").html(data);
            $("#shots").empty()
        }
    });
});

$("#sequences").change(function() {
    $.ajax({
        type: "POST",
        url: "/change_shot",
        data: {
            project: $("#projects").val(),
            sequence: $("#sequences").val()
        },
        success: function(data) {
            $("#shots").html(data);
        }
    });
});

$("#submit").bind('click', function() {
    $("#loader").show();
    $("#done").hide();
    $("#fail").hide();
    $("#filename").hide();
    project = $("#projects").val();
    sequence = $("#sequences").val();
    shot = $("#shots").val();
    getDataFromServer(project, sequence, shot, function(chartData){
        if (chartData[0] === undefined || chartData[0].length == 0) {
            alert("error");
        }
        else {
            $("#loader").hide();
            $("#done").show();
            $("#bid-panel").show();
            $("#user-panel").show();
            $("#user-panel2").show();
            drawChart(chartData[0], chartData[1], chartData[2]);
        }
    });
});

$("#export").bind('click', function () {
    $("#loader").show();
    $("#done").hide();
    $("#fail").hide();
    $("#filename").hide();
    $.ajax({
        type: "POST",
        url: "/export_data",
        data: {
            project: $("#projects").val()
        },
        success: function (data) {
            $("#loader").hide();
            $("#done").show();
            $("#filename").show();
            $("#filename").val("Exported to: "+data)
        },
        error: function () {
            $("#loader").hide();
            $("#fail").show();
            $("#filename").hide();
        }
    });
});


