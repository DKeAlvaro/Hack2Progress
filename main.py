import geopandas as gpd
import folium
from pyproj import Transformer
import requests
import urllib3
import pandas as pd
import random
from collections import defaultdict

urllib3.disable_warnings()

# UI Constants
UI_COLORS = {
    'active': '#28a745',      # Bootstrap green
    'inactive': '#dc3545',    # Bootstrap red
    'stop': '#007bff',        # Bootstrap blue
    'stop_hover': '#17a2b8',  # Bootstrap info
    'background': '#f8f9fa',  # Bootstrap light
    'border': '#dee2e6'       # Bootstrap border
}

# Read GeoJSON data
data = gpd.read_file("espiras.geojson")

# Read bus lines CSV
bus_lines = pd.read_csv("lineas_bus_secuencia.csv")

# Get active espiras from API
try:
    response = requests.get('https://api.sumlabencuestas.es/numeros_espiras_hk', verify=False)
    active_espiras = response.json()['espiras']
except:
    print("Could not fetch active espiras")
    active_espiras = []

# Convert from EPSG:25830 to EPSG:4326 (lat/lon)
transformer = Transformer.from_crs("EPSG:25830", "EPSG:4326", always_xy=True)

# Create a Folium map centered on the mean point of all markers
center_x = data.geometry.x.mean()
center_y = data.geometry.y.mean()
center_lon, center_lat = transformer.transform(center_x, center_y)

m = folium.Map(location=[center_lat, center_lon], 
               zoom_start=14,
               tiles='CartoDB positron',
               control_scale=True)

# Create feature groups with consistent naming
active_group = folium.FeatureGroup(name='Active Espiras')
inactive_group = folium.FeatureGroup(name='Inactive Espiras')
stops_group = folium.FeatureGroup(name='Bus Stops')

# Add espiras markers with consistent styling
for idx, row in data.iterrows():
    lon, lat = transformer.transform(row.geometry.x, row.geometry.y)
    espira_num = int(row['RefName'].strip('()'))
    is_active = espira_num in active_espiras
    
    popup_html = f"""
    <div style='min-width: 180px; padding: 5px;'>
        <h6 style='margin: 0 0 5px 0; padding-bottom: 5px; border-bottom: 1px solid {UI_COLORS["border"]};'>
            Espira {row['RefName']}
        </h6>
        <span style='color: {UI_COLORS["active"] if is_active else UI_COLORS["inactive"]}; font-weight: bold;'>
            {'● Active' if is_active else '● Inactive'}
        </span>
    </div>
    """
    
    marker = folium.CircleMarker(
        location=[lat, lon],
        radius=6,
        color=UI_COLORS['active'] if is_active else UI_COLORS['inactive'],
        fill=True,
        fillOpacity=0.7,
        weight=2,
        popup=folium.Popup(popup_html, max_width=300),
        tooltip=f"Espira {row['RefName']}"
    )
    
    if is_active:
        marker.add_to(active_group)
    else:
        marker.add_to(inactive_group)

# Generate a consistent color palette for bus lines
unique_lines = sorted(bus_lines['ayto:Linea'].unique())
color_map = {}
hue_step = 360 / len(unique_lines)
for i, line in enumerate(unique_lines):
    hue = i * hue_step
    color_map[line] = f'hsl({hue}, 70%, 50%)'

# Create a dictionary to store stops information
stops_info = defaultdict(lambda: {'lines': set(), 'name': set(), 'routes': set()})

# First pass: collect all information for each unique location
for _, row in bus_lines.iterrows():
    pos_key = (float(row['ayto:PosX']), float(row['ayto:PosY']))
    stops_info[pos_key]['lines'].add(str(row['ayto:Linea']))
    stops_info[pos_key]['name'].add(row['ayto:NombreParada'])
    stops_info[pos_key]['routes'].add(f"{row['ayto:Linea']} - {row['ayto:NombreSublinea']}")

