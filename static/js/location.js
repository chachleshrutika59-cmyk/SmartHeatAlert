function getUserLocation() {

    if (!navigator.geolocation) {
        alert("Geolocation is not supported by your browser.");
        return;
    }

    const locationElement =
        document.getElementById("location-value");

    if (locationElement) {
        locationElement.innerText = "Detecting location...";
    }

    navigator.geolocation.getCurrentPosition(
        saveLocation,
        locationError,
        {
            enableHighAccuracy: true,
            timeout: 20000,
            maximumAge: 0
        }
    );
}


function saveLocation(position) {

    const latitude = position.coords.latitude;
    const longitude = position.coords.longitude;

    const accuracy = position.coords.accuracy;

    console.log("Latitude:", latitude);
    console.log("Longitude:", longitude);
    console.log("Accuracy:", accuracy, "meters");

    fetch("/api/location", {

        method: "POST",

        headers: {
            "Content-Type": "application/json"
        },

        body: JSON.stringify({
            latitude: latitude,
            longitude: longitude
        })

    })

    .then(response => response.json())

    .then(data => {

        console.log("Location response:", data);

        if (data.success) {

            const locationElement =
                document.getElementById("location-value");

            if (locationElement) {

                if (data.location_name) {

                    locationElement.innerText =
                        data.location_name;

                } else {

                    locationElement.innerText =
                        `${latitude.toFixed(5)}, ${longitude.toFixed(5)}`;
                }
            }

            alert(
                "Location detected successfully!\n\n" +
                "Accuracy: " +
                Math.round(accuracy) +
                " meters"
            );

        } else {

            alert(data.message);
        }

    })

    .catch(error => {

        console.error("Location save error:", error);

        alert("Unable to save location.");
    });
}


function locationError(error) {

    console.error("Geolocation error:", error);

    if (error.code === error.PERMISSION_DENIED) {

        alert(
            "Location permission was denied.\n\n" +
            "Please allow location access in your browser."
        );

    } else if (error.code === error.POSITION_UNAVAILABLE) {

        alert(
            "Your exact location is currently unavailable.\n\n" +
            "Please make sure Windows Location Services are enabled."
        );

    } else if (error.code === error.TIMEOUT) {

        alert(
            "Location detection timed out.\n\n" +
            "Please try again."
        );

    } else {

        alert("Unable to detect your location.");
    }
}


function searchLocation() {

    const input =
        document.getElementById("location-search-input");

    const message =
        document.getElementById("location-search-message");

    const locationName = input.value.trim();

    if (!locationName) {

        message.innerText =
            "Please enter a location.";

        return;
    }

    message.innerText =
        "Searching location...";

    fetch("/api/search-location", {

        method: "POST",

        headers: {
            "Content-Type": "application/json"
        },

        body: JSON.stringify({
            location: locationName
        })

    })

    .then(response => response.json())

    .then(data => {

        if (data.success) {

            message.innerText =
                "Location updated successfully.";

            setTimeout(() => {
                window.location.reload();
            }, 700);

        } else {

            message.innerText =
                data.message;
        }

    })

    .catch(error => {

        console.error(error);

        message.innerText =
            "Unable to search location.";
    });
}