// Map + zoom +location
var map = L.map('map',{zoomControl: false}).setView([48.14, 17.12], 13);
L.control.locate({position:'topright'}).addTo(map);
var searchControl = L.Control.geocoder({
  defaultMarkGeocode: false,
  collapsed: true,
}).addTo(map);
L.control.zoom({position: 'bottomleft'}).addTo(map);

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

// Start and end point + pass coordinates to django view
var startPoint = null;
var endPoint = null;


let routeLayer;
let route_markers = L.featureGroup().addTo(map);
var greenIcon = new L.Icon({
  iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-green.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41]
});

var redIcon = new L.Icon({
  iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-red.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41]
});
let button = L.DomUtil.create('button', 'popup-button');
button.innerHTML = 'Direction from here';
button.id = 'popup_btn';

// Toggle button for select path type - time or distance
var pathTypeSelect = document.getElementById('pathType');
function getToggleValue() {
  if (pathTypeSelect.checked) {
      return "time";
  } else {
      return "length";
    }
};

// Geocoder marker with popup button direction from here - same as popup button in marker on click
searchControl.on('markgeocode', function(e) {
  if (!startPoint) {
    startPoint = e.geocode.center;
    map.setView(startPoint, 18);

    let marker_button = L.marker(startPoint)
      .addTo(map)
      .bindPopup(button)
      .openPopup();
    route_markers.addLayer(marker_button);

    button.addEventListener('click', function() {
      route_markers.clearLayers();
      let marker_start = L.marker(startPoint, { icon: greenIcon })
        .addTo(map)
        .bindPopup("Start point")
        .openPopup();
      marker_start.addTo(route_markers);
    });

    function showButton() {
      document.getElementById('deleteButton').style.display = 'block';
    }

    document.getElementById('deleteButton').addEventListener('click', function() {
      route_markers.clearLayers();
      if (routeLayer) {
        map.removeLayer(routeLayer);
        routeLayer = null;
      }
      startPoint = null;
      endPoint = null;
      this.style.display = 'none';
    });

    showButton();
  } else if (!endPoint) {
    endPoint = e.geocode.center;

    let marker_end = L.marker(endPoint, { icon: redIcon })
      .addTo(map)
      .bindPopup("End point")
      .openPopup();
    marker_end.addTo(route_markers);

    // Calculate route
    let type = getToggleValue();
    console.log(type);
    let car_weight = document.getElementById('id_weight').value;
    let route = calculateRoute(startPoint, endPoint, car_weight, type);
    map.closePopup();
  }
})

// Marker on click with direction from here popup button
function onMapClick(e) {
  if (startPoint === null) {
    startPoint = e.latlng;
    let marker_button = L.marker(startPoint)
      .addTo(map)
      .bindPopup(button)
      .openPopup();
    route_markers.addLayer(marker_button);

    button.addEventListener('click', function() {
      route_markers.clearLayers();
      marker_start = L.marker(startPoint,{icon: greenIcon})
        .addTo(map)
        .bindPopup("Start point")
        .openPopup();
      marker_start.addTo(route_markers);
    });

  // Show delete button
  function showButton() {
    document.getElementById('deleteButton').style.display = 'block';
  }

  document.getElementById('deleteButton').addEventListener('click', function() {
    route_markers.clearLayers();
    if (routeLayer) {
      map.removeLayer(routeLayer);
      routeLayer = null;
    }
    startPoint = null;
    endPoint = null;
    this.style.display = 'none';
  });

  showButton();
    
    
  } else if (endPoint === null) {
    endPoint = e.latlng;
    let marker_end = L.marker(endPoint,{icon: redIcon})
      .addTo(map)
      .bindPopup("End point")
      .openPopup();
    marker_end.addTo(route_markers);
  }

  // Calculate route
  let type = getToggleValue();
  console.log(type);
  let car_weight = document.getElementById('id_weight').value;
  let route = calculateRoute(startPoint, endPoint, car_weight, type);
  map.closePopup();
}

// Functions using AJAX to send data to Django view
function calculateRoute(startPoint, endPoint, car_weight, type) {
  startPoint_route = [startPoint.lng, startPoint.lat];
  endPoint_route = [endPoint.lng, endPoint.lat];

  $('#loading-icon').show();
  const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;
  let data = {
    'start_lat': startPoint.lat,
    'start_lon': startPoint.lng,
    'end_lat': endPoint.lat,
    'end_lon': endPoint.lng,
    'car_weight': car_weight,
    'type': type
  };

  $.ajax({
    url: '/directions/',
    type: 'POST',
    headers: {'X-CSRFToken': csrftoken},
    mode: 'same-origin',
    data: JSON.stringify(data),
    success: function(response) {
      console.log(response);
      let route_all = response;
      let route = JSON.parse(route_all.route);
      let route_length = route_all.length;
      let route_time = route_all.time;

      console.log("Route length: " + route_length + " km");
      console.log("Route time: " + route_time + " min");

      let myStyle = {
        "color": "#007bff",
        "weight": 7,
        "opacity": 0.75
      };
      if (routeLayer) {
        map.removeLayer(routeLayer);
      }
      routeLayer = L.geoJSON(route, {
        style: myStyle
        })
        .bindPopup(route_length + " km ," +  route_time + " min")
        .addTo(map)
        .openPopup();
    },
    error: function(xhr, errmsg, err) {
      console.log(xhr.status + ": " + xhr.responseText); 
    }
  }); 
  $('#loading-icon').hide();
}

map.on('click', onMapClick);


let obstacleLayer
const toggleButton = document.getElementById('toggleButton');

// Info popup about car category
document.getElementById('submit_button').addEventListener('click', function() {
  var car_weight = document.getElementById('id_weight').value;
  console.log(toggleButton.checked);
  if (toggleButton.checked) {
    console.log(toggleButton.checked);
    showObstacles(car_weight);
  }
  document.getElementById('carInfoPopup').style.display = 'block';
  var infoPopup = L.divOverlay({
    className: 'info_popup',
    html: document.getElementById('carInfoPopup').innerHTML = "Car weight: " + car_weight + " t"
  }).addTo(map);
});

// View obstacles button
// document.getElementById('obstacles_button').addEventListener('click', function() {
//   var car_weight = document.getElementById('id_weight').value;
//   if (obstacleLayer) {
//     map.removeLayer(obstacleLayer);
//   }
//   showObstacles(car_weight);
// });

// Toggle button for obstacles
toggleButton.addEventListener('change', function() {
  if (this.checked) {
    console.log(toggleButton.checked);
    var car_weight = document.getElementById('id_weight').value;
    showObstacles(car_weight);
  } else {
      hideObstacles();
  }
});

function hideObstacles() {
  if (obstacleLayer) {
    map.removeLayer(obstacleLayer);
  }

}


function showObstacles(car_weight) {
  const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;
  data ={'car_weight': car_weight}

  $.ajax({
    url: '/obstacles/',
    type: 'POST',
    headers: {'X-CSRFToken': csrftoken},
    mode: 'same-origin',
    data: JSON.stringify(data),
    success: function(response) {
      console.log(response)
      if (obstacleLayer) {
        map.removeLayer(obstacleLayer);
      }
      obstacleLayer = L.geoJSON(response, {
        onEachFeature: function(feature, layer) {
          layer.bindPopup("Max Weight: " + feature.properties["max_weight"] + " t");
        }
      }).addTo(map);
    },
    error: function(xhr, errmsg, err) {
      console.log(xhr.status + ": " + xhr.responseText); 
    }
  }); 
}





