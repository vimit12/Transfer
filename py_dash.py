# -*- coding: utf-8 -*-
# Enhanced Leave Analytics Dashboard with Working/Billable Days Option
# Full PyQt6 + Dash Leave Analytics Dashboard
import calendar
import sys
import threading
import json
import time
import webbrowser

import pandas as pd

import dash
import dash_bootstrap_components as dbc
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
# Define proper month order
month_order = list(calendar.month_name)[1:]  # ["January", "February", ..., "December"]

# Ensure df["Month"] is categorical in the right order
df["Month"] = pd.Categorical(df["Month"], categories=month_order, ordered=True)

# Precompute useful columns
df["Month_Abbr"] = df["Month_Year"].dt.strftime("%b %Y")

years = sorted(df["Year"].unique())
employees = sorted(df["Full Name"].unique())

# -------------------------
# 2) Dash app with Bootstrap
# -------------------------
dash_app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
dash_app.title = "Leave & Attendance Dashboard"


def kpi_card(title, value, color="primary"):
    return dbc.Card(
        dbc.CardBody(
            [
                html.H6(title, className="card-subtitle mb-2 text-muted kpi-title"),
                html.H4(
                    f"{value}", className=f"card-title text-{color} font-weight-bold kpi-title"
                ),
            ],
            className="text-center",
        ),
        className="mb-3 shadow-sm kpi-card",
    )


