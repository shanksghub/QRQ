from flask import Flask, render_template_string, request, jsonify
import folium
import random
import datetime
from geopy.distance import geodesic
from geopy import Point
from apscheduler.schedulers.background import BackgroundScheduler

app = Flask(__name__)

# Coordinates for Sector 19, Gurgaon
sector_19_coords = (28.4595, 77.0266)

# List of disaster types
disaster_types = ["Earthquake", "Fire", "Shooting", "Robbery"]

# Store all disasters (latest at index 0)
disaster_data = []

# Function to generate a random disaster
def generate_disaster():
    """Generate a new disaster and store it."""
    disaster_type = random.choice(disaster_types)
    random_location = generate_random_location(sector_19_coords, 30)
    disaster_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Generate disaster-specific details
    if disaster_type == "Earthquake":
        details = f"Magnitude: {random.uniform(5.0, 8.0):.1f} Richter"
    elif disaster_type == "Shooting":
        details = f"Fatalities: {random.randint(1, 10)} people"
    elif disaster_type == "Robbery":
        details = f"Stolen Amount: ₹{random.randint(50000, 500000)}"
    else:
        details = "Details not available."

    disaster_details = {
        "type": disaster_type,
        "location": random_location,
        "details": details,
        "timestamp": disaster_time
    }

    # Store the new disaster at index 0
    disaster_data.insert(0, disaster_details)

    print(f"New disaster: {disaster_type} at {random_location} on {disaster_time}")

# Function to generate a random location within a 30km radius
def generate_random_location(center_coords, radius_km):
    center = Point(center_coords[0], center_coords[1])
    bearing = random.uniform(0, 360)
    distance = random.uniform(0, radius_km)
    new_point = geodesic(kilometers=distance).destination(center, bearing)
    return new_point.latitude, new_point.longitude

# Flask route to get geolocation and redirect to map
@app.route('/')
def index():
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Geolocation</title>
        <script>
            window.onload = function() {
                if (navigator.geolocation) {
                    navigator.geolocation.getCurrentPosition(sendPositionToPython);
                } else {
                    alert("Geolocation is not supported.");
                }
            };

            function sendPositionToPython(position) {
                const latitude = position.coords.latitude;
                const longitude = position.coords.longitude;

                fetch("/geolocation", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({latitude: latitude, longitude: longitude})
                })
                .then(response => response.json())
                .then(data => {
                    window.location.href = `/map/${data.latitude}/${data.longitude}`;
                })
                .catch(error => console.error("Error:", error));
            }
        </script>
    </head>
    <body>
        <h2>Getting Your Location...</h2>
    </body>
    </html>
    """
    return render_template_string(html_content)

# Flask route to receive geolocation data
@app.route('/geolocation', methods=['POST'])
def geolocation():
    data = request.get_json()
    latitude = data.get('latitude')
    longitude = data.get('longitude')
    return jsonify({"status": "success", "latitude": latitude, "longitude": longitude})

# Flask route to display the map
@app.route('/map/<float:lat>/<float:lon>')
def map_page(lat, lon):
    """Map with markers for current location and disasters."""
    m = folium.Map(location=(lat, lon), zoom_start=12)

    # Current location marker (green)
    folium.Marker(
        location=(lat, lon),
        popup="You are here",
        icon=folium.Icon(color='green')
    ).add_to(m)

    # Add markers for disasters
    for index, disaster in enumerate(disaster_data):
        color = "red" if index == 0 else "blue"  # Latest is red, others are blue
        folium.Marker(
            location=disaster["location"],
            popup=f"<b>Disaster:</b> {disaster['type']}<br><b>Details:</b> {disaster['details']}<br><b>Time:</b> {disaster['timestamp']}",
            icon=folium.Icon(color=color)
        ).add_to(m)

    # Auto-reload the page every 2 minutes
    html_code = f"""
    <html>
    <head>
        <meta http-equiv="refresh" content="120">
    </head>
    <body>
        {m.get_root().render()}
    </body>
    </html>
    """
    return html_code

# Scheduler to generate disasters every 2 minutes
scheduler = BackgroundScheduler()
scheduler.add_job(generate_disaster, 'interval', minutes=1)
scheduler.start()

if __name__ == "__main__":
    app.run(debug=True)
