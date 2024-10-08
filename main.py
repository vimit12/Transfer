# Import necessary libraries
import dash

from dash import Dash, dcc, html, Input, Output
from dash.dependencies import Input, Output, State, ALL
import pandas as pd
import json
from dash import callback_context

def load_data():
    with open('data.json') as f:
        data = json.load(f)
    
    instances_list = []
    volumes_list = []
    snapshots_list = []

    for entry in data:
        # Extract volume info
        volume_info = entry['volume_info']
        volumes_list.append(volume_info)

        # Extract instance info
        for instance in entry['instance_info']:
            instances_list.append(instance)

        # Extract snapshot info
        for snapshot in entry['snapshot_ids_with_time']:
            snapshot['volume_id'] = volume_info['volume_id']  # Add volume ID to snapshots
            snapshots_list.append(snapshot)

    instances_df = pd.DataFrame(instances_list)
    volumes_df = pd.DataFrame(volumes_list)
    snapshots_df = pd.DataFrame(snapshots_list)
    
    return instances_df, volumes_df, snapshots_df



app = Dash(__name__)

# Load data
instances_df, volumes_df, snapshots_df = load_data()

# Layout
app.layout = html.Div([
    dcc.Dropdown(
        id='backup-id-dropdown',
        options=[{'label': bid, 'value': bid} for bid in instances_df['BackupID'].unique()],
        placeholder="Select Backup ID"
    ),
    html.Div(id='instance-cards'),
    dcc.Store(id='selected-instance-id'),
    dcc.Store(id='selected-volume-id')
])

# Callback to display instances based on selected BackupID
@app.callback(
    Output('instance-cards', 'children'),
    Input('backup-id-dropdown', 'value')
)
def update_instance_cards(selected_backup_id):
    if selected_backup_id is None:
        return []

    filtered_instances = instances_df[instances_df['BackupID'] == selected_backup_id]
    cards = []

    for _, row in filtered_instances.iterrows():
        cards.append(html.Div([
            html.H4(row['InstanceId']),
            html.Button('View Volumes', id={'type': 'volume-button', 'instance_id': row['InstanceId']}),
            # Store selected instance ID
            dcc.Store(id='selected-instance-id', data=row['InstanceId'])
        ]))

    return cards

# Callback to display volumes for selected instance
@app.callback(
    Output('instance-cards', 'children', True),
    Input({'type': 'volume-button', 'instance_id': ALL}, 'n_clicks'),
    prevent_initial_call=True
)
def display_volumes(n_clicks):
    ctx = dash.callback_context
    if not ctx.triggered:
        return []
    
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    selected_instance_id = eval(button_id)['instance_id']  # Extract instance_id from button id
    filtered_volumes = volumes_df[volumes_df['InstanceId'] == selected_instance_id]
    print("VOL", filtered_volumes)
    volume_cards = []
    for _, vol in filtered_volumes.iterrows():
        volume_cards.append(html.Div([
            html.H5(vol['volume_id']),
            html.Button('View Snapshots', id={'type': 'snapshot-button', 'volume_id': vol['volume_id']}),
            # Store selected volume ID
            dcc.Store(id='selected-volume-id', data=vol['volume_id'])
        ]))

    return volume_cards

# # Callback to display snapshots for selected volume
# @app.callback(
#     Output('instance-cards', 'children'),
#     Input({'type': 'snapshot-button', 'volume_id': ALL}, 'n_clicks'),
#     prevent_initial_call=True
# )
# def display_snapshots(n_clicks):
#     ctx = dash.callback_context
#     if not ctx.triggered:
#         return []
    
#     button_id = ctx.triggered[0]['prop_id'].split('.')[0]
#     selected_volume_id = eval(button_id)['volume_id']  # Extract volume_id from button id
#     filtered_snapshots = snapshots_df[snapshots_df['volume_id'] == selected_volume_id]
    
#     snapshot_cards = []
#     for _, snap in filtered_snapshots.iterrows():
#         snapshot_cards.append(html.Div([
#             html.P(f"Snapshot ID: {snap['SnapshotId']}"),
#             html.P(f"Created on: {snap['SnapshotCreateDateTime']}"),
#             html.P(f"Description: {snap['Description']}")
#         ]))

#     return snapshot_cards

if __name__ == '__main__':
    app.run_server(debug=True)