dash_app.layout = dbc.Container(
    # # Inject custom CSS
    # html.Div([html.Style(custom_style)]),
    fluid=True,
    children=[  # Header
        dbc.Row(
            [
                dbc.Col(
                    [
                        html.H1(
                            "Employee Leave & Attendance Dashboard",
                            className="text-center my-4 text-primary",
                        ),
                        html.P(
                            "Comprehensive analysis of employee leave patterns and attendance trends",
                            className="text-center text-muted mb-4",
                        ),
                    ]
                )
            ]
        ),
        # Filters and Controls
        dbc.Card(
            [
                dbc.CardBody(
                    [
                        dbc.Row(
                            [
                                dbc.Col(
                                    [
                                        dbc.Label(
                                            "Employee", html_for="employee-dropdown"
                                        ),
                                        dcc.Dropdown(
                                            id="employee-dropdown",
                                            options=[
                                                {"label": n, "value": n}
                                                for n in employees
                                            ],
                                            value=employees[0],
                                            clearable=False,
                                            className="mb-2",
                                        ),
                                    ],
                                    width=3,
                                ),
                                dbc.Col(
                                    [
                                        dbc.Label("Year", html_for="year-dropdown"),
                                        dcc.Dropdown(
                                            id="year-dropdown",
                                            options=[
                                                {"label": int(y), "value": int(y)}
                                                for y in years
                                            ],
                                            value=years[-1],
                                            clearable=False,
                                            className="mb-2",
                                        ),
                                    ],
                                    width=2,
                                ),
                                dbc.Col(
                                    [
                                        dbc.Label(
                                            "Calculation Base",
                                            html_for="calculation-base-dropdown",
                                        ),
                                        dcc.Dropdown(
                                            id="calculation-base-dropdown",
                                            options=[
                                                {
                                                    "label": "Total Working Days",
                                                    "value": "Total Working Days",
                                                },
                                                {
                                                    "label": "Total Billable Days",
                                                    "value": "Total Billable Days",
                                                },
                                            ],
                                            value="Total Working Days",
                                            clearable=False,
                                            className="mb-2",
                                        ),
                                    ],
                                    width=2,
                                ),
                                dbc.Col(
                                    [
                                        dbc.Label(
                                            "Attendance Threshold (%)",
                                            html_for="threshold-slider",
                                        ),
                                        dcc.Slider(
                                            id="threshold-slider",
                                            min=50,
                                            max=100,
                                            step=1,
                                            value=90,
                                            marks={
                                                x: str(x) for x in range(50, 101, 10)
                                            },
                                            tooltip={
                                                "placement": "bottom",
                                                "always_visible": True,
                                            },
                                        ),
                                    ],
                                    width=3,
                                ),
                                dbc.Col(
                                    [
                                        dbc.Button(
                                            "Download Filtered CSV",
                                            id="download-csv-btn",
                                            color="success",
                                            className="mt-4 w-100 btn-custom",
                                        ),
                                        dcc.Download(id="download-csv"),
                                    ],
                                    width=2,
                                ),
                            ],
                            align="center",
                        )
                    ]
                )
            ],
            className="mb-4 shadow",
        ),
        # KPI Row
        dbc.Row([dbc.Col(html.Div(id="kpi-row"), width=12)], className="mb-4"),
        # Tabs for charts
        dbc.Card(
            [
                dbc.CardBody(
                    [
                        dcc.Tabs(
                            id="tabs",
                            value="tab-overview",
                            className="mb-3",
                            children=[
                                dcc.Tab(
                                    label="Overview",
                                    value="tab-overview",
                                    className="py-2 custom-tab",
                                    children=[
                                        dbc.Row(
                                            [
                                                dbc.Col(
                                                    dcc.Graph(id="fig-leave-bar"),
                                                    width=12,
                                                    className="mb-3",
                                                ),
                                                dbc.Col(
                                                    dcc.Graph(
                                                        id="fig-leave-vs-working-line"
                                                    ),
                                                    width=12,
                                                    className="mb-3",
                                                ),
                                                dbc.Col(
                                                    dcc.Graph(id="fig-attendance-perc"),
                                                    width=12,
                                                ),
                                            ]
                                        )
                                    ],
                                ),
                                dcc.Tab(
                                    label="Trends",
                                    value="tab-trends",
                                    className="py-2 custom-tab",
                                    children=[
                                        dbc.Row(
                                            [
                                                dbc.Col(
                                                    dcc.Graph(
                                                        id="fig-attendance-trend-ma"
                                                    ),
                                                    width=12,
                                                    className="mb-3",
                                                ),
                                                dbc.Col(
                                                    dcc.Graph(id="fig-mom-change"),
                                                    width=12,
                                                    className="mb-3",
                                                ),
                                                dbc.Col(
                                                    dcc.Graph(
                                                        id="fig-cumulative-attendance"
                                                    ),
                                                    width=12,
                                                ),
                                            ]
                                        )
                                    ],
                                ),
                                dcc.Tab(
                                    label="Comparisons",
                                    value="tab-compare",
                                    className="py-2 custom-tab",
                                    children=[
                                        dbc.Row(
                                            [
                                                dbc.Col(
                                                    dcc.Graph(
                                                        id="fig-heatmap-employee"
                                                    ),
                                                    width=12,
                                                    className="mb-3",
                                                ),
                                                dbc.Col(
                                                    dcc.Graph(
                                                        id="fig-multi-employee-attendance"
                                                    ),
                                                    width=12,
                                                    className="mb-3",
                                                ),
                                                dbc.Col(
                                                    dcc.Graph(
                                                        id="fig-top-leave-months"
                                                    ),
                                                    width=12,
                                                ),
                                            ]
                                        )
                                    ],
                                ),
                                dcc.Tab(
                                    label="Export Chart",
                                    value="tab-export",
                                    className="py-2 custom-tab",
                                    children=[
                                        dbc.Row(
                                            [
                                                dbc.Col(
                                                    [
                                                        dbc.Card(
                                                            [
                                                                dbc.CardBody(
                                                                    [
                                                                        dbc.Label(
                                                                            "Select chart to export as PNG"
                                                                        ),
                                                                        dcc.Dropdown(
                                                                            id="export-fig-selector",
                                                                            options=[
                                                                                {
                                                                                    "label": "Leave Taken (Bar)",
                                                                                    "value": "fig-leave-bar",
                                                                                },
                                                                                {
                                                                                    "label": "Leave vs Working (Line)",
                                                                                    "value": "fig-leave-vs-working-line",
                                                                                },
                                                                                {
                                                                                    "label": "Attendance % (Bar)",
                                                                                    "value": "fig-attendance-perc",
                                                                                },
                                                                                {
                                                                                    "label": "Attendance Trend MA (Line)",
                                                                                    "value": "fig-attendance-trend-ma",
                                                                                },
                                                                                {
                                                                                    "label": "MoM Change (Bar)",
                                                                                    "value": "fig-mom-change",
                                                                                },
                                                                                {
                                                                                    "label": "Cumulative Attendance (Line)",
                                                                                    "value": "fig-cumulative-attendance",
                                                                                },
                                                                                {
                                                                                    "label": "Employee Heatmap",
                                                                                    "value": "fig-heatmap-employee",
                                                                                },
                                                                                {
                                                                                    "label": "Multi-Employee Attendance",
                                                                                    "value": "fig-multi-employee-attendance",
                                                                                },
                                                                                {
                                                                                    "label": "Top Leave Months",
                                                                                    "value": "fig-top-leave-months",
                                                                                },
                                                                            ],
                                                                            value="fig-attendance-perc",
                                                                            clearable=False,
                                                                            className="mb-3",
                                                                        ),
                                                                        dbc.Button(
                                                                            "Download PNG",
                                                                            id="download-png-btn",
                                                                            color="primary",
                                                                            className="w-100 btn-custom",
                                                                        ),
                                                                        dcc.Download(
                                                                            id="download-png"
                                                                        ),
                                                                    ]
                                                                )
                                                            ]
                                                        )
                                                    ],
                                                    width=4,
                                                ),
                                                dbc.Col(
                                                    [
                                                        dbc.Alert(
                                                            [
                                                                html.H6(
                                                                    "Export Tip",
                                                                    className="alert-heading",
                                                                ),
                                                                html.P(
                                                                    "PNG export requires the 'kaleido' package.",
                                                                    className="mb-0",
                                                                ),
                                                                html.Code(
                                                                    "pip install kaleido",
                                                                    className="mt-2",
                                                                ),
                                                            ],
                                                            color="info",
                                                        )
                                                    ],
                                                    width=8,
                                                ),
                                            ]
                                        )
                                    ],
                                ),
                                dcc.Tab(
                                    label="Consolidated Report",
                                    value="tab-consolidated",
                                    className="py-2 custom-tab",
                                    children=[
                                        dbc.Row(
                                            [
                                                dbc.Col(
                                                    [
                                                        dbc.Card(
                                                            [
                                                                dbc.CardBody(
                                                                    [
                                                                        dbc.Row(
                                                                            [
                                                                                dbc.Col(
                                                                                    [
                                                                                        dbc.Label(
                                                                                            "Select Year:"
                                                                                        ),
                                                                                        dcc.Dropdown(
                                                                                            id="consolidated-year-dropdown",
                                                                                            options=[
                                                                                                {
                                                                                                    "label": y,
                                                                                                    "value": y,
                                                                                                }
                                                                                                for y in years
                                                                                            ],
                                                                                            value=years[
                                                                                                -1
                                                                                            ],
                                                                                            clearable=False,
                                                                                        ),
                                                                                    ],
                                                                                    width=2,
                                                                                ),
                                                                                dbc.Col(
                                                                                    [
                                                                                        dbc.Label(
                                                                                            "Select Month:"
                                                                                        ),
                                                                                        dcc.Dropdown(
                                                                                            id="consolidated-month-dropdown",
                                                                                            options=[
                                                                                                {
                                                                                                    "label": m,
                                                                                                    "value": m,
                                                                                                }
                                                                                                for m in month_order
                                                                                            ],
                                                                                            value=month_order[
                                                                                                0
                                                                                            ],
                                                                                            clearable=False,
                                                                                        ),
                                                                                    ],
                                                                                    width=2,
                                                                                ),
                                                                                dbc.Col(
                                                                                    [
                                                                                        dbc.Label(
                                                                                            "Calculation Base:"
                                                                                        ),
                                                                                        dcc.Dropdown(
                                                                                            id="consolidated-calculation-base-dropdown",
                                                                                            options=[
                                                                                                {
                                                                                                    "label": "Total Working Days",
                                                                                                    "value": "Total Working Days",
                                                                                                },
                                                                                                {
                                                                                                    "label": "Total Billable Days",
                                                                                                    "value": "Total Billable Days",
                                                                                                },
                                                                                            ],
                                                                                            value="Total Working Days",
                                                                                            clearable=False,
                                                                                        ),
                                                                                    ],
                                                                                    width=2,
                                                                                ),
                                                                                dbc.Col(
                                                                                    [
                                                                                        dbc.Label(
                                                                                            "Attendance Threshold (%)"
                                                                                        ),
                                                                                        dcc.Slider(
                                                                                            id="consolidated-threshold-slider",
                                                                                            min=50,
                                                                                            max=100,
                                                                                            step=1,
                                                                                            value=90,
                                                                                            marks={
                                                                                                x: str(
                                                                                                    x
                                                                                                )
                                                                                                for x in range(
                                                                                                    50,
                                                                                                    101,
                                                                                                    10,
                                                                                                )
                                                                                            },
                                                                                            tooltip={
                                                                                                "placement": "bottom",
                                                                                                "always_visible": True,
                                                                                            },
                                                                                        ),
                                                                                    ],
                                                                                    width=4,
                                                                                ),
                                                                                dbc.Col(
                                                                                    [
                                                                                        dbc.Button(
                                                                                            "Download CSV",
                                                                                            id="download-consolidated-csv-btn",
                                                                                            color="success",
                                                                                            className="mt-4 w-100 btn-custom",
                                                                                        ),
                                                                                        dcc.Download(
                                                                                            id="download-consolidated-csv"
                                                                                        ),
                                                                                    ],
                                                                                    width=2,
                                                                                ),
                                                                            ],
                                                                            align="center",
                                                                        )
                                                                    ]
                                                                )
                                                            ],
                                                            className="mb-3",
                                                        )
                                                    ],
                                                    width=12,
                                                )
                                            ]
                                        ),
                                        dbc.Row(
                                            [
                                                dbc.Col(
                                                    [
                                                        dbc.Card(
                                                            [
                                                                dbc.CardBody(
                                                                    [
                                                                        html.Div(
                                                                            id="consolidated-table-container",
                                                                            className="consolidated-table"
                                                                        )
                                                                    ]
                                                                )
                                                            ]
                                                        )
                                                    ],
                                                    width=12,
                                                )
                                            ]
                                        ),
                                    ],
                                ),
                            ],
                        )
                    ]
                )
            ],
            className="shadow",
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
    style={"backgroundColor": "#f8f9fa", "minHeight": "100vh", "padding": "20px"},
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
    Input("calculation-base-dropdown", "value"),
    Input("threshold-slider", "value"),
)
def update_all(selected_employee, selected_year, calculation_base, threshold):
    # Filter for employee/year
    df_emp = df[
        (df["Full Name"] == selected_employee) & (df["Year"] == selected_year)
    ].copy()
    df_emp = df_emp.sort_values("Month_Year").reset_index(drop=True)
    # Year-wide data (all employees) for comparisons
    df_year = df[df["Year"] == selected_year].copy()

    # Calculate attendance percentage based on selected calculation base
    if (
        calculation_base == "Total Billable Days"
        and "Total Billable Days" in df_emp.columns
    ):
        df_emp["Attendance %"] = 100 - (
            df_emp["Leave Taken Days"] / df_emp["Total Billable Days"] * 100
        )
        df_year["Attendance %"] = 100 - (
            df_year["Leave Taken Days"] / df_year["Total Billable Days"] * 100
        )
    else:
        # Default to Total Working Days
        df_emp["Attendance %"] = 100 - (
            df_emp["Leave Taken Days"] / df_emp["Total Working Days"] * 100
        )
        df_year["Attendance %"] = 100 - (
            df_year["Leave Taken Days"] / df_year["Total Working Days"] * 100
        )

    # --- KPIs ---
    total_leave = int(df_emp["Leave Taken Days"].sum()) if not df_emp.empty else 0
    avg_att = round(df_emp["Attendance %"].mean(), 2) if not df_emp.empty else 0.0
    min_att_month = (
        df_emp.loc[df_emp["Attendance %"].idxmin(), "Month"]
        if not df_emp.empty
        else "—"
    )
    alerts = (
        df_emp[df_emp["Attendance %"] < 80]["Month"].tolist()
        if not df_emp.empty
        else []
    )

    # Create KPI cards with appropriate colors
    kpi_cards = dbc.Row(
        [
            dbc.Col(kpi_card("Total Leave Days", total_leave, "danger"), width=3),
            dbc.Col(
                kpi_card("Average Attendance %", f"{avg_att}%", "primary"), width=3
            ),
            dbc.Col(
                kpi_card("Lowest Attendance Month", min_att_month, "warning"), width=3
            ),
            dbc.Col(
                kpi_card(
                    "Alerts (<80%)",
                    ", ".join(alerts) if alerts else "None",
                    "success" if not alerts else "danger",
                ),
                width=3,
            ),
        ],
        className="g-4",
    )

    # --- Leave Taken (Bar) ---
    fig_leave_bar = px.bar(
        df_emp,
        x="Month_Year",
        y="Leave Taken Days",
        text="Leave Taken Days",
        title=f"Leave Taken Days per Month — {selected_employee} ({selected_year})",
        labels={"Month_Year": "Month", "Leave Taken Days": "Days"},
        hover_data=["Dates of Leave", calculation_base],
        color_discrete_sequence=["#ff7f0e"],
    )
    fig_leave_bar.update_xaxes(
        ticktext=df_emp["Month_Abbr"], tickvals=df_emp["Month_Year"]
    )
    fig_leave_bar.update_layout(template="plotly_white")

    # --- Leave vs Working (Line) ---
    # Determine which column to use based on selection
    comparison_column = (
        calculation_base if calculation_base in df_emp.columns else "Total Working Days"
    )

    fig_line = px.line(
        df_emp,
        x="Month_Year",
        y=["Leave Taken Days", comparison_column],
        markers=True,
        title=f"Leave vs {comparison_column} — {selected_employee} ({selected_year})",
        labels={"value": "Days", "variable": "Metric", "Month_Year": "Month"},
        color_discrete_sequence=["#d62728", "#2ca02c"],
    )
    fig_line.update_xaxes(ticktext=df_emp["Month_Abbr"], tickvals=df_emp["Month_Year"])
    fig_line.update_layout(template="plotly_white")

    # --- Attendance % (Bar) with threshold coloring ---
    colors = ["#d62728" if v < threshold else "#2ca02c" for v in df_emp["Attendance %"]]
    fig_att_perc = px.bar(
        df_emp,
        x="Month_Year",
        y="Attendance %",
        text=df_emp["Attendance %"].round(1),
        title=f"Attendance % (Based on {calculation_base}) — {selected_employee} ({selected_year})  (Threshold: {threshold}%)",
        labels={"Month_Year": "Month", "Attendance %": "% Attendance"},
    )
    fig_att_perc.update_traces(marker_color=colors, showlegend=False)
    fig_att_perc.update_xaxes(
        ticktext=df_emp["Month_Abbr"], tickvals=df_emp["Month_Year"]
    )
    fig_att_perc.update_layout(template="plotly_white")

    # --- Attendance Trend (3-mo MA) ---
    df_emp["Attendance_MA"] = (
        df_emp["Attendance %"].rolling(window=3, min_periods=1).mean()
    )
    fig_trend = px.line(
        df_emp,
        x="Month_Year",
        y="Attendance_MA",
        markers=True,
        title=f"Attendance Trend — 3-Month Moving Average ({selected_employee}, {selected_year})",
        labels={"Month_Year": "Month", "Attendance_MA": "Attendance % (3-mo MA)"},
        color_discrete_sequence=["#9467bd"],
    )
    fig_trend.update_xaxes(ticktext=df_emp["Month_Abbr"], tickvals=df_emp["Month_Year"])
    fig_trend.update_layout(template="plotly_white")

    # --- Month-over-Month Change ---
    df_emp["MoM_Change"] = df_emp["Attendance %"].diff().fillna(0.0)
    mom_colors = ["#d62728" if v < 0 else "#2ca02c" for v in df_emp["MoM_Change"]]
    fig_mom = px.bar(
        df_emp,
        x="Month_Year",
        y="MoM_Change",
        text=df_emp["MoM_Change"].round(1),
        title=f"Month-over-Month Attendance Change — {selected_employee} ({selected_year})",
        labels={"Month_Year": "Month", "MoM_Change": "Δ %"},
    )
    fig_mom.update_traces(marker_color=mom_colors, showlegend=False)
    fig_mom.update_xaxes(ticktext=df_emp["Month_Abbr"], tickvals=df_emp["Month_Year"])
    fig_mom.update_layout(template="plotly_white")

    # --- Cumulative Attendance % (simple running mean) ---
    if not df_emp.empty:
        df_emp["Cum_Att"] = df_emp["Attendance %"].expanding().mean()
    else:
        df_emp["Cum_Att"] = []
    fig_cum = px.line(
        df_emp,
        x="Month_Year",
        y="Cum_Att",
        markers=True,
        title=f"Cumulative Attendance % — {selected_employee} ({selected_year})",
        labels={"Month_Year": "Month", "Cum_Att": "Cumulative %"},
        color_discrete_sequence=["#17becf"],
    )
    fig_cum.update_xaxes(ticktext=df_emp["Month_Abbr"], tickvals=df_emp["Month_Year"])
    fig_cum.update_layout(template="plotly_white")

    # --- Employee Heatmap (Leave Days by month) ---
    # single employee heatmap may be 1-row; still useful
    if not df_emp.empty:
        heat_df = df_emp.pivot(
            index="Full Name", columns="Month_Year", values="Leave Taken Days"
        )
        heat_df = heat_df.reindex(columns=df_emp["Month_Year"])  # keep chronological
        fig_heat = px.imshow(
            heat_df,
            text_auto=True,
            labels={"x": "Month", "y": "Employee", "color": "Leave Days"},
            title=f"Leave Heatmap — {selected_employee} ({selected_year})",
            color_continuous_scale="Reds",
        )
        fig_heat.update_xaxes(ticktext=df_emp["Month_Abbr"], tickvals=heat_df.columns)
        fig_heat.update_layout(template="plotly_white")
    else:
        fig_heat = go.Figure().update_layout(
            title="Leave Heatmap — No data", template="plotly_white"
        )

    # --- Multi-Employee Attendance % grouped ---
    # Calculate attendance for all employees in the selected year
    if (
        calculation_base == "Total Billable Days"
        and "Total Billable Days" in df_year.columns
    ):
        multi = df_year.groupby(["Full Name", "Month_Year"], as_index=False).agg(
            {"Leave Taken Days": "sum", "Total Billable Days": "sum"}
        )
        multi["Attendance %"] = 100 - (
            multi["Leave Taken Days"] / multi["Total Billable Days"] * 100
        )
    else:
        multi = df_year.groupby(["Full Name", "Month_Year"], as_index=False).agg(
            {"Leave Taken Days": "sum", "Total Working Days": "sum"}
        )
        multi["Attendance %"] = 100 - (
            multi["Leave Taken Days"] / multi["Total Working Days"] * 100
        )

    multi = multi.sort_values("Month_Year")
    fig_multi = px.bar(
        multi,
        x="Month_Year",
        y="Attendance %",
        color="Full Name",
        barmode="group",
        title=f"Attendance % by Employee — {selected_year}",
        labels={
            "Month_Year": "Month",
            "Attendance %": "% Attendance",
            "Full Name": "Employee",
        },
    )
    # Month labels
    month_labels = multi["Month_Year"].dt.strftime("%b %Y").unique().tolist()
    month_vals = multi["Month_Year"].drop_duplicates().tolist()
    fig_multi.update_xaxes(ticktext=month_labels, tickvals=month_vals)
    fig_multi.update_layout(template="plotly_white")

    # --- Top 5 Leave Months (for selected employee) ---
    top5 = df_emp.sort_values("Leave Taken Days", ascending=False).head(5)
    fig_top = px.bar(
        top5,
        x="Month_Year",
        y="Leave Taken Days",
        text="Leave Taken Days",
        title=f"Top 5 Months with Most Leave — {selected_employee} ({selected_year})",
        labels={"Month_Year": "Month", "Leave Taken Days": "Days"},
        color_discrete_sequence=["#e377c2"],
    )
    fig_top.update_xaxes(ticktext=top5["Month_Abbr"], tickvals=top5["Month_Year"])
    fig_top.update_layout(template="plotly_white")

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
        kpi_cards,
        fig_leave_bar,
        fig_line,
        fig_att_perc,
        fig_trend,
        fig_mom,
        fig_cum,
        fig_heat,
        fig_multi,
        fig_top,
        *store_data,
    )


# -------------------------
# 4) CSV download for filtered employee/year
# -------------------------
@dash_app.callback(
    Output("download-csv", "data"),
    Input("download-csv-btn", "n_clicks"),
    State("employee-dropdown", "value"),
    State("year-dropdown", "value"),
    State("calculation-base-dropdown", "value"),
    prevent_initial_call=True,
)
def download_csv(n, employee, year, calculation_base):
    dff = df[(df["Full Name"] == employee) & (df["Year"] == year)].copy()

    # Calculate attendance percentage based on selected calculation base
    if (
        calculation_base == "Total Billable Days"
        and "Total Billable Days" in dff.columns
    ):
        dff["Attendance %"] = 100 - (
            dff["Leave Taken Days"] / dff["Total Billable Days"] * 100
        )
    else:
        dff["Attendance %"] = 100 - (
            dff["Leave Taken Days"] / dff["Total Working Days"] * 100
        )

    if dff.empty:
        dff = pd.DataFrame(columns=df.columns)
    return dcc.send_data_frame(
        dff.to_csv, f"leave_data_{employee}_{year}.csv", index=False
    )


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
    prevent_initial_call=True,
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
    Input("consolidated-calculation-base-dropdown", "value"),
    Input("consolidated-threshold-slider", "value"),
)
def update_consolidated_table(
    selected_year, selected_month, calculation_base, threshold
):
    dff = df[(df["Year"] == selected_year) & (df["Month"] == selected_month)].copy()
    if dff.empty:
        return html.P("No data available for selected year/month.")

    # Calculate attendance percentage based on selected calculation base
    if (
        calculation_base == "Total Billable Days"
        and "Total Billable Days" in dff.columns
    ):
        dff["Attendance %"] = 100 - (
            dff["Leave Taken Days"] / dff["Total Billable Days"] * 100
        )
    else:
        dff["Attendance %"] = 100 - (
            dff["Leave Taken Days"] / dff["Total Working Days"] * 100
        )

    # Build table with Bootstrap styling
    table_header = [
        html.Thead(
            html.Tr(
                [
                    html.Th("Full Name"),
                    html.Th("Leave Taken Days"),
                    html.Th(calculation_base),
                    html.Th("Attendance %"),
                ],
                className="table-primary table-header",
            )
        )
    ]

    rows = []
    for _, row in dff.iterrows():
        attendance_color = (
            "text-danger" if row["Attendance %"] < threshold else "text-success"
        )
        rows.append(
            html.Tr(
                [
                    html.Td(row["Full Name"]),
                    html.Td(row["Leave Taken Days"]),
                    html.Td(
                        row[calculation_base] if calculation_base in row else "N/A"
                    ),
                    html.Td(
                        f"{row['Attendance %']:.1f}%",
                        className=f"font-weight-bold {attendance_color}",
                    ),
                ]
            )
        )

    table_body = [html.Tbody(rows)]

    return dbc.Table(
        table_header + table_body,
        striped=True,
        bordered=True,
        hover=True,
        responsive=True,
    )


