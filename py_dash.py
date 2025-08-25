# -*- coding: utf-8 -*-
# Full PyQt6 + Dash Leave Analytics Dashboard
# Adds: Year filter, KPIs, multiple charts, moving average trend,
# MoM change, top leave months, cumulative attendance, multi-employee comparison,
# CSV export, and PNG export of any chart (requires `pip install kaleido`).

import sys
import threading
import json
import time
import webbrowser

import pandas as pd

import dash
from dash import html, dcc, Input, Output, State, dash_table
import plotly.express as px
import plotly.graph_objects as go

from PyQt6.QtWidgets import QApplication, QMessageBox

# -------------------------
# 1) Load JSON data
# -------------------------
with open("leave_summary.json") as f:
    data = json.load(f)

df = pd.DataFrame(data)
# Ensure proper types and ordering
df["Year"] = df["Year"].astype(int)
df["Month_Year"] = pd.to_datetime(df["Month"] + " " + df["Year"].astype(str))
df = df.sort_values(["Full Name", "Month_Year"]).reset_index(drop=True)

# Precompute useful columns
df["Attendance %"] = 100 - (df["Leave Taken Days"] / df["Total Working Days"] * 100)
df["Month_Abbr"] = df["Month_Year"].dt.strftime("%b %Y")

years = sorted(df["Year"].unique())
employees = sorted(df["Full Name"].unique())

# -------------------------
# 2) Dash app
# -------------------------
dash_app = dash.Dash(__name__)
dash_app.title = "Leave & Attendance Dashboard"


def kpi_card(title, value):
    return html.Div(
        [
            html.H4(title, style={"margin": 0}),
            html.H2(value, style={"margin": 0, "fontWeight": "700"})
        ],
        style={
            "padding": "14px 16px",
            "border": "1px solid #e5e7eb",
            "borderRadius": "10px",
            "boxShadow": "0 1px 4px rgba(0,0,0,0.06)",
            "textAlign": "center",
            "width": "24%",
            "background": "white"
        }
    )


