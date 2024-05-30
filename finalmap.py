import folium
import geojson
import mysql.connector
import json
import branca
from branca.colormap import LinearColormap
import sys

# Load the GeoJSON file for Tennessee
with open("tennessee.geojson", "r") as geojson_file:
    tennessee_boundary = json.load(geojson_file)

# Load the GeoJSON file containing state boundaries and names
with open('unitedstates.geojson', 'r') as geojson_file:
    unitedstates = json.load(geojson_file)
    
# Create a Folium map centered on Tennessee
tennessee_map = folium.Map(location=[35.8, -86.4], zoom_start=7, tiles = "cartodbpositron")

###############################################################################################################################
def usage():
    print("Usage: python %s <user> <password> <database name>" % (sys.argv[0]))
    print("\t<user>: Can be root or another user set up in your SQL database")
    print("\t<password>: Account password used to get into MySQL")
    print("\t<database name>: Name of the database being accessed")
    print("\tIe: python %s root myPassword1 CEM_EVENTS" % (sys.argv[0]))
    print("\tNote: This script assumes you will be using localhost")

# Connect to the database using values passed from the command line. If the connection fails, print the error and exit
def connect_to_database(user, password, database):
    try:
        mydb = mysql.connector.connect(
            host='localhost',
            user=user,
            password=password,
            database=database
        )
    except Exception as e:
        print("Error: Connection to the database has failed")
        print(f"\t{e}")
        exit(1)
    return mydb
mydb = connect_to_database(sys.argv[1], sys.argv[2], sys.argv[3])
# Setup a cursor
mycursor = mydb.cursor()

# Retrieve the county names along with the number of events associated with each county
mycursor.execute("""
  SELECT 
    o.OrgCounty, 
    COALESCE(SUM(e.Onsite + e.Offsite), 0) AS NumEvents,
    COALESCE(SUM(CASE WHEN e.Onsite > 0 THEN 1 ELSE 0 END), 0) AS NumOnsiteEvents,
    COALESCE(SUM(CASE WHEN e.Offsite > 0 THEN 1 ELSE 0 END), 0) AS NumOffsiteEvents
FROM 
    ORGANIZATIONS o
LEFT JOIN 
    CEMEVENTS e ON o.OrgName = e.OrgName
WHERE
    (e.Onsite > 0 OR e.Offsite > 0)
GROUP BY 
    o.OrgCounty;



""")
county_events_count_data = mycursor.fetchall()

# Create a dictionary from the retrieved data
numerical_data = {row[0]: float(row[1]) for row in county_events_count_data}

# Retrieve organization names and the number of events for each organization
mycursor.execute("""
   SELECT
    o.OrgName,
    o.OrgCounty,
    SUM(e.Onsite + e.Offsite) AS NumEvents
FROM
    ORGANIZATIONS o
LEFT JOIN
    CEMEVENTS e ON o.OrgName = e.OrgName
GROUP BY
    o.OrgName, o.OrgCounty;


""")
organization_events_data = mycursor.fetchall()

# Create a dictionary to store the data
organization_events = {(row[0], row[1]): {'NumEvents': row[2]} for row in organization_events_data}

# Assuming organization_events is already defined as described in your code
for key, value in organization_events.items():
    org_name, org_county = key
    num_events = value['NumEvents']
    print(f"Organization: {org_name}, County: {org_county}, NumEvents: {num_events}")


# Close the cursor and connection
mycursor.close()
mydb.close()


threshold_scale = [0, 10,30,60,100, 150,200,300,400,500, 700]  # Adjust these values based on your data

# Create the choropleth map based on numerical values with custom colors and range
folium.Choropleth(
    geo_data=tennessee_boundary,
    data=numerical_data,
    columns=["name", "value"],  # "name" should match the district names
    key_on="feature.properties.name",  # The key in GeoJSON properties to match with your district names
    fill_color='YlOrBr',
    fill_opacity=0.7,
    line_opacity=0.2,
    legend_name="Colors according to no. of Attendies",
    threshold_scale=threshold_scale,  # Specify your custom thresholds
    fill_scale=None,  # Disable fill scale to use the specified thresholds
).add_to(tennessee_map)

