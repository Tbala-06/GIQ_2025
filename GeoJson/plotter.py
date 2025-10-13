import json
import matplotlib.pyplot as plt
import numpy as np

def plot_road_marking(feature_json_string):
    """
    Plot a single road marking feature from GeoJSON
    
    Args:
        feature_json_string: JSON string of a single feature
    """
    # Parse the JSON string
    feature = json.loads(feature_json_string)
    
    # Extract properties
    properties = feature['properties']
    geometry = feature['geometry']
    
    # Create figure
    fig, ax = plt.subplots(figsize=(12, 10))
    
    # Determine color based on marking type
    typ_cd = properties.get('TYP_CD', '')
    if 'Yellow' in properties.get('TYP_NAM', '') or typ_cd in ['G', 'I', 'N']:
        color = 'yellow'
    elif 'Red' in properties.get('TYP_NAM', ''):
        color = 'red'
    else:
        color = 'white'
    
    # Plot the geometry
    if geometry['type'] == 'LineString':
        coords = geometry['coordinates']
        lons = [coord[0] for coord in coords]
        lats = [coord[1] for coord in coords]
        ax.plot(lons, lats, color=color, linewidth=3, marker='o', markersize=4, 
                markerfacecolor='red', markeredgecolor='black')
    
    elif geometry['type'] == 'MultiLineString':
        for line in geometry['coordinates']:
            lons = [coord[0] for coord in line]
            lats = [coord[1] for coord in line]
            ax.plot(lons, lats, color=color, linewidth=3, marker='o', markersize=4,
                    markerfacecolor='red', markeredgecolor='black')
    
    # Add grid and labels
    ax.grid(True, alpha=0.3)
    ax.set_xlabel('Longitude', fontsize=12)
    ax.set_ylabel('Latitude', fontsize=12)
    
    # Create title with key information
    title = f"Road Marking: {properties.get('TYP_CD', 'Unknown')}\n"
    title += f"{properties.get('TYP_NAM', 'No description')}\n"
    title += f"ID: {properties.get('UNIQUE_ID', 'Unknown')}"
    ax.set_title(title, fontsize=10, pad=20)
    
    # Add legend
    ax.plot([], [], color=color, linewidth=3, label=f'{typ_cd} marking')
    ax.plot([], [], 'ro', markersize=6, label='Coordinates')
    ax.legend(loc='upper right')
    
    # Set aspect ratio to be equal for proper geographic display
    ax.set_aspect('equal', adjustable='box')
    
    # Adjust layout
    plt.tight_layout()
    plt.show()

def plot_from_file(geojson_file, unique_id=None, index=None):
    """
    Plot a road marking from a GeoJSON file
    
    Args:
        geojson_file: Path to the GeoJSON file
        unique_id: UNIQUE_ID of the feature to plot (optional)
        index: Index of the feature to plot (optional)
    """
    with open(geojson_file, 'r') as f:
        data = json.load(f)
    
    feature = None
    
    if unique_id:
        # Find by UNIQUE_ID
        for feat in data['features']:
            if feat['properties'].get('UNIQUE_ID') == unique_id:
                feature = feat
                break
    elif index is not None:
        # Find by index
        if 0 <= index < len(data['features']):
            feature = data['features'][index]
    else:
        print("Please provide either unique_id or index")
        return
    
    if feature:
        feature_json = json.dumps(feature)
        plot_road_marking(feature_json)
    else:
        print(f"Feature not found!")

# Main execution
if __name__ == "__main__":
    print("Road Marking Plotter")
    print("=" * 50)
    print("\nOptions:")
    print("1. Plot from JSON string")
    print("2. Plot from file by ID")
    print("3. Plot from file by index")
    
    choice = input("\nEnter your choice (1/2/3): ")
    
    if choice == '1':
        print("\nPaste your feature JSON string (single line):")
        json_string = input()
        plot_road_marking(json_string)
    
    elif choice == '2':
        geojson_file = input("Enter GeoJSON file path: ")
        unique_id = input("Enter UNIQUE_ID: ")
        plot_from_file(geojson_file, unique_id=unique_id)
    
    elif choice == '3':
        geojson_file = input("Enter GeoJSON file path: ")
        index = int(input("Enter feature index (0-based): "))
        plot_from_file(geojson_file, index=index)
    
    else:
        print("Invalid choice!")

# Example usage with a JSON string:
# example_json = '{"type": "Feature", "properties": {"Name": "kml_1", "TYP_CD": "I", "TYP_NAM": "I - 0.1m width - Double Yellow - Continuous - Side Line (no parking at all times on that side of carriageway)", "UNIQUE_ID": "328369"}, "geometry": {"type": "LineString", "coordinates": [[103.876669749692994, 1.34240462601037, 0.0], [103.87672088491, 1.34247783992797, 0.0]]}}'
# plot_road_marking(example_json)1