var map = L.map('map',{zoomControl: false}).setView([48.14, 17.12], 10);
L.control.zoom({position: 'bottomright'}).addTo(map);

// Geocoder with marker removable on click

// var geocoder = L.Control.geocoder({
//   defaultMarkGeocode: false
// }).addTo(map);

//   var marker;

//   geocoder.on('markgeocode', function(e) {
//     if (marker) {
//       map.removeLayer(marker);
//     }
//     marker = L.marker(e.geocode.center).addTo(map);
//   });

//   map.on('click', function(e) {
//     if (marker) {
//       map.removeLayer(marker);
//       marker = null;
//     }
//   });

// Geocoder with marker removable with x button

var geocoder = L.Control.geocoder({
  defaultMarkGeocode: false
}).addTo(map);

  var marker;

  geocoder.on('markgeocode', function(e) {
      marker = L.marker(e.geocode.center).addTo(map);
      marker
        .bindPopup( "Center Marker" , {removable: true} )
        .addTo(leafletMap)
    // marker = L.marker(e.geocode.center).addTo(map);
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

