

//Vis.js population adding code
function addNode(nID,nLabel,nColor = '#7BE141',nValue=25, pozX=0, pozY=0) {
try {
    nodes.add({ id: nID, label: nLabel , value: nValue, x: pozX, y:pozY, color: nColor, shape: 'dot', font: { size:40,  strokeWidth:5, strokeColor:'#ffffff'}});
  }
catch (err) {
  alert(err);
  }
}

function addEdge(nID,nTo,nFrom, nValue =1) {
   try {
       edges.add({ id: nID, from: nTo, to: nFrom, value: nValue, arrows:'to'});
   }
   catch (err) {
       alert(err);
   }
}
function populateGraph (nodeData,edgeData, locationList = {}){
  console.log("Adding nodes :" + nodeData.length);
  for( var i=0; i< nodeData.length; i++){
      var current = nodeData[i];
      var x =0;
      var y= 0;
      // 200 000 SAT is min chan size
      var size = (current.channels+1)*30;
      if ( current.pub_key in locationList){  //Use cached coords in possible
        x= locationList[current.pub_key]["x"];
        y= locationList[current.pub_key]["y"];
      }

      addNode(current.pub_key,current.alias,current.color,size,x,y);
      // console.log("Now node :" + i + " pubkey:" + current.pub_key + " at x,y " + x + ":" + y);
  }
  console.log("Adding edges :" + edgeData.length);
  for( var i=0; i< edgeData.length; i++){
      var current = edgeData[i];
      addEdge(current.chan_id,current.node2_pub,current.node1_pub,current.capacity/10**2);
      // console.log("Now edge :" + i + "\t "+ current.chan_id );
      // console.log("Between :" + current.node2_pub + "\t "+ current.node1_pub + "\tCapacity:" + current.capacity );
  }
}

function addLabels(edgeSet,edgeData){
  for(var i=0; i< edgeData.length;i++){
      edgeSet.update([{id: edgeData[i]["chan_id"], label: edgeData[i]["capacity"] + " SAT" }]);
    }
}


//Copied the default values
//Found at http://visjs.org/examples/network/other/animationShowcase.html
var offsetx =0 ;
var offsety= 0 ;
var scale= 1.0;
var duration=1.0;
var easingFunction = "easeInOutQuad";
function focusRandom() {
  var testNodeID = "02f82a1188bb4baa885de6c0d14276db056aa9da768de545c4fc7349379b5670cb"; //TODO REMOVE THIS
  var nodeId = testNodeID
  var options = {
    // position: {x:positionx,y:positiony}, // this is not relevant when focusing on nodes
    scale: scale,
    offset: {x:offsetx,y:offsety},
    animation: {
      duration: duration,
      easingFunction: easingFunction
    }
  };

  network.focus(nodeId, options);
}