dash_app.layout = html.Div(
    [
        html.H1("Employee Leave & Attendance Dashboard", style={"textAlign": "center", "marginBottom": 10}),
        html.Div(
            [
                html.Div(
                    [
                        html.Label("Employee"),
                        dcc.Dropdown(
                            id="employee-dropdown",
                            options=[{"label": n, "value": n} for n in employees],
                            value=employees[0],
                            clearable=False,
                        ),
                    ],
                    style={"width": "32%"}
                ),
                html.Div(
                    [
                        html.Label("Year"),
                        dcc.Dropdown(
                            id="year-dropdown",
                            options=[{"label": int(y), "value": int(y)} for y in years],
                            value=years[-1],
                            clearable=False,
                        ),
                    ],
                    style={"width": "16%"}
                ),
                html.Div(
                    [
                        html.Label("Attendance Threshold (%)"),
                        dcc.Slider(
                            id="threshold-slider",
                            min=50, max=100, step=1, value=90,
                            marks={x: str(x) for x in range(50, 101, 10)}
                        ),
                    ],
                    style={"width": "42%", "paddingTop": "6px"}
                ),
                html.Div(
                    [
                        html.Button("Download Filtered CSV", id="download-csv-btn", n_clicks=0),
                        dcc.Download(id="download-csv"),
                    ],
                    style={"width": "10%", "display": "flex", "alignItems": "end", "justifyContent": "flex-end"}
                )
            ],
            style={"display": "flex", "gap": "2%", "marginBottom": 12}
        ),

        # KPI Row
        html.Div(id="kpi-row", style={"display": "flex", "gap": "2%", "marginBottom": 16}),

        # Tabs for charts
        dcc.Tabs(
            id="tabs",
            value="tab-overview",
            children=[
                dcc.Tab(label="Overview", value="tab-overview", children=[
                    html.Div(
                        [
                            dcc.Graph(id="fig-leave-bar"),
                            dcc.Graph(id="fig-leave-vs-working-line"),
                            dcc.Graph(id="fig-attendance-perc"),
                        ],
                        style={"padding": "8px 0"}
                    ),
                ]),
                dcc.Tab(label="Trends", value="tab-trends", children=[
                    html.Div(
                        [
                            dcc.Graph(id="fig-attendance-trend-ma"),
                            dcc.Graph(id="fig-mom-change"),
                            dcc.Graph(id="fig-cumulative-attendance"),
                        ],
                        style={"padding": "8px 0"}
                    ),
                ]),
                dcc.Tab(label="Comparisons", value="tab-compare", children=[
                    html.Div(
                        [
                            dcc.Graph(id="fig-heatmap-employee"),
                            dcc.Graph(id="fig-multi-employee-attendance"),
                            dcc.Graph(id="fig-top-leave-months"),
                        ],
                        style={"padding": "8px 0"}
                    ),
                ]),
                dcc.Tab(label="Export Chart", value="tab-export", children=[
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.Label("Select chart to export as PNG"),
                                    dcc.Dropdown(
                                        id="export-fig-selector",
                                        options=[
                                            {"label": "Leave Taken (Bar)", "value": "fig-leave-bar"},
                                            {"label": "Leave vs Working (Line)", "value": "fig-leave-vs-working-line"},
                                            {"label": "Attendance % (Bar)", "value": "fig-attendance-perc"},
                                            {"label": "Attendance Trend MA (Line)", "value": "fig-attendance-trend-ma"},
                                            {"label": "MoM Change (Bar)", "value": "fig-mom-change"},
                                            {"label": "Cumulative Attendance (Line)",
                                             "value": "fig-cumulative-attendance"},
                                            {"label": "Employee Heatmap", "value": "fig-heatmap-employee"},
                                            {"label": "Multi-Employee Attendance",
                                             "value": "fig-multi-employee-attendance"},
                                            {"label": "Top Leave Months", "value": "fig-top-leave-months"},
                                        ],
                                        value="fig-attendance-perc",
                                        clearable=False
                                    ),
                                    html.Button("Download PNG", id="download-png-btn", n_clicks=0,
                                                style={"marginTop": "8px"}),
                                    dcc.Download(id="download-png"),
                                ],
                                style={"width": "320px"}
                            ),
                            html.Div(
                                [
                                    html.P("Tip: PNG export requires the 'kaleido' package.",
                                           style={"marginTop": "14px"}),
                                    html.Code("pip install kaleido")
                                ],
                                style={"marginLeft": "24px"}
                            )
                        ],
                        style={"display": "flex", "alignItems": "start", "padding": "16px"}
                    )
                ]),
                # -------------------------
                # Consolidated Report Tab (Add inside dcc.Tabs children)
                # -------------------------
                dcc.Tab(label="Consolidated Report", value="tab-consolidated", children=[
                    html.Div([
                        html.Div([
                            html.Label("Select Year:"),
                            dcc.Dropdown(
                                id="consolidated-year-dropdown",
                                options=[{"label": y, "value": y} for y in years],
                                value=years[-1],
                                clearable=False,
                                style={"width": "150px", "marginRight": "12px"}
                            ),
                        ], style={"display": "inline-block", "marginRight": "24px"}),

                        html.Div([
                            html.Label("Select Month:"),
                            dcc.Dropdown(
                                id="consolidated-month-dropdown",
                                options=[{"label": m, "value": m} for m in df["Month"].unique()],
                                value=df["Month"].unique()[0],
                                clearable=False,
                                style={"width": "150px"}
                            ),
                        ], style={"display": "inline-block", "marginRight": "24px"}),

                        html.Div([
                            html.Label("Attendance Threshold (%)"),
                            dcc.Slider(
                                id="consolidated-threshold-slider",
                                min=50, max=100, step=1, value=90,
                                marks={x: str(x) for x in range(50, 101, 10)},
                                tooltip={"placement": "bottom", "always_visible": True},
                            ),
                        ], style={"display": "inline-block", "width": "300px", "marginRight": "24px"}),

                        html.Button("Download CSV", id="download-consolidated-csv-btn", n_clicks=0,
                                    style={"height": "32px", "marginTop": "22px"}),
                        dcc.Download(id="download-consolidated-csv"),
                    ], style={"display": "flex", "alignItems": "center", "gap": "12px", "marginBottom": "12px"}),

                    # Table for consolidated report
                    html.Div(id="consolidated-table-container")
                ])

            ],
            style={"background": "white", "borderRadius": "8px"}
        ),
        # Hidden stores to pass figures for PNG export
        dcc.Store(id="store-fig-leave-bar"),
        dcc.Store(id="store-fig-leave-vs-working-line"),
        dcc.Store(id="store-fig-attendance-perc"),
        dcc.Store(id="store-fig-attendance-trend-ma"),
        dcc.Store(id="store-fig-mom-change"),
        dcc.Store(id="store-fig-cumulative-attendance"),
        dcc.Store(id="store-fig-heatmap-employee"),
        dcc.Store(id="store-fig-multi-employee-attendance"),
        dcc.Store(id="store-fig-top-leave-months"),
    ],
    style={"maxWidth": "1300px", "margin": "0 auto", "padding": "10px 14px", "background": "#f8fafc"}
)