# -------------------------
# CSV download for consolidated report
# -------------------------
@dash_app.callback(
    Output("download-consolidated-csv", "data"),
    Input("download-consolidated-csv-btn", "n_clicks"),
    State("consolidated-year-dropdown", "value"),
    State("consolidated-month-dropdown", "value"),
    State("consolidated-calculation-base-dropdown", "value"),
    prevent_initial_call=True,
)
def download_consolidated_csv(n_clicks, year, month, calculation_base):
    dff = df[(df["Year"] == year) & (df["Month"] == month)].copy()

    # Calculate attendance percentage based on selected calculation base
    if (
        calculation_base == "Total Billable Days"
        and "Total Billable Days" in dff.columns
    ):
        dff["Attendance %"] = 100 - (
            dff["Leave Taken Days"] / dff["Total Billable Days"] * 100
        )
    else:
        dff["Attendance %"] = 100 - (
            dff["Leave Taken Days"] / dff["Total Working Days"] * 100
        )

    if dff.empty:
        dff = pd.DataFrame(
            columns=["Full Name", "Leave Taken Days", calculation_base, "Attendance %"]
        )
    return dcc.send_data_frame(
        dff.to_csv, f"consolidated_attendance_{month}_{year}.csv", index=False
    )


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
        msg.setText(
            f"Your Dash app is running!\n\nOpen this link in your browser:\n{url}"
        )
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