# Define a style function to set the outline color and weight based on zoom level
def style_function(feature):
    return {
        "color": "black",  # Set outline color to black
        "weight": 2,       # Set the outline weight
        "fillOpacity": 0,  # Set fill opacity to 0 for transparent fill
    }

###############################################################################################################################


# Add state outlines as GeoJSON layers
state_layer = folium.GeoJson(
    unitedstates,
    style_function=lambda feature: {
        'color': 'black',       # Customize the polygon border color
        'weight': 2,            # Customize the polygon border weight
        'fillColor': 'none',    # Make the states transparent
    }
)
state_layer.add_to(tennessee_map)

###############################################################################################################################

# Modify the GeoJson layer to include the organization data in the popup
geojson_layer = folium.GeoJson(
    tennessee_boundary,
    name='GeoJSON Layer',
    style_function=lambda feature: {
        'color': 'black',       # Customize the polygon border color
        'weight': 2,            # Customize the polygon border weight
        'fillOpacity': 0,       # Customize the polygon fill opacity
    },
    highlight_function=lambda x: {'weight': 3, 'color': 'blue'},  # Highlight style on hover
    popup=folium.GeoJsonPopup(fields=['name', 'Organization Names', 'NumEvents'], aliases=['County Name', 'School Districts', '']),
).add_to(tennessee_map)

# Add the organization data to the GeoJson layer
for feature in geojson_layer.data['features']:
    county_name = feature['properties']['name']
    organization_names = feature['properties'].get('school_district', [])

# Generate dynamic aliases for organization names with bold formatting
    aliases = [f'<b>{organization}</b>' for organization in organization_names]


    popup_text = "<br>".join([
    f"<b>{aliases[i]}</b>: {organization_events.get((org, county_name), {'NumEvents': 0})['NumEvents']} Participants"
    for i, org in enumerate(organization_names)
]) if organization_names else 'No Data'



    feature['properties']['Organization Names'] = popup_text
    feature['properties']['NumEvents'] = ''  # Set default value if there are no events

