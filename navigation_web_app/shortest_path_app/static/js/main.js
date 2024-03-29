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

const layerControl = L.control.layers(baseMaps,overlayMaps).addTo(map);



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
var startPoint = null;
var endPoint = null;

var greenIcon = L.icon({
  iconUrl: 'leaf-green.png',
});

var redIcon = L.icon({
  iconUrl: 'leaf-green.png',
});

function onMapClick(e) {
  let route_markers = L.featureGroup().addTo(map);

  if (startPoint === null) {
    let button = L.DomUtil.create('button', 'popup-button');
    button.innerHTML = 'Direction from here';
    button.id = 'popup_btn';

    startPoint = e.latlng;
    let marker_button = L.marker(startPoint)
      .addTo(map)
      .bindPopup(button)
      .openPopup();
    route_markers.addLayer(marker_button);

    button.addEventListener('click', function() {
      route_markers.clearLayers();
      marker_start = L.marker(startPoint)
        .addTo(map)
        .bindPopup("Start point")
        .openPopup();
      route_markers.addLayer(marker_start);
    });
    
    
  } else if (endPoint === null) {
    endPoint = e.latlng;
    let marker_end = L.marker(endPoint).addTo(map).bindPopup("Ending point").openPopup();
    marker_end._icon.classList.add("huechange");
    route_markers.addLayer(marker_end);
  }


  function showButton() {
    document.getElementById('deleteButton').style.display = 'block';
  }

  document.getElementById('deleteButton').addEventListener('click', function() {
    route_markers.clearLayers();
    startPoint = null;
    endPoint = null;
    this.style.display = 'none';
  });

  showButton();
  
  // Calculate route
  startPoint_route = [startPoint.lng, startPoint.lat];
  endPoint_route = [endPoint.lng, endPoint.lat];
  let route = calculateRoute(startPoint, endPoint);

  // Plot shortest path
  L.geoJSON(route, {
    style: function (feature) {
        return {
            color: 'blue', 
            weight: 3      
        };
    }
  }).addTo(map);
}

// Functions using AJAX to send data to Django view
function calculateRoute(startPoint, endPoint) {
  const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;
  // let data = {
  //   'start_lat': startPoint.lat,
  //   'start_lon': startPoint.lng,
  //   'end_lat': endPoint.lat,
  //   'end_lon': endPoint.lng
  // };

  let data = {
    'start_lat': 48.13981270510992,
    'start_lon': 17.108043371743726,
    'end_lat': 48.146124356029965, 
    'end_lon': 17.127030258137136
  };

  $.ajax({
    url: '/directions/',
    type: 'POST',
    headers: {'X-CSRFToken': csrftoken},
    mode: 'same-origin',
    data: JSON.stringify(data),
    success: function(response) {
      var geojsonFeature = JSON.parse(response);
      var myStyle = {
        "color": "#ff7800",
        "weight": 5,
        "opacity": 0.65
    };
      var geojsonLayer = L.geoJSON(geojsonFeature, {style:myStyle}).addTo(map);
      // map.fitBounds(geojsonLayer.getBounds());
    },
    error: function(xhr, errmsg, err) {
        console.log(xhr.status + ": " + xhr.responseText); 
    }
  });
}



map.on('click', onMapClick);