function get_logged_time_unix(){
  var split_url = window.location.href.split("/");
  return   split_url[split_url.length - 1]
}
// Needs a defined "network" variable
// Put after definitions
// Get info on mouse click

network.on("click", function (params) {
    params.event = "[original event]";
    // document.getElementById('eventSpan').innerHTML = '<h2>Click event:</h2>' + JSON.stringify(params, null, 4);
    console.log('click event, getNodeAt returns: ' + this.getNodeAt(params.pointer.DOM));
  });

// Redirect, on double click, to corresponding node or payment channels
  network.on("doubleClick", function (params) {
      params.event = "[original event]";
      var network = window.location.href.split("/")[3];
      if(network != "mainnet" && network != "testnet"){
        return;
      }

      inspectMe = this.getNodeAt(params.pointer.DOM);
      console.log('double click event, getNodeAt returns: ' + inspectMe);
      if(inspectMe != null){
        console.log("Double Clicked on a node");
        console.log("Redirecting to:\t" + network+"/node/" + inspectMe);
        // document.location.href= "/"+ network + "/node/" + inspectMe + "/"+ get_logged_time_unix() ;
        window.open("/"+ network + "/node/" + inspectMe + "/"+ get_logged_time_unix(),'_blank');
      }
      else{
        inspectMe3 = params;
        // console.log("double click params: "+ params);

        if(params["edges"].length > 0){
          console.log("Double Clicked on edge/channel: " + params["edges"][0] );
          // document.location.href= "/"+ network + "/channel/" + params["edges"][0]+  "/"+ get_logged_time_unix() ;
          window.open("/"+ network + "/channel/" + params["edges"][0]+  "/"+ get_logged_time_unix(),'_blank');
        }
      }
  });


  //Node selection tools
  document.getElementById("node_capacity").onclick = function(evt){
    var activePoints = chart_capacity.getElementsAtEvent(evt);
    var result =activePoints[0];
    console.log(result);
    if(chart_capacity.data.datasets[result._datasetIndex]["data"][result._index].x){
      var site_now =window.location.href ;
      var time_now = chart_capacity.data.datasets[result._datasetIndex]["data"][result._index].x;

      var new_site= site_now.split("/");
      console.log(chart_capacity.data.datasets[result._datasetIndex]["data"][result._index].x);
      //Get the unix time for the UTC timezone
      var time_picked_unix =(new Date(time_now + "Z")).getTime() / 1000
      if(site_now.split("/").length == 7){
        new_site[6]=time_picked_unix;
      }
      else{
        new_site.push(time_picked_unix);
      }
      window.location.href = new_site.join("/");
    }};

  document.getElementById("node_channels").onclick = function(evt){
    var activePoints = chart_channels.getElementsAtEvent(evt);
    var result =activePoints[0];
    console.log(result);
    if(chart_channels.data.datasets[result._datasetIndex]["data"][result._index].x){
      var site_now =window.location.href ;
      var time_now = chart_channels.data.datasets[result._datasetIndex]["data"][result._index].x;

      var new_site= site_now.split("/");
      console.log(chart_channels.data.datasets[result._datasetIndex]["data"][result._index].x);
      //Get the unix time for the UTC timezone
      var time_picked_unix =(new Date(time_now + "Z")).getTime() / 1000
      if(site_now.split("/").length == 7){
        new_site[6]=time_picked_unix;
      }
      else{
        new_site.push(time_picked_unix);
      }
      window.location.href = new_site.join("/");
    }
  };