# Add merged stops with consistent styling
for (pos_x, pos_y), info in stops_info.items():
    lon, lat = transformer.transform(pos_x, pos_y)
    
    lines_list = sorted(info['lines'], key=lambda x: int(x))
    routes_list = sorted(info['routes'])
    stop_names = sorted(info['name'])
    
    popup_html = f"""
    <div style='min-width: 250px; padding: 5px;'>
        <h6 style='margin: 0 0 5px 0; padding-bottom: 5px; border-bottom: 1px solid {UI_COLORS["border"]};'>
            {' / '.join(stop_names)}
        </h6>
        <p style='margin: 0 0 5px 0;'><b>Lines:</b> {', '.join(lines_list)}</p>
        <div style='max-height: 150px; overflow-y: auto;'>
            <p style='margin: 0 0 5px 0;'><b>Routes:</b></p>
            {'<br>'.join(f"<span style='color: {color_map[int(route.split('-')[0].strip())]};'>●</span> {route}" for route in routes_list)}
        </div>
    </div>
    """
    
    # Create the stop marker with fixed pixel size
    icon = folium.DivIcon(
        html=f'''
            <div style="
                width: 8px;
                height: 8px;
                background-color: {UI_COLORS['stop']};
                border-radius: 50%;
                opacity: 0.5;
                border: 1px solid white;
                transition: all 0.2s;
            " class="stop-{pos_x}-{pos_y}"></div>
        ''',
        icon_size=(8, 8),
        icon_anchor=(4, 4),
        class_name="stop-div-icon"
    )
    
    marker = folium.Marker(
        location=[lat, lon],
        icon=icon,
        popup=folium.Popup(popup_html, max_width=300),
        tooltip=f"Lines: {', '.join(lines_list)}"
    ).add_to(stops_group)
    
    # Add hover effect with JavaScript
    hover_js = f"""
        var marker = document.getElementsByClassName('stop-{pos_x}-{pos_y}')[0];
        marker.addEventListener('mouseover', function() {{
            this.style.backgroundColor = '{UI_COLORS["stop_hover"]}';
            this.style.opacity = '1';
        }});
        marker.addEventListener('mouseout', function() {{
            this.style.backgroundColor = '{UI_COLORS["stop"]}';
            this.style.opacity = '0.5';
        }});
    """
    folium.Element(f"<script>{hover_js}</script>").add_to(m)

# Group bus lines by line number and route
grouped_lines = bus_lines.groupby(['ayto:Linea', 'ayto:Ruta'])

# Add bus lines with consistent styling
for (line_num, route_num), group in grouped_lines:
    line_info = group.iloc[0]
    group_name = f"Line {line_num} - {line_info['ayto:NombreSublinea']}"
    
    line_group = folium.FeatureGroup(name=group_name)
    group = group.sort_values('ayto:PuntoKM')
    coordinates = []
    
    for _, row in group.iterrows():
        lon, lat = transformer.transform(float(row['ayto:PosX']), float(row['ayto:PosY']))
        coordinates.append([lat, lon])
    
    popup_html = f"""
    <div style='min-width: 200px; padding: 5px;'>
        <h6 style='margin: 0 0 5px 0; padding-bottom: 5px; border-bottom: 1px solid {UI_COLORS["border"]};'>
            <span style='color: {color_map[line_num]};'>●</span> Line {line_num}
        </h6>
        <p style='margin: 0;'><b>Label:</b> {line_info['dc:EtiquetaLinea']}</p>
        <p style='margin: 0;'><b>Route:</b> {line_info['ayto:NombreSublinea']}</p>
        <p style='margin: 0;'><b>Direction:</b> {line_info['ayto:SentidoRuta']}</p>
    </div>
    """
    
    folium.PolyLine(
        locations=coordinates,
        weight=4,
        color=color_map[line_num],
        opacity=0.7,
        popup=folium.Popup(popup_html, max_width=300),
        tooltip=f"Line {line_num}"
    ).add_to(line_group)
    
    line_group.add_to(m)

# Add groups in logical order
stops_group.add_to(m)
active_group.add_to(m)
inactive_group.add_to(m)

folium.LayerControl(collapsed=False).add_to(m)

css = '''
<style>
.leaflet-control-layers {
    background: white;
    padding: 15px;
    border-radius: 8px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    max-height: 70vh;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
}
.leaflet-control-layers-list {
    max-height: calc(70vh - 30px);
    overflow-y: auto;
}
.leaflet-control-layers label {
    margin-bottom: 8px;
    padding: 5px;
    border-radius: 4px;
    transition: background-color 0.2s;
}
.leaflet-control-layers label:hover {
    background-color: #f8f9fa;
}
.leaflet-popup-content-wrapper {
    border-radius: 8px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
}
.leaflet-popup-content {
    margin: 10px;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
}
.leaflet-tooltip {
    background: white;
    border: none;
    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    padding: 8px 12px;
    border-radius: 4px;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
}
.stop-div-icon {
    background: none;
    border: none;
}
</style>
'''
m.get_root().html.add_child(folium.Element(css))

m.save('espiras_map.html')

import webbrowser
webbrowser.open('espiras_map.html')
