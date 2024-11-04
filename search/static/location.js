// Automatically request location when the page loads
window.onload = function() {
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(sendPosition, handleError);
    } else {
        alert("Geolocation is not supported by this browser.");
    } 
};

function sendPosition(position) {
    const latitude = position.coords.latitude;
    const longitude = position.coords.longitude;

    // Send the location data to the server
    fetch('', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': '{{ csrf_token }}'  // Include CSRF token for Django
        },
        body: JSON.stringify({
            latitude: latitude,
            longitude: longitude
        })
    })
    .then(response => response.json())
    .then(data => {
        console.log("Server response:", data);
        document.body.innerHTML = "<h1>Location Saved!</h1>";
    })
    .catch(error => console.error("Error:", error));
}

function handleError(error) {
    switch(error.code) {
        case error.PERMISSION_DENIED:
            // alert("User denied the request for Geolocation.");
            break;
        case error.POSITION_UNAVAILABLE:
            //alert("Location information is unavailable.");
            break;
        case error.TIMEOUT:
            //alert("The request to get user location timed out.");
            break;
        case error.UNKNOWN_ERROR:
            //alert("An unknown error occurred.");
            break;
    }
}