# -------------------------
# 3) Main update callback (figures + KPIs + stores)
# -------------------------
@dash_app.callback(
    Output("kpi-row", "children"),
    Output("fig-leave-bar", "figure"),
    Output("fig-leave-vs-working-line", "figure"),
    Output("fig-attendance-perc", "figure"),
    Output("fig-attendance-trend-ma", "figure"),
    Output("fig-mom-change", "figure"),
    Output("fig-cumulative-attendance", "figure"),
    Output("fig-heatmap-employee", "figure"),
    Output("fig-multi-employee-attendance", "figure"),
    Output("fig-top-leave-months", "figure"),
    # also store figs as JSON for PNG export
    Output("store-fig-leave-bar", "data"),
    Output("store-fig-leave-vs-working-line", "data"),
    Output("store-fig-attendance-perc", "data"),
    Output("store-fig-attendance-trend-ma", "data"),
    Output("store-fig-mom-change", "data"),
    Output("store-fig-cumulative-attendance", "data"),
    Output("store-fig-heatmap-employee", "data"),
    Output("store-fig-multi-employee-attendance", "data"),
    Output("store-fig-top-leave-months", "data"),
    Input("employee-dropdown", "value"),
    Input("year-dropdown", "value"),
    Input("threshold-slider", "value"),
)
def update_all(selected_employee, selected_year, threshold):
    # Filter for employee/year
    df_emp = df[(df["Full Name"] == selected_employee) & (df["Year"] == selected_year)].copy()
    df_emp = df_emp.sort_values("Month_Year").reset_index(drop=True)
    # Year-wide data (all employees) for comparisons
    df_year = df[df["Year"] == selected_year].copy()

    # --- KPIs ---
    total_leave = int(df_emp["Leave Taken Days"].sum()) if not df_emp.empty else 0
    avg_att = round(df_emp["Attendance %"].mean(), 2) if not df_emp.empty else 0.0
    min_att_month = df_emp.loc[df_emp["Attendance %"].idxmin(), "Month"] if not df_emp.empty else "—"
    alerts = df_emp[df_emp["Attendance %"] < 80]["Month"].tolist() if not df_emp.empty else []
    kpis = [
        kpi_card("Total Leave Days", str(total_leave)),
        kpi_card("Average Attendance %", f"{avg_att}%"),
        kpi_card("Lowest Attendance Month", str(min_att_month)),
        kpi_card("Alerts (<80%)", ", ".join(alerts) if alerts else "None"),
    ]

    # --- Leave Taken (Bar) ---
    fig_leave_bar = px.bar(
        df_emp, x="Month_Year", y="Leave Taken Days", text="Leave Taken Days",
        title=f"Leave Taken Days per Month — {selected_employee} ({selected_year})",
        labels={"Month_Year": "Month", "Leave Taken Days": "Days"},
        hover_data=["Dates of Leave", "Total Working Days"]
    )
    fig_leave_bar.update_xaxes(ticktext=df_emp["Month_Abbr"], tickvals=df_emp["Month_Year"])

    # --- Leave vs Working (Line) ---
    fig_line = px.line(
        df_emp, x="Month_Year", y=["Leave Taken Days", "Total Working Days"],
        markers=True,
        title=f"Leave vs Total Working Days — {selected_employee} ({selected_year})",
        labels={"value": "Days", "variable": "Metric", "Month_Year": "Month"},
    )
    fig_line.update_xaxes(ticktext=df_emp["Month_Abbr"], tickvals=df_emp["Month_Year"])

    # --- Attendance % (Bar) with threshold coloring ---
    colors = ["red" if v < threshold else "green" for v in df_emp["Attendance %"]]
    fig_att_perc = px.bar(
        df_emp, x="Month_Year", y="Attendance %", text=df_emp["Attendance %"].round(1),
        title=f"Attendance % — {selected_employee} ({selected_year})  (Threshold: {threshold}%)",
        labels={"Month_Year": "Month", "Attendance %": "% Attendance"},
    )
    fig_att_perc.update_traces(marker_color=colors, showlegend=False)
    fig_att_perc.update_xaxes(ticktext=df_emp["Month_Abbr"], tickvals=df_emp["Month_Year"])

    # --- Attendance Trend (3-mo MA) ---
    df_emp["Attendance_MA"] = df_emp["Attendance %"].rolling(window=3, min_periods=1).mean()
    fig_trend = px.line(
        df_emp, x="Month_Year", y="Attendance_MA", markers=True,
        title=f"Attendance Trend — 3-Month Moving Average ({selected_employee}, {selected_year})",
        labels={"Month_Year": "Month", "Attendance_MA": "Attendance % (3-mo MA)"},
    )
    fig_trend.update_xaxes(ticktext=df_emp["Month_Abbr"], tickvals=df_emp["Month_Year"])

    # --- Month-over-Month Change ---
    df_emp["MoM_Change"] = df_emp["Attendance %"].diff().fillna(0.0)
    fig_mom = px.bar(
        df_emp, x="Month_Year", y="MoM_Change", text=df_emp["MoM_Change"].round(1),
        title=f"Month-over-Month Attendance Change — {selected_employee} ({selected_year})",
        labels={"Month_Year": "Month", "MoM_Change": "Δ %"},
    )
    fig_mom.update_xaxes(ticktext=df_emp["Month_Abbr"], tickvals=df_emp["Month_Year"])

    # --- Cumulative Attendance % (simple running mean) ---
    if not df_emp.empty:
        df_emp["Cum_Att"] = df_emp["Attendance %"].expanding().mean()
    else:
        df_emp["Cum_Att"] = []
    fig_cum = px.line(
        df_emp, x="Month_Year", y="Cum_Att", markers=True,
        title=f"Cumulative Attendance % — {selected_employee} ({selected_year})",
        labels={"Month_Year": "Month", "Cum_Att": "Cumulative %"},
    )
    fig_cum.update_xaxes(ticktext=df_emp["Month_Abbr"], tickvals=df_emp["Month_Year"])

    # --- Employee Heatmap (Leave Days by month) ---
    # single employee heatmap may be 1-row; still useful
    if not df_emp.empty:
        heat_df = df_emp.pivot(index="Full Name", columns="Month_Year", values="Leave Taken Days")
        heat_df = heat_df.reindex(columns=df_emp["Month_Year"])  # keep chronological
        fig_heat = px.imshow(
            heat_df,
            text_auto=True,
            labels={"x": "Month", "y": "Employee", "color": "Leave Days"},
            title=f"Leave Heatmap — {selected_employee} ({selected_year})",
        )
        fig_heat.update_xaxes(ticktext=df_emp["Month_Abbr"], tickvals=heat_df.columns)
    else:
        fig_heat = go.Figure().update_layout(title="Leave Heatmap — No data")

    # --- Multi-Employee Attendance % grouped ---
    multi = df_year.groupby(["Full Name", "Month_Year"], as_index=False).agg(
        {"Leave Taken Days": "sum", "Total Working Days": "sum"}
    )
    multi["Attendance %"] = 100 - (multi["Leave Taken Days"] / multi["Total Working Days"] * 100)
    multi = multi.sort_values("Month_Year")
    fig_multi = px.bar(
        multi, x="Month_Year", y="Attendance %", color="Full Name", barmode="group",
        title=f"Attendance % by Employee — {selected_year}",
        labels={"Month_Year": "Month", "Attendance %": "% Attendance", "Full Name": "Employee"},
    )
    # Month labels
    month_labels = multi["Month_Year"].dt.strftime("%b %Y").unique().tolist()
    month_vals = multi["Month_Year"].drop_duplicates().tolist()
    fig_multi.update_xaxes(ticktext=month_labels, tickvals=month_vals)

    # --- Top 5 Leave Months (for selected employee) ---
    top5 = df_emp.sort_values("Leave Taken Days", ascending=False).head(5)
    fig_top = px.bar(
        top5, x="Month_Year", y="Leave Taken Days", text="Leave Taken Days",
        title=f"Top 5 Months with Most Leave — {selected_employee} ({selected_year})",
        labels={"Month_Year": "Month", "Leave Taken Days": "Days"},
    )
    fig_top.update_xaxes(ticktext=top5["Month_Abbr"], tickvals=top5["Month_Year"])

    # Serialize figures for PNG export (to_json)
    store_data = [
        fig_leave_bar.to_plotly_json(),
        fig_line.to_plotly_json(),
        fig_att_perc.to_plotly_json(),
        fig_trend.to_plotly_json(),
        fig_mom.to_plotly_json(),
        fig_cum.to_plotly_json(),
        fig_heat.to_plotly_json(),
        fig_multi.to_plotly_json(),
        fig_top.to_plotly_json(),
    ]

    return (
        kpis,
        fig_leave_bar, fig_line, fig_att_perc,
        fig_trend, fig_mom, fig_cum,
        fig_heat, fig_multi, fig_top,
        *store_data
    )


