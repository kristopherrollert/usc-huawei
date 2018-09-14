/*
    top left:     36.320904, -115.364003
    top right:    36.320904, -114.890439
    bottom left:  35.931493, -115.364003
    bottom right: 35.931493, -114.890439

    height: 0.473564
    width: 0.389411

    canvas height: 473 * 1.3 = 614.9
    canvas width: 389 * 1.3 = 505.7


 */



var currentMap;
var markers = [];
var tempRestMarkers = [];
var tempPath = null;

$(document).ready(function () {
    var currentDrivers, currentOrders;

    $('#gen-form-submit').click(function () {
        o_num = $("#o-num").val();
        d_num = $("#d-num").val();
        if (o_num && d_num && !isNaN(o_num) && !isNaN(d_num) && o_num > 0 && d_num > 0) {
            wipeMarkers();
            $(".data-row").remove();
            $.ajax({
                type: "POST",
                url: "/generate",
                contentType: 'application/json;charset=UTF-8',
                dataType: "json",
                data: JSON.stringify({'orders': o_num, 'drivers': d_num})
            }).done(function(val) {
                var i, currLoc, title, pos;
                for (i = 0; i < val.orders[0].length; i++) {
                    currLoc = val.orders[0][i].company.location;
                    pos = {lat: currLoc[0], lng: currLoc[1]};
                    title = 'Company ' + (i + 1);
                    addPreRunCompanyMarker(title, pos, val.orders[0][i].restaurants);
                }

                currentDrivers = val.drivers[0];
                currentOrders = val.orders[0];

                for (i = 0; i < val.drivers[0].length; i++) {
                    currLoc = val.drivers[0][i].location;
                    pos = {lat: currLoc[0], lng: currLoc[1]};
                    title = 'Driver ' + (i + 1);
                    addPreRunDriverMarker(title, pos);
                }
           });
        }
        else {
            alert('Invalid values');
        }
    });


    $('#solve-form-submit').click(function () {
         // TODO FINISH SOLVE
    });
 });

function pathHover() {
    var rests = this.rests;
    var order = this.order;
    for (var m = 0; m < rests.length; m++) {
        var restMarker = new google.maps.Marker({
            position: {
                lat: rests[m].location[0],
                lng: rests[m].location[1]
            },
            map: currentMap,
            title: rests[m].name,
            icon: {
                url: 'static/styling/img/utensils.png',
                scaledSize : new google.maps.Size(25, 25),
                origin: new google.maps.Point(0, 0),
                anchor: new google.maps.Point(12.5, 12.5)
            }
        });
        tempRestMarkers.push(restMarker);
    }

    tempPath = new google.maps.Polyline({
          path: order,
          geodesic: true,
          strokeColor: '#FF0000',
          strokeOpacity: 1.0,
          strokeWeight: 2,
          map: currentMap
        });
}

function pathHoverOut() {
    tempPath.setMap(null);
    tempPath = null;
    wipeTempRestMarkers();
}

function initMap() {
     var cent = {lat: 36.143721, lng: -115.177044};
     currentMap = new google.maps.Map(document.getElementById('map'), {zoom: 10,
         center: cent,
         disableDefaultUI: true,
         styles: mapStyling = [
            {
                "featureType": "administrative",
                "elementType": "all",
                "stylers": [
                    {
                        "saturation": "-100"
                    }
                ]
            },
            {
                "featureType": "administrative.province",
                "elementType": "all",
                "stylers": [
                    {
                        "visibility": "off"
                    }
                ]
            },
            {
                "featureType": "landscape",
                "elementType": "all",
                "stylers": [
                    {
                        "saturation": -100
                    },
                    {
                        "lightness": 65
                    },
                    {
                        "visibility": "on"
                    }
                ]
            },
            {
                "featureType": "poi",
                "elementType": "all",
                "stylers": [
                    {
                        "saturation": -100
                    },
                    {
                        "lightness": "50"
                    },
                    {
                        "visibility": "simplified"
                    }
                ]
            },
            {
                "featureType": "road",
                "elementType": "all",
                "stylers": [
                    {
                        "saturation": "-100"
                    }
                ]
            },
            {
                "featureType": "road.highway",
                "elementType": "all",
                "stylers": [
                    {
                        "visibility": "simplified"
                    }
                ]
            },
            {
                "featureType": "road.arterial",
                "elementType": "all",
                "stylers": [
                    {
                        "lightness": "30"
                    }
                ]
            },
            {
                "featureType": "road.local",
                "elementType": "all",
                "stylers": [
                    {
                        "lightness": "40"
                    }
                ]
            },
            {
                "featureType": "transit",
                "elementType": "all",
                "stylers": [
                    {
                        "saturation": -100
                    },
                    {
                        "visibility": "simplified"
                    }
                ]
            },
            {
                "featureType": "water",
                "elementType": "geometry",
                "stylers": [
                    {
                        "hue": "#ffff00"
                    },
                    {
                        "lightness": -25
                    },
                    {
                        "saturation": -97
                    }
                ]
            },
            {
                "featureType": "water",
                "elementType": "labels",
                "stylers": [
                    {
                        "lightness": -25
                    },
                    {
                        "saturation": -100
                    }
                ]
            },
            {
              featureType: 'poi.business',
              stylers: [{visibility: 'off'}]
            },
            {
              featureType: 'transit',
              elementType: 'labels.icon',
              stylers: [{visibility: 'off'}]
            }
        ]
    });
}

function addPreRunDriverMarker(name, pos) {
    var marker = new google.maps.Marker({
         position: pos,
         map: currentMap,
         title: name,
         icon: {
             url: 'static/styling/img/car.png',
             scaledSize : new google.maps.Size(25, 25),
             origin: new google.maps.Point(0, 0),
             anchor: new google.maps.Point(12.5, 12.5)
         }

     });

     markers.push(marker);
}

function addPreRunCompanyMarker(name, pos, rests) {
    var marker = new google.maps.Marker({
         position: pos,
         map: currentMap,
         title: name,
         icon: {
             url: 'static/styling/img/building.png',
             scaledSize : new google.maps.Size(25, 25),
             origin: new google.maps.Point(0, 0),
             anchor: new google.maps.Point(12.5, 12.5)
         }
    });

    google.maps.event.addListener(marker, 'click', function() {
        if (currentRestOpen == marker) {
            currentRestOpen = null;
            // delete all markers
            wipeTempRestMarkers();
        }
        else {
            if (currentRestOpen != null) {
                // close other markers
                wipeTempRestMarkers();
            }

            currentRestOpen = marker;
            // open markers
            for (var j = 0; j < rests.length; j++) {
                var restMarker = new google.maps.Marker({
                     position: {
                         lat: rests[j].location[0],
                         lng: rests[j].location[1]
                     },
                     map: currentMap,
                     title: rests[j].name,
                     icon: {
                         url: 'static/styling/img/utensils.png',
                         scaledSize : new google.maps.Size(25, 25),
                         origin: new google.maps.Point(0, 0),
                         anchor: new google.maps.Point(12.5, 12.5)
                     }
                });
                tempRestMarkers.push(restMarker);
            }

        }
    });

     markers.push(marker);
}

function wipeMarkers() {
    for (var i = 0; i < markers.length; i++) {
          markers[i].setMap(null);
    }
    markers = [];
}

function wipeTempRestMarkers() {
    for (var i = 0; i < tempRestMarkers.length; i++) {
          tempRestMarkers[i].setMap(null);
    }
    tempRestMarkers = [];
}
