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
      inspectMe = this.getNodeAt(params.pointer.DOM);
      console.log('double click event, getNodeAt returns: ' + inspectMe);
      if(inspectMe != null){
        console.log("Double Clicked on a node");
        console.log("Redirecting to:\t" + "/nodes/" + inspectMe);
        document.location.href= "/nodes/" + inspectMe ;
      }
      else{
        inspectMe3 = params;
        console.log("double click params: "+ params);

        if(params["edges"].length > 0){
          console.log("Double Clicked on edge/channel: " + params["edges"][0] );
          document.location.href= "/channels/" + params["edges"][0]  ;
        }
      }
  });