# -------------------------
# 4) CSV download for filtered employee/year
# -------------------------
@dash_app.callback(
    Output("download-csv", "data"),
    Input("download-csv-btn", "n_clicks"),
    State("employee-dropdown", "value"),
    State("year-dropdown", "value"),
    prevent_initial_call=True
)
def download_csv(n, employee, year):
    dff = df[(df["Full Name"] == employee) & (df["Year"] == year)].copy()
    if dff.empty:
        dff = pd.DataFrame(columns=df.columns)
    return dcc.send_data_frame(dff.to_csv, f"leave_data_{employee}_{year}.csv", index=False)


# -------------------------
# 5) PNG chart download (requires kaleido)
# -------------------------
@dash_app.callback(
    Output("download-png", "data"),
    Input("download-png-btn", "n_clicks"),
    State("export-fig-selector", "value"),
    State("store-fig-leave-bar", "data"),
    State("store-fig-leave-vs-working-line", "data"),
    State("store-fig-attendance-perc", "data"),
    State("store-fig-attendance-trend-ma", "data"),
    State("store-fig-mom-change", "data"),
    State("store-fig-cumulative-attendance", "data"),
    State("store-fig-heatmap-employee", "data"),
    State("store-fig-multi-employee-attendance", "data"),
    State("store-fig-top-leave-months", "data"),
    prevent_initial_call=True
)
def download_png(n, fig_key, *stored_figs):
    key_map = {
        "fig-leave-bar": 0,
        "fig-leave-vs-working-line": 1,
        "fig-attendance-perc": 2,
        "fig-attendance-trend-ma": 3,
        "fig-mom-change": 4,
        "fig-cumulative-attendance": 5,
        "fig-heatmap-employee": 6,
        "fig-multi-employee-attendance": 7,
        "fig-top-leave-months": 8,
    }
    idx = key_map.get(fig_key, 2)
    fig_json = stored_figs[idx]
    fig = go.Figure(fig_json)
    png_bytes = fig.to_image(format="png", scale=2)  # needs kaleido
    return dcc.send_bytes(png_bytes, f"{fig_key}.png")


