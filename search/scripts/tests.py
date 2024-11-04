"""
import os 
import sys 
from pathlib import Path
import subprocess

result = subprocess.run(['gcloud', 'compute', 'instances', 'describe', 'instance-2-test', '--zone', 'us-central1-a', '--format=get(status)'],
                        check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

print(result.stdout)

import plotly.graph_objects as go
import networkx as nx
import pandas as pd 
from pathlib import Path
import sys
secrets_path = str(Path(__file__).resolve().parents[1].parents[0] / 'secrets')
sys.path.insert(0, secrets_path)


from route_data.load_routes import codes_found, routes_with_cords, airport_routes

codes = [i[0:3] for i in codes_found['Airport Code'].to_list()]
lat = codes_found['Latitude'].to_list()
long = codes_found['Longitude'].to_list()
country = codes_found['Country Name'].to_list()
city = codes_found['City Name'].to_list()

# The line below removes codes that locations have not yet been found for 
# TODO ==== Find Locations for the missing codes ====
routes_with_cords = routes_with_cords.loc[routes_with_cords['Departure_Airport_IATA'].isin(codes) & routes_with_cords['Arrival_Airport_IATA'].isin(codes)]

depatures_cords = [i[0:3] for i in routes_with_cords['Departure_Airport_IATA'].to_list()]
arrivals_cords = [i[0:3] for i in routes_with_cords['Arrival_Airport_IATA'].to_list()]

# Create routes network 
G = nx.Graph()

# Create nodes
for i in range(len(codes)):
    G.add_node(codes[i], latitude=lat[i], longitude=long[i], country=country[i], city=city[i])

# Connect nodes
for i in range(len(depatures_cords)):
    G.add_edge(depatures_cords[i], arrivals_cords[i])

for node in G.nodes():
    print(node , " : ", G.nodes[node])


# Assuming all nodes now have latitude and longitude attributes
pos = {node: (G.nodes[node]['longitude'], G.nodes[node]['latitude']) for node in G.nodes()}

# Create edge traces with lighter lines
edge_trace = []
for edge in G.edges():
    x0, y0 = pos[edge[0]]
    x1, y1 = pos[edge[1]]
    edge_trace.append(go.Scattergeo(
        lon=[x0, x1],
        lat=[y0, y1],
        mode='lines',
        line=dict(width=1, color='rgba(0, 0, 255, 0.3)'),  # Light blue color with 30% opacity
    ))

# Create node trace with smaller markers
node_trace = go.Scattergeo(
    lon=[pos[node][0] for node in G.nodes()],
    lat=[pos[node][1] for node in G.nodes()],
    mode='markers',
    text=[f"{G.nodes[node]['city']}, {G.nodes[node]['country']}" for node in G.nodes()],
    marker=dict(size=5, color='orange'),  # Smaller markers with size 6
    textposition="top center"
)

# Create the figure
fig = go.Figure(data=edge_trace + [node_trace])

# Update layout
fig.update_layout(
    title="Graph Visualization with Smaller Markers",
    showlegend=False,
    geo=dict(
        projection_type='natural earth',
        showland=True,
        landcolor="rgb(217, 217, 217)",
    )
)

# Show the figure
fig.show()
"""
import undetected_chromedriver as uc 
import certifi
import os

# certificate
os.environ['SSL_CERT_FILE'] = certifi.where()

options = uc.ChromeOptions()
options.add_argument("--headless")
# options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_argument("--disable-infobars")
options.add_argument("--start-maximized")
options.add_argument("--disable-gpu")
options.add_argument("--disable-extensions")
options.add_argument("--proxy-bypass-list=*")
options.add_argument("--disable-software-rasterizer")
# options.add_argument("--disable-web-security")
options.add_argument("--lang=en-US")
options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
driver = uc.Chrome(options=options)
# driver = webdriver.Chrome(options= options, service=ChromeService(ChromeDriverManager().install()))

# Inject JavaScript to modify properties

driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
    "source": """
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined
        });

        window.navigator.chrome = {
            runtime: {},
            // Add other necessary properties if needed
        };

        const originalQuery = window.navigator.permissions.query;
        window.navigator.permissions.query = (parameters) => (
            parameters.name === 'notifications' ?
                Promise.resolve({ state: Notification.permission }) :
                originalQuery(parameters)
        );

        Object.defineProperty(navigator, 'plugins', {
            get: () => [1, 2, 3],
        });

        Object.defineProperty(navigator, 'languages', {
            get: () => ['en-US', 'en'],
        });

        Object.defineProperty(screen, 'availWidth', {
            get: () => screen.width,
        });

        Object.defineProperty(screen, 'availHeight', {
            get: () => screen.height,
        });

        const getParameter = WebGLRenderingContext.prototype.getParameter;
        WebGLRenderingContext.prototype.getParameter = function(parameter) {
            // UNMASKED_VENDOR_WEBGL
            if (parameter === 37445) {
                return 'Intel Inc.';
            }
            // UNMASKED_RENDERER_WEBGL
            if (parameter === 37446) {
                return 'Intel Iris OpenGL Engine';
            }
            return getParameter(parameter);
        };
    """})



driver.get("https://www.aa.com")
print(driver.title)