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

var restVisibility = false;
var permRestMarkers = [];

$(document).ready(function () {
    var currentDrivers, currentOrders;

    $('#check-show-rests').change(function() {
        restVisibility = this.checked;
        resetPRMVisibility();
    });

    $('#load-submit').click(function() {
        wipeMarkers();
        wipePermRestMarkers();
        $(".data-row").remove();

        $.ajax({
            type: "POST",
            url: "/load",
            contentType: 'application/json;charset=UTF-8',
            dataType: "json"
        }).done(function(val) {
            var i, currLoc, title, pos;
            var rests = [];

            for (i = 0; i < val.orders[0].length; i++) {
                currLoc = val.orders[0][i].company.location;
                pos = {lat: currLoc[0], lng: currLoc[1]};
                title = 'Company ' + (i + 1);
                rests = rests.concat(val.orders[0][i].restaurants);
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

            addRestMarkers(rests);
        });
    });

    $('#gen-form-submit').click(function () {
        o_num = $("#o-num").val();
        d_num = $("#d-num").val();
        if (o_num && d_num && !isNaN(o_num) && !isNaN(d_num) && o_num > 0 && d_num > 0) {
            wipeMarkers();
            wipePermRestMarkers();
            $(".data-row").remove();
            $.ajax({
                type: "POST",
                url: "/generate",
                contentType: 'application/json;charset=UTF-8',
                dataType: "json",
                data: JSON.stringify({'orders': o_num, 'drivers': d_num})
            }).done(function(val) {
                var i, currLoc, title, pos;
                var rests = [];

                for (i = 0; i < val.orders[0].length; i++) {
                    currLoc = val.orders[0][i].company.location;
                    pos = {lat: currLoc[0], lng: currLoc[1]};
                    title = 'Company ' + (i + 1);
                    rests = rests.concat(val.orders[0][i].restaurants);
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

                addRestMarkers(rests);
           });
        }
        else {
            alert('Invalid values');
        }
    });


    $('#solve-form-submit').click(function () {
        var selValue = $('input[name=algorithm]:checked').val();
        $(".data-row").remove();
        $('#distance-field').text('...');
        $('#percent-field').text('...');
        wipeMarkers();
        $.ajax({
            type: "POST",
            url: "/solve",
            contentType: 'application/json;charset=UTF-8',
            dataType: "json",
            data: JSON.stringify(selValue)
        }).done(function(data) {
            match_data = data.matches;
            percent_matched = data.percent_matched;
            total_distance = data.total_distance;
            $('#distance-field').text((total_distance / 1000.0) + ' km');
            $('#percent-field').text(percent_matched.toFixed(2) + ' %');
            for (var i = 1; i < match_data.length; i ++) {
                var html = "";
                if (match_data[i] == null) {
                    html = '<tr class= "data-row"><td>' + i + '</td><td>No match</td><td>n/a</td></tr>';
                }
                else {
                    html ='<tr class= "data-row" id ="driver-' + i + '"><td>' + i + '</td>' +
                    '<td>' + match_data[i][0] + '</td>' +
                    '<td>' + match_data[i][1] + ' km</td></tr>';
                }
                $("#match-table").append(html);
            }

            var ordersCompleted = currentOrders.slice();

            // DRAW LINES
            if (selValue == 'single') {
                for (var j = 1; j < match_data.length; j++) {
                    var currentDriver = currentDrivers[j - 1];
                    if (match_data[j] == null) {
                        addPostRunUnmatchedDriverMarker('Driver' + j, {lat: currentDriver.location[0], lng: currentDriver.location[1]});
                    }
                    else {
                        var currentRestPath = match_data[j][2].order;
                        var companyIndex = parseInt(match_data[j][0].substring(1)) - 1;
                        ordersCompleted[companyIndex] = null;
                        var currentCompany = currentOrders[companyIndex].company;
                        var restData = currentOrders[companyIndex].restaurants;
                        var order = [{lat: currentDriver.location[0], lng: currentDriver.location[1]}];
                        for (var m = 0; m < currentRestPath.length; m++) {
                            order.push(currentRestPath[m].pos);
                        }
                        order.push({lat: currentCompany.location[0], lng: currentCompany.location[1]});

                        var hoverIn = pathHover.bind({'order' : order, 'rests' : restData});

                        addPostRunMatchedDriverMarker('Driver ' + j,
                            {lat: currentDriver.location[0], lng: currentDriver.location[1]}, hoverIn);
                        addPostRunMatchedCompanyMarker('Company ' + (companyIndex + 1),
                            {lat: currentCompany.location[0], lng: currentCompany.location[1]}, hoverIn);
                        $('#driver-' + j).mouseover(hoverIn);
                        $('#driver-' + j).mouseout(pathHoverOut);
                    }
                }

            }
            else {
                for (var j = 1; j < match_data.length; j++) {
                    var currentDriver = currentDrivers[j - 1];
                    if (match_data[j] == null) {
                        addPostRunUnmatchedDriverMarker('Driver' + j, {lat: currentDriver.location[0], lng: currentDriver.location[1]});
                    }
                    else {
                        var currentRestPath = match_data[j][2].order;
                        var companyIndices = match_data[j][0].substring(1).split(',');
                        if (companyIndices.length == 1) {
                            var companyIndex = parseInt(companyIndices[0]) - 1;
                            ordersCompleted[companyIndex] = null;
                            console.log(companyIndex);
                            var currentCompany = currentOrders[companyIndex].company;
                            var restData = currentOrders[companyIndex].restaurants;
                            var order = [{lat: currentDriver.location[0], lng: currentDriver.location[1]}];
                            for (var m = 0; m < currentRestPath.length; m++) {
                                order.push(currentRestPath[m].pos);
                            }

                            var hoverIn = pathHover.bind({'order' : order, 'rests' : restData});

                            addPostRunMatchedDriverMarker('Driver ' + j,
                                {lat: currentDriver.location[0], lng: currentDriver.location[1]}, hoverIn);
                            addPostRunMatchedCompanyMarker('Company ' + (companyIndex + 1),
                                {lat: currentCompany.location[0], lng: currentCompany.location[1]}, hoverIn);
                            $('#driver-' + j).mouseover(hoverIn);
                            $('#driver-' + j).mouseout(pathHoverOut);
                        }
                        else {
                            var comp1Index = parseInt(companyIndices[0]) - 1;
                            var comp2Index = parseInt(companyIndices[1]) - 1;
                            ordersCompleted[comp1Index] = null;
                            ordersCompleted[comp2Index] = null;
                            var currentCompany1 = currentOrders[comp1Index].company;
                            var currentCompany2 = currentOrders[comp2Index].company;
                            var restData = currentOrders[comp1Index].restaurants.concat(currentOrders[comp2Index].restaurants);
                            var order = [{lat: currentDriver.location[0], lng: currentDriver.location[1]}];
                            for (var m = 0; m < currentRestPath.length; m++) {
                                order.push(currentRestPath[m].pos);
                            }
                            var hoverIn = pathHover.bind({'order' : order, 'rests' : restData});

                            addPostRunMatchedDriverMarker('Driver ' + j,
                                {lat: currentDriver.location[0], lng: currentDriver.location[1]}, hoverIn);
                            addPostRunMatchedCompanyMarker('Company ' + (comp1Index + 1),
                                {lat: currentCompany1.location[0], lng: currentCompany1.location[1]}, hoverIn);
                            addPostRunMatchedCompanyMarker('Company ' + (comp2Index + 1),
                                {lat: currentCompany2.location[0], lng: currentCompany2.location[1]}, hoverIn);
                            $('#driver-' + j).mouseover(hoverIn);
                            $('#driver-' + j).mouseout(pathHoverOut);
                        }
                    }
                }
            }

            // TODO: check for unmatched companies
            for (var p = 0; p < ordersCompleted.length; p++) {
                if (ordersCompleted[p] != null) {
                    console.log(ordersCompleted[p]);
                    var marker = new google.maps.Marker({
                         position: {
                             lat: ordersCompleted[p].company.location[0],
                             lng: ordersCompleted[p].company.location[1]
                         },
                         map: currentMap,
                         title: 'Company ' + (p + 1),
                         icon: {
                             url: 'static/styling/img/building_grey.png',
                             scaledSize : new google.maps.Size(25, 25),
                             origin: new google.maps.Point(0, 0),
                             anchor: new google.maps.Point(12.5, 12.5)
                         }
                    });
                    markers.push(marker);
                }
            }

       });
    });
 });

function addRestMarkers(rests) {
    for (var i = 0; i < rests.length; i++) {
        var restMarker = new google.maps.Marker({
            position: {
                lat: rests[i].location[0],
                lng: rests[i].location[1]
            },
            map: currentMap,
            title: rests[i].name,
            icon: {
                url: 'static/styling/img/utensils.png',
                scaledSize : new google.maps.Size(25, 25),
                origin: new google.maps.Point(0, 0),
                anchor: new google.maps.Point(12.5, 12.5)
            }
        });
        restMarker.setVisible(restVisibility);
        permRestMarkers.push(restMarker);
    }
}


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

function addPostRunUnmatchedDriverMarker(name, pos) {
    var marker = new google.maps.Marker({
         position: pos,
         map: currentMap,
         title: name,
         icon: {
             url: 'static/styling/img/car_grey.png',
             scaledSize : new google.maps.Size(25, 25),
             origin: new google.maps.Point(0, 0),
             anchor: new google.maps.Point(12.5, 12.5)
         }

    });

    markers.push(marker);
}

function addPostRunUnmatchedCompanyMarker(name, pos) {
    var marker = new google.maps.Marker({
         position: pos,
         map: currentMap,
         title: name,
         icon: {
             url: 'static/styling/img/building_grey.png',
             scaledSize : new google.maps.Size(25, 25),
             origin: new google.maps.Point(0, 0),
             anchor: new google.maps.Point(12.5, 12.5)
         }
    });

    markers.push(marker);
}

function addPostRunMatchedDriverMarker(name, pos, hoverIn) {
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
    google.maps.event.addListener(marker, 'mouseover', hoverIn);
    google.maps.event.addListener(marker, 'mouseout', pathHoverOut);
    markers.push(marker);
}

function addPostRunMatchedCompanyMarker(name, pos, hoverIn) {
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

    google.maps.event.addListener(marker, 'mouseover', hoverIn);
    google.maps.event.addListener(marker, 'mouseout', pathHoverOut);
    markers.push(marker);
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

function resetPRMVisibility() {
    for (var i = 0; i < permRestMarkers.length; i++) {
          permRestMarkers[i].setVisible(restVisibility);
    }
}

function wipePermRestMarkers() {
    for (var i = 0; i < permRestMarkers.length; i++) {
          permRestMarkers[i].setMap(null);
    }
    permRestMarkers = [];
}