# -------------------------
# Callback to update consolidated report table
# -------------------------
@dash_app.callback(
    Output("consolidated-table-container", "children"),
    Input("consolidated-year-dropdown", "value"),
    Input("consolidated-month-dropdown", "value"),
    Input("consolidated-threshold-slider", "value")
)
def update_consolidated_table(selected_year, selected_month, threshold):
    dff = df[(df["Year"] == selected_year) & (df["Month"] == selected_month)].copy()
    if dff.empty:
        return html.P("No data available for selected year/month.")

    # Highlight Attendance < threshold in red
    def color_att(val):
        color = "red" if val < threshold else "green"
        return f"color: {color}; font-weight: 700;"

    # Build table
    table = html.Table([
        html.Thead([
            html.Tr([html.Th(c) for c in ["Full Name", "Leave Taken Days", "Total Working Days", "Attendance %"]])
        ]),
        html.Tbody([
            html.Tr([
                html.Td(row["Full Name"]),
                html.Td(row["Leave Taken Days"]),
                html.Td(row["Total Working Days"]),
                html.Td(f"{row['Attendance %']:.1f}%",
                        style={"color": "red" if row["Attendance %"] < threshold else "green", "fontWeight": "700"})
            ]) for _, row in dff.iterrows()
        ])
    ], style={"borderCollapse": "collapse", "width": "100%"})

    return table


