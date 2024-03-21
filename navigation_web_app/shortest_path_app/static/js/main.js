var map = L.map('map',{zoomControl: false}).setView([48.14, 17.12], 10);
L.control.zoom({position: 'bottomright'}).addTo(map);
// My location button
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

// Geocoder with marker removable with x button

// var geocoder = L.Control.geocoder({
//   defaultMarkGeocode: false
// }).addTo(map);

//   var marker;

//   geocoder.on('markgeocode', function(e) {
//       marker = L.marker(e.geocode.center).addTo(map);
//       marker
//         .bindPopup( "Center Marker" , {removable: true} )
//         .addTo(leafletMap)
//     // marker = L.marker(e.geocode.center).addTo(map);
//   });



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
function onMapClick(e) {
  var button = L.DomUtil.create('button', 'popup-button');
  button.innerHTML = 'Direction from here';
  button.id = 'popup_btn';

  button.addEventListener('click', function() {
    alert('Button clicked!');
  });

  marker = L.marker([e.latlng.lat, e.latlng.lng])
    .bindPopup("You clicked the map at " + e.latlng.toString() + '<br>').addTo(map)
    .bindPopup("You clicked the map at " + e.latlng.toString() + '<br>').addTo(map)
    .openPopup()
    .bindPopup(button)
    .addTo(map);
}

map.on('click', onMapClick);


// Start and end point + pass coordinates to django view
// var startPoint = null;
// var endPoint = null;

// function onMapClick(e) {
//   if (startPoint === null) {
//     // First click: Set starting point
//     startPoint = e.latlng;
//     L.marker(startPoint).addTo(map).bindPopup("Starting point").openPopup();
//   } else if (endPoint === null) {
//     // Second click: Set ending point
//     endPoint = e.latlng;
//     L.marker(endPoint).addTo(map).bindPopup("Ending point").openPopup();

//     // Calculate route
//     calculateRoute(startPoint, endPoint);

//     // Reset points for next route calculation
//     startPoint = null;
//     endPoint = null;
//   }
// }

// function calculateRoute(startPoint, endPoint) {
//   // Prepare data to send to Django view
//   var data = {
//     start_lat: startPoint.lat,
//     start_lng: startPoint.lng,
//     end_lat: endPoint.lat,
//     end_lng: endPoint.lng
//   };

//   // Make AJAX request to Django view
//   // Example using jQuery AJAX
//   $.ajax({
//     url: '/your_django_route_view/',
//     method: 'POST',
//     data: data,
//     success: function(response) {
//       // Handle successful response from Django
//       console.log(response);
//     },
//     error: function(xhr, status, error) {
//       // Handle error
//       console.error(xhr.responseText);
//     }
//   });
// }

// map.on('click', onMapClick);