###############################################################################################################################
# Charter Schools
marker_data = [
    {
        'location': [35.14803766201546, -89.89985182],
        'icon_url': 'triangle.png',
        'icon_size': (10, 10),
        'popup_text': "Aurora Collegiate"
    },
    {
        'location': [35.0230729574025, -85.27854927],
        'icon_url': 'triangle.png',
        'icon_size': (10, 10),
        'popup_text': "Chattanooga School of Excellence"
    },
    {
        'location': [35.14066064220739, -89.99995290],
        'icon_url': 'triangle.png',
        'icon_size': (10, 10),
        'popup_text': "Compass"
    },
    {
        'location': [35.069040134080225, -89.88972488],
        'icon_url': 'triangle.png',
        'icon_size': (10, 10),
        'popup_text': "Cornerstone Prep"
    },
    {
        'location': [35.96833062890766, -83.93353885],
        'icon_url': 'triangle.png',
        'icon_size': (10, 10),
        'popup_text': "Emerald Academy (Knox)"
    },
    {
        'location': [35.21467258919195, -90.0122966215441],
        'icon_url': 'triangle.png',
        'icon_size': (10, 10),
        'popup_text': "Frayser Community Schools"
    },
    {
        'location': [35.026406009081164, -90.0902091167188],
        'icon_url': 'triangle.png',
        'icon_size': (10, 10),
        'popup_text': "Freedom Prep"
    },
    {
        'location': [35.07707990124379, -89.9008944249416],
        'icon_url': 'triangle.png',
        'icon_size': (10, 10),
        'popup_text': "Gestalt Community Schools"
    },
    {
        'location': [35.14723951658383, -90.0498446909726],
        'icon_url': 'triangle.png',
        'icon_size': (10, 10),
        'popup_text': "Grizzlies Prep"
    },
    {
        'location': [35.01281980766233, -90.0502098933512],
        'icon_url': 'triangle.png',
        'icon_size': (10, 10),
        'popup_text': "Green Dot"
    },
    {
        'location': [36.04974105080055, -86.6454491973964],
        'icon_url': 'triangle.png',
        'icon_size': (10, 10),
        'popup_text': "Intrepid College Prep"
    },
    {
        'location': [35.16948655249128, -90.0401489032786],
        'icon_url': 'triangle.png',
        'icon_size': (10, 10),
        'popup_text': "Kipp Memphis"
    },
    {
        'location': [36.20791608060283, -86.769292128103],
        'icon_url': 'triangle.png',
        'icon_size': (10, 10),
        'popup_text': "Kipp Nashville"
    },
    {
        'location': [36.04717758959462, -86.652722904897],
        'icon_url': 'triangle.png',
        'icon_size': (10, 10),
        'popup_text': "Knowledge Academies Nashville"
    },
    {
        'location': [36.14878301308138, -86.7643556126362],
        'icon_url': 'triangle.png',
        'icon_size': (10, 10),
        'popup_text': "Lead Public Schools"
    },
    {
        'location': [35.145720006784174, -90.0181688522993],
        'icon_url': 'triangle.png',
        'icon_size': (10, 10),
        'popup_text': "MASE"
    },
    {
        'location': [35.221512649961106, -89.9944798431302],
        'icon_url': 'triangle.png',
        'icon_size': (10, 10),
        'popup_text': "Memphis Business Executives"
    },
    {
        'location': [35.10902490221267, -89.8660786997118],
        'icon_url': 'triangle.png',
        'icon_size': (10, 10),
        'popup_text': "Memphis School of Excellence"
    },
    {
        'location': [35.05034667253472, -89.8342600932534],
        'icon_url': 'triangle.png',
        'icon_size': (10, 10),
        'popup_text': "My Journeys"
    },
    {
        'location': [36.045631846719814, -86.7012566127438],
        'icon_url': 'triangle.png',
        'icon_size': (10, 10),
        'popup_text': "Nashville Collegiate"
    },
    {
        'location': [35.054169791975525, -89.8800682939882],
        'icon_url': 'triangle.png',
        'icon_size': (10, 10),
        'popup_text': "Power Center Academy"
    },
    {
        'location': [35.17272553991484, -89.973605804897],
        'icon_url': 'triangle.png',
        'icon_size': (10, 10),
        'popup_text': "Promise Academy"
    },
    {
        'location': [36.19499372758001, -86.7943465205326],
        'icon_url': 'triangle.png',
        'icon_size': (10, 10),
        'popup_text': "Purpose Prep"
    },
    {
        'location': [36.22979615554932, -86.7624422142617],
        'icon_url': 'triangle.png',
        'icon_size': (10, 10),
        'popup_text': "Rocketship"
    },
    {
        'location': [36.24273258007936, -86.7794071665106],
        'icon_url': 'triangle.png',
        'icon_size': (10, 10),
        'popup_text': "Republic"
    },
    {
        'location': [36.13591832057791, -86.7385357413324],
        'icon_url': 'triangle.png',
        'icon_size': (10, 10),
        'popup_text': "Stem Prep Academy"
    },
]
# Create and add markers with popups using the custom circle icon
for marker in marker_data:
    location = marker['location']
    icon_url = marker['icon_url']
    icon_size = marker['icon_size']
    popup_text = marker['popup_text']
    
    # Create a custom icon for the marker
    custom_icon = folium.CustomIcon(
        icon_image=icon_url,
        icon_size=icon_size,
        icon_anchor=(icon_size[0] // 2, icon_size[1] // 2)
    )
    
 # Check if the lowercase version of popup_text matches any organization in organization_events
    for key, value in organization_events.items():
         org_name, org_county = key
         if org_name.lower() == popup_text.lower():
            # Format the information for the matching organization
            alias = f'<b>{org_name}</b>'
            event_number = value.get('NumEvents', 0)
            popup_text = f"{alias}: {event_number} Participants"
            break  # Stop iterating after finding the matching organization


    marker_obj = folium.Marker(
        location=location,
        popup=popup_text,
        icon=custom_icon
    )
    marker_obj.add_to(tennessee_map)
    # Non-Public Schools
# Define marker locations and popup texts in a list of dictionaries
marker_data = [
    {
        'location': [35.132526830498186, -89.86472533697],
        'icon_url': 'square.jpg',
        'icon_size': (10, 10),
        'popup_text': "Christian Brothers High School"
    },
    {
        'location': [35.876235547118995, -84.1702421668917],
        'icon_url': 'square.jpg',
        'icon_size': (10, 10),
        'popup_text': "Concord Christian"
    },
    {
        'location': [36.18448411218491, -86.6498402512281],
        'icon_url': 'square.jpg',
        'icon_size': (10, 10),
        'popup_text': "Donelson Christian"
    },
    {
        'location': [35.101860548909094, -89.9142665477903],
        'icon_url': 'square.jpg',
        'icon_size': (10, 10),
        'popup_text': "Harding Academy Memphis"
    },
    {
        'location': [35.81507768048518, -86.3506952991627],
        'icon_url': 'square.jpg',
        'icon_size': (10, 10),
        'popup_text': "Islamic Center of Murfreesboro"
    },
    {
        'location': [36.107294503015034, -86.7966102893927],
        'icon_url': 'square.jpg',
        'icon_size': (10, 10),
        'popup_text': "Lipscomb Academy"
    },
    {
        'location': [35.73581043889549, -84.0240345085401],
        'icon_url': 'square.jpg',
        'icon_size': (10, 10),
        'popup_text': "Maryville Christian"
    },
    {
        'location': [36.12908566009482, -86.8363376359439],
        'icon_url': 'square.jpg',
        'icon_size': (10, 10),
        'popup_text': "Montgomery Bell Academy"
    },
    {
        'location': [35.86986711746426, -86.3836068595001],
        'icon_url': 'square.jpg',
        'icon_size': (10, 10),
        'popup_text': "Middle TN Christian"
    },
    {
        'location': [36.498714546424026, -87.2425543677155],
        'icon_url': 'square.jpg',
        'icon_size': (10, 10),
        'popup_text': "Montessori"
    },
    {
        'location': [35.16355652562645, -85.3117135490752],
        'icon_url': 'square.jpg',
        'icon_size': (10, 10),
        'popup_text': "Signal Mountain Christian"
    },
    {
        'location': [35.18185543425699, -89.7905271602069],
        'icon_url': 'square.jpg',
        'icon_size': (10, 10),
        'popup_text': "St Francis of Assisi Catholic"
    },
    {
        'location': [35.0629689844613, -85.1384839910129],
        'icon_url': 'square.jpg',
        'icon_size': (10, 10),
        'popup_text': "Silverdale Baptist Academy"
    },
    {
        'location': [37.03477872929351, -95.821520204305],
        'icon_url': 'square.jpg',
        'icon_size': (10, 10),
        'popup_text': "Tyro Christian"
    },
]
# Create and add markers with popups using the custom circle icon
for marker in marker_data:
    location = marker['location']
    icon_url = marker['icon_url']
    icon_size = marker['icon_size']
    popup_text = marker['popup_text']
    
    # Create a custom icon for the marker
    custom_icon = folium.CustomIcon(
        icon_image=icon_url,
        icon_size=icon_size,
        icon_anchor=(icon_size[0] // 2, icon_size[1] // 2)
    )
    
 # Check if the lowercase version of popup_text matches any organization in organization_events
    for key, value in organization_events.items():
         org_name, org_county = key
         if org_name.lower() == popup_text.lower():
            # Format the information for the matching organization
            alias = f'<b>{org_name}</b>'
            event_number = value.get('NumEvents', 0)
            popup_text = f"{alias}: {event_number} Participants"
            break  # Stop iterating after finding the matching organization


    marker_obj = folium.Marker(
        location=location,
        popup=popup_text,
        icon=custom_icon
    )
    marker_obj.add_to(tennessee_map)

    # Other public schools
marker_data = [
    {
        'location': [35.15283920330544, -90.0143521443479],
        'icon_url': 'circle.png',
        'icon_size': (10, 10),
        'popup_text': "Achievement"
    },
    {
        'location': [36.444124041311376, -84.9377438509566],
        'icon_url': 'circle.png',
        'icon_size': (10, 10),
        'popup_text': "Alvin C York"
    },
    {
        'location': [36.168703589733234, -86.6537309205599],
        'icon_url': 'circle.png',
        'icon_size': (10, 10),
        'popup_text': "TN School for the Blind"
    },
    {
        'location': [35.95999195990508, -83.8798670620052],
        'icon_url': 'circle.png',
        'icon_size': (10, 10),
        'popup_text': "TN School for the Deaf"
    }
]
# Create and add markers with popups using the custom circle icon
for marker in marker_data:
    location = marker['location']
    icon_url = marker['icon_url']
    icon_size = marker['icon_size']
    popup_text = marker['popup_text']
    
    # Create a custom icon for the marker
    custom_icon = folium.CustomIcon(
        icon_image=icon_url,
        icon_size=icon_size,
        icon_anchor=(icon_size[0] // 2, icon_size[1] // 2)
    )
    
 # Check if the lowercase version of popup_text matches any organization in organization_events
    for key, value in organization_events.items():
         org_name, org_county = key
         if org_name.lower() == popup_text.lower():
            # Format the information for the matching organization
            alias = f'<b>{org_name}</b>'
            event_number = value.get('NumEvents', 0)
            popup_text = f"{alias}: {event_number} Participants"
            break  # Stop iterating after finding the matching organization


    marker_obj = folium.Marker(
        location=location,
        popup=popup_text,
        icon=custom_icon
    )
    marker_obj.add_to(tennessee_map)



    # Higher Ed Institutions
marker_data = [
    {
        'location': [36.53584160927396, -87.3547139201756],
        'icon_url': 'star.png',
        'icon_size': (10, 10),
        'popup_text': "APSU"
    },
    {
        'location': [40.05577206746051, -75.3738763316631],
        'icon_url': 'star.png',
        'icon_size': (10, 10),
        'popup_text': "Cabrini"
    },
    {
        'location': [36.12212812451781, -83.4905136048969],
        'icon_url': 'star.png',
        'icon_size': (10, 10),
        'popup_text': "Carson Newman University"
    },
    {
        'location': [36.205930930759685, -86.2990894665490],
        'icon_url': 'star.png',
        'icon_size': (10, 10),
        'popup_text': "Cumberland University"
    },
    {
        'location': [46.88310525410919, -102.8001384773400],
        'icon_url': 'star.png',
        'icon_size': (10, 10),
        'popup_text': "Dickinson State"
    },
    {
        'location': [36.30319042548863, -82.3697672511048],
        'icon_url': 'star.png',
        'icon_size': (10, 10),
        'popup_text': "ETSU"
    },
    {
        'location': [35.441517709314866, -88.6385462673397],
        'icon_url': 'star.png',
        'icon_size': (10, 10),
        'popup_text': "Freed Hardeman"
    },
    {
        'location': [36.58782377019689, -82.1595371121764],
        'icon_url': 'star.png',
        'icon_size': (10, 10),
        'popup_text': "King University"
    },
    {
        'location': [37.349940380879374, -79.1783265499958],
        'icon_url': 'star.png',
        'icon_size': (10, 10),
        'popup_text': "Liberty"
    },
    {
        'location': [36.10493782091739, -86.7988567067465],
        'icon_url': 'star.png',
        'icon_size': (10, 10),
        'popup_text': "Lipscomb University"
    },
    {
        'location': [43.044097554447966, -87.9208978974758],
        'icon_url': 'star.png',
        'icon_size': (10, 10),
        'popup_text': "Milwaukee Area Tech (Wisconsin)"
    },
    {
        'location': [40.86666705196981, -74.1976433767605],
        'icon_url': 'star.png',
        'icon_size': (10, 10),
        'popup_text': "Montclair (New Jersey)"
    },
    {
        'location': [35.84928338916708, -86.3667868362346],
        'icon_url': 'star.png',
        'icon_size': (10, 10),
        'popup_text': "MTSU"
    },
    {
        'location': [36.16858683073668, -86.8257975914039],
        'icon_url': 'star.png',
        'icon_size': (10, 10),
        'popup_text': "TN State Univ"
    },
    {
        'location': [36.17731795646853, -85.5094090893200],
        'icon_url': 'star.png',
        'icon_size': (10, 10),
        'popup_text': "TN Tech"
    },
    {
        'location': [36.14283936775191, -86.7531827512719],
        'icon_url': 'star.png',
        'icon_size': (10, 10),
        'popup_text': "Trevecca"
    },
    {
        'location': [32.98279446162801, -80.0706125697831],
        'icon_url': 'star.png',
        'icon_size': (10, 10),
        'popup_text': "Charleston Southern"
    },
    {
        'location': [36.14543072143137, -86.8027839279826],
        'icon_url': 'star.png',
        'icon_size': (10, 10),
        'popup_text': "U of Kentucky"
    },
    {
        'location': [32.53225122278321, -92.0688299162422],
        'icon_url': 'star.png',
        'icon_size': (10, 10),
        'popup_text': "U of Louisiana Monroe"
    },
    {
        'location': [35.11895164256866, -89.9374123337326],
        'icon_url': 'star.png',
        'icon_size': (10, 10),
        'popup_text': "U of Memphis"
    },
    {
        'location': [35.95506090589829, -83.9294564821527],
        'icon_url': 'star.png',
        'icon_size': (10, 10),
        'popup_text': "U of Tennessee Knoxville"
    },
    {
        'location': [36.145638651774476, -86.8027839279826],
        'icon_url': 'star.png',
        'icon_size': (10, 10),
        'popup_text': "Vanderbilt"
    }
]

# Create and add markers with popups using the custom circle icon
for marker in marker_data:
    location = marker['location']
    icon_url = marker['icon_url']
    icon_size = marker['icon_size']
    popup_text = marker['popup_text']
    
    # Create a custom icon for the marker
    custom_icon = folium.CustomIcon(
        icon_image=icon_url,
        icon_size=icon_size,
        icon_anchor=(icon_size[0] // 2, icon_size[1] // 2)
    )
    
    # Check if the lowercase version of popup_text matches any organization in organization_events
    for key, value in organization_events.items():
         org_name, org_county = key
         if org_name.lower() == popup_text.lower():
            # Format the information for the matching organization
            alias = f'<b>{org_name}</b>'
            event_number = value.get('NumEvents', 0)
            popup_text = f"{alias}: {event_number} Participants"
            break  # Stop iterating after finding the matching organization


    marker_obj = folium.Marker(
        location=location,
        popup=popup_text,
        icon=custom_icon
    )
    marker_obj.add_to(tennessee_map)


    legend_html = """
<div style="position: fixed; bottom: 50px; left: 50px; background-color: white; padding: 10px; border: 2px solid gray; z-index: 1000;">
    <p><strong>Legend</strong></p>
    <p><svg height="10" width="10"><path d="M5 0 L6.2 3.8 H10 L7.5 6.2 L8.8 10 L5 8.1 L1.2 10 L2.5 6.2 L0 3.8 H3.8 Z" fill="black"></circle></svg> Higher Ed</p>
    <p><svg height="10" width="10"><polygon points="0,0 10,0 5,10" fill="black"></circle></svg> Charter Schools</p>
    <p><svg height="10" width="10"><rect x="0" y="0" width="10" height="10" fill="black"></circle></svg> Non-Public Schools</p>
    <p><svg height="10" width="10"><circle cx="5" cy="5" r="5" fill="black"></circle></svg> Other Public Schools</p>
</div>
"""

# Add the legend HTML to the map
tennessee_map.get_root().html.add_child(folium.Element(legend_html))
# Save the map as an HTML file
tennessee_map.save("tennessee_boundary_map.html")

tennessee_map