# -------------------------
# CSV download for consolidated report
# -------------------------
@dash_app.callback(
    Output("download-consolidated-csv", "data"),
    Input("download-consolidated-csv-btn", "n_clicks"),
    State("consolidated-year-dropdown", "value"),
    State("consolidated-month-dropdown", "value"),
    prevent_initial_call=True
)
def download_consolidated_csv(n_clicks, year, month):
    dff = df[(df["Year"] == year) & (df["Month"] == month)].copy()
    if dff.empty:
        dff = pd.DataFrame(columns=["Full Name", "Leave Taken Days", "Total Working Days", "Attendance %"])
    return dcc.send_data_frame(dff.to_csv, f"consolidated_attendance_{month}_{year}.csv", index=False)


# -------------------------
# 6) Run Dash (thread) + PyQt fallback
# -------------------------
def run_dash():
    dash_app.run(port=8050, debug=False, use_reloader=False)


if __name__ == "__main__":
    thread = threading.Thread(target=run_dash, daemon=True)
    thread.start()
    time.sleep(2)

    url = "http://127.0.0.1:8050"
    try:
        opened = webbrowser.open(url)
    except Exception:
        opened = False

    if not opened:
        app = QApplication(sys.argv)
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Icon.Information)
        msg.setWindowTitle("Open Dashboard")
        msg.setText(f"Your Dash app is running!\n\nOpen this link in your browser:\n{url}")
        msg.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg.exec()
        sys.exit(0)

    print(f"✅ Dash app running at {url}")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down...")
        sys.exit(0)
