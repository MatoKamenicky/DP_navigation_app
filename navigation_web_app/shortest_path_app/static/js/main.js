// Map + zoom +location
var map = L.map('map',{zoomControl: false}).setView([48.14, 17.12], 10);
L.control.zoom({position: 'bottomright'}).addTo(map);
L.control.locate({position:'topright'}).addTo(map);

// Geocoder with marker removable on click

var geocoder = L.Control.geocoder({
  defaultMarkGeocode: false
}).addTo(map);

  var marker;

  geocoder.on('markgeocode', function(e) {
    if (marker) {
      map.removeLayer(marker);
    }
    marker = L.marker(e.geocode.center).addTo(map);
  });

  map.on('click', function(e) {
    if (marker) {
      map.removeLayer(marker);
      marker = null;
    }
  });

// Add layers
osm = L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
maxZoom: 19,
attribution: '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>'
}).addTo(map);

L.tileLayer('https://{s}.tile.osm.org/{z}/{x}/{y}.png', {
  attribution: '&copy; <a href="https://osm.org/copyright">OpenStreetMap</a> contributors'
}).addTo(map);

googleSat = L.tileLayer('http://{s}.google.com/vt?lyrs=s&x={x}&y={y}&z={z}',{
maxZoom: 20,
subdomains:['mt0','mt1','mt2','mt3']
});

googleStreets = L.tileLayer('http://{s}.google.com/vt?lyrs=m&x={x}&y={y}&z={z}',{
maxZoom: 20,
subdomains:['mt0','mt1','mt2','mt3']
});

var baseMaps = {
"OpenStreetMap": osm,
"Google Map": googleStreets,
"Google Satellite": googleSat,
};

//Add markers with bridges
let geojson_data = JSON.parse(document.getElementById('geojson_points').textContent);
let bridgeFeatureGroup = L.featureGroup();

geojson_data.features.forEach(pointik => {
L.marker([pointik.geometry.coordinates[1], pointik.geometry.coordinates[0]]).bindPopup(pointik.properties.name).addTo(bridgeFeatureGroup);
});
let overlayMaps = {"Bridge": bridgeFeatureGroup};

var layerControl = L.control.layers(baseMaps,overlayMaps).addTo(map);



// Marker on click

// function onMapClick(e) {
//   marker = L.marker([e.latlng.lat , e.latlng.lng])
//   .bindPopup("You clicked the map at " + e.latlng.toString())
//   .addTo(map);
// }
// map.on('click', onMapClick);

// Popup for markers with button
// function onMapClick(e) {
//   var button = L.DomUtil.create('button', 'popup-button');
//   button.innerHTML = 'Direction from here';
//   button.id = 'popup_btn';

//   button.addEventListener('click', function() {
//     alert('Button clicked!');
//   });

//   marker = L.marker([e.latlng.lat, e.latlng.lng])
//     .bindPopup("You clicked the map at " + e.latlng.toString() + '<br>').addTo(map)
//     .bindPopup("You clicked the map at " + e.latlng.toString() + '<br>').addTo(map)
//     .openPopup()
//     .bindPopup(button)
//     .addTo(map);
// }

// map.on('click', onMapClick);


// Start and end point + pass coordinates to django view

function clearMarkers() {
  if (marker) {
      map.removeLayer(marker);
  }
  if (endPointMarker) {
      map.removeLayer(endPointMarker);
  }
  startPoint = null;
  endPoint = null;
}


var startPoint = null;
var endPoint = null;

function onMapClick(e) {
  if (startPoint === null) {
    var button = L.DomUtil.create('button', 'popup-button');
    button.innerHTML = 'Direction from here';
    button.id = 'popup_btn';

    startPoint = e.latlng;
    marker = L.marker(startPoint)
      .addTo(map)
      .bindPopup(button)
      .openPopup();

    button.addEventListener('click', function() {;
        marker = L.marker(startPoint)
          .addTo(map)
          .bindPopup("Start point")
          .openPopup();
    });

  } else if (endPoint === null) {
    
    endPoint = e.latlng;
    L.marker(endPoint).addTo(map).bindPopup("Ending point").openPopup();
    // // Calculate route
    // calculateRoute(startPoint, endPoint);

    // // Plot shortest path
    // let geojson_data = JSON.parse(document.getElementById('geojson_shortest_path').textContent);

    // geojson_data.features.forEach(pointik => {
    // L.polyline([pointik.geometry.coordinates[1], pointik.geometry.coordinates[0]]).bindPopup(pointik.properties.name).addTo(bridgeFeatureGroup);
    // });



    // Reset points for next route calculation
    startPoint = null;
    endPoint = null;
  }
}


// Functions using AJAX to send data to Django view

function calculateRoute(startPoint, endPoint) {
  var data = {
    start_lat: startPoint.lat,
    start_lng: startPoint.lng,
    end_lat: endPoint.lat,
    end_lng: endPoint.lng
  };

  // Make AJAX request to Django view
  $.ajax({
    url: '/route_view',
    method: 'POST',
    data: data,
    success: function(response) {
      // Handle successful response from Django
      console.log(response);
    },
    error: function(xhr, status, error) {
      // Handle error
      console.error(xhr.responseText);
    }
  });
}

function makeid(length) {
  var data = {
    start_lat: startPoint.lat,
    start_lng: startPoint.lng,
    end_lat: endPoint.lat,
    end_lng: endPoint.lng
  };
  $.ajax({
      type: "GET",
      url: '/route_view',
      data: data,
      dataType: "json",
      success: function (data) {
          alert("successfull")
      },
      failure: function () {
          alert("failure");
      }
  });
}


map.on('click', onMapClick);
