import dash
from dash import dcc, html, Input, Output, State
import dash_bootstrap_components as dbc

# Initialize the Dash app with Bootstrap theme
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.LUX])

# Sample Data
instances_data = [
    {"InstanceId": "i-123", "Name": "App Server", "State": "Running", "LaunchTime": "2023-08-10"},
    {"InstanceId": "i-456", "Name": "DB Server", "State": "Stopped", "LaunchTime": "2023-09-12"},
]

volumes_data = {
    "i-123": [
        {"VolumeId": "vol-001", "Size": "100GB", "Type": "gp2", "State": "In-use"},
        {"VolumeId": "vol-002", "Size": "200GB", "Type": "gp3", "State": "In-use"},
    ],
    "i-456": [
        {"VolumeId": "vol-003", "Size": "500GB", "Type": "io1", "State": "Available"},
    ],
}

# Helper to create instance cards
def create_instance_cards(instances):
    cards = []
    for instance in instances:
        card = dbc.Card(
            [
                dbc.CardHeader(f"Instance ID: {instance['InstanceId']}", style={'backgroundColor': '#343a40', 'color': 'white'}),
                dbc.CardBody(
                    [
                        html.H5(instance["Name"], className="card-title"),
                        html.P(f"State: {instance['State']}", className="card-text"),
                        html.P(f"Launched: {instance['LaunchTime']}", className="card-text"),
                        dbc.Button("View Volumes", id={"type": "volume-button", "index": instance["InstanceId"]}, color="info", n_clicks=0)
                    ]
                ),
            ],
            style={"width": "18rem", "margin": "10px"},
        )
        cards.append(card)
    return cards

# Replacing Jumbotron with a Container styled as the hero section
hero_section = dbc.Container(
    [
        html.H1("AWS Instance Dashboard", className="display-3"),
        html.P(
            "Monitor and manage your AWS instances and volumes with ease.",
            className="lead",
        ),
        html.Hr(className="my-2"),
        html.P("Select an instance to view its volumes and other details."),
    ],
    fluid=True,
    className="py-3 bg-light rounded-3",
)

# Main layout
app.layout = dbc.Container(
    fluid=True,
    children=[
        hero_section,
        dbc.Row(
            [
                dbc.Col(html.H3("Instances Overview"), width=12),
                dbc.Col(html.Div(id="instance-cards", children=create_instance_cards(instances_data)), width=12),
            ],
            style={"padding": "20px"}
        ),
        dbc.Row(
            [
                dbc.Col(html.H3("Volume Details"), width=12),
                dbc.Col(html.Div(id="volume-details", children=[]), width=12),
            ],
            style={"padding": "20px"}
        ),
    ]
)

# Callback to handle "View Volumes" button clicks
@app.callback(
    Output("volume-details", "children"),
    Input({"type": "volume-button", "index": dash.ALL}, "n_clicks"),
    State({"type": "volume-button", "index": dash.ALL}, "id")
)
def display_volumes(n_clicks, button_ids):
    ctx = dash.callback_context

    if not ctx.triggered:
        return []

    button_id = ctx.triggered[0]["prop_id"].split(".")[0]
    instance_id = eval(button_id)["index"]

    volumes = volumes_data.get(instance_id, [])
    volume_cards = []
    
    for vol in volumes:
        card = dbc.Card(
            dbc.CardBody(
                [
                    html.H5(f"Volume ID: {vol['VolumeId']}", className="card-title"),
                    html.P(f"Size: {vol['Size']}", className="card-text"),
                    html.P(f"Type: {vol['Type']}", className="card-text"),
                    html.P(f"State: {vol['State']}", className="card-text"),
                ]
            ),
            style={"width": "16rem", "margin": "10px"}
        )
        volume_cards.append(card)
    
    return dbc.Collapse(
        dbc.Row(volume_cards, className="d-flex flex-wrap"),
        is_open=True,
    )

if __name__ == "__main__":
    app.run_server(debug=True)