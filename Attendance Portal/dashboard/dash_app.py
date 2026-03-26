# ======================
# dashboard/dash_app.py — Dash analytics dashboard (singleton, lazy imports)
# ======================
#
# PERF: dash, plotly, and QWebEngineView are imported LAZILY — only when the
#       user first clicks "Analyze". This saves 3-5 seconds on app startup.
#
# PERF: Dash server is a singleton — started once and reused. Pushing new data
#       updates the in-memory reference without restarting the thread.
# ======================

import calendar
import threading

import pandas as pd

# ── Singleton state ──────────────────────────────────────────────────────────
_dash_thread = None
_dash_running = False
_current_df = None          # updated each time show_dashboard() is called
DASH_PORT = 8050
DASH_HOST = "127.0.0.1"
# ─────────────────────────────────────────────────────────────────────────────


def show_dashboard(output_list: list) -> None:
    """
    Entry point called from the UI.
    Builds (or updates) the Dash app, starts the server thread if needed,
    then opens a Qt WebEngine dialog pointing at localhost.
    """
    global _dash_thread, _dash_running, _current_df

    # --- Lazy imports (not loaded at app startup) ---
    import dash
    import dash_bootstrap_components as dbc
    from dash import html, dcc, Input, Output, State, dash_table
    import plotly.express as px
    import plotly.graph_objects as go
    from PyQt6.QtWidgets import QDialog, QVBoxLayout, QApplication
    from PyQt6.QtCore import QUrl
    from PyQt6.QtWebEngineWidgets import QWebEngineView

    # ── Prepare DataFrame ─────────────────────────────────────────────────
    df = pd.DataFrame(output_list)
    df["Year"] = df["Year"].astype(int)
    df["Month_Year"] = pd.to_datetime(df["Month"] + " " + df["Year"].astype(str))
    df = df.sort_values(["Full Name", "Month_Year"]).reset_index(drop=True)

    month_order = list(calendar.month_name)[1:]
    df["Month"] = pd.Categorical(df["Month"], categories=month_order, ordered=True)
    df["Month_Abbr"] = df["Month_Year"].dt.strftime("%b %Y")

    _current_df = df
    years = sorted(df["Year"].unique())
    employees = sorted(df["Full Name"].unique())

    # ── Build Dash app ────────────────────────────────────────────────────
    dash_app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
    dash_app.title = "Leave & Attendance Dashboard"

    def kpi_card(title, value, color="primary"):
        return dbc.Card(
            dbc.CardBody([
                html.H6(title, className="card-subtitle mb-2 text-muted"),
                html.H4(f"{value}", className=f"card-title text-{color} font-weight-bold"),
            ], className="text-center"),
            className="mb-3 shadow-sm",
        )

    dash_app.layout = dbc.Container(fluid=True, children=[
        dbc.Row([dbc.Col([
            html.H1("Employee Leave & Attendance Dashboard",
                    className="text-center my-4 text-primary"),
            html.P("Comprehensive analysis of employee leave patterns and attendance trends",
                   className="text-center text-muted mb-4"),
        ])]),

        # ── Filters ──────────────────────────────────────────────────────
        dbc.Card([dbc.CardBody([dbc.Row([
            dbc.Col([
                dbc.Label("Employee"),
                dcc.Dropdown(id="employee-dropdown",
                             options=[{"label": n, "value": n} for n in employees],
                             value=employees[0], clearable=False, className="mb-2"),
            ], width=3),
            dbc.Col([
                dbc.Label("Year"),
                dcc.Dropdown(id="year-dropdown",
                             options=[{"label": int(y), "value": int(y)} for y in years],
                             value=years[-1], clearable=False, className="mb-2"),
            ], width=2),
            dbc.Col([
                dbc.Label("Calculation Base"),
                dcc.Dropdown(id="calculation-base-dropdown",
                             options=[
                                 {"label": "Total Working Days", "value": "Total Working Days"},
                                 {"label": "Total Billable Days", "value": "Total Billable Days"},
                             ],
                             value="Total Working Days", clearable=False, className="mb-2"),
            ], width=2),
            dbc.Col([
                dbc.Label("Attendance Threshold (%)"),
                dcc.Slider(id="threshold-slider", min=50, max=100, step=1, value=90,
                           marks={x: str(x) for x in range(50, 101, 10)},
                           tooltip={"placement": "bottom", "always_visible": True}),
            ], width=3),
            dbc.Col([
                dbc.Button("Download Filtered CSV", id="download-csv-btn",
                           color="success", className="mt-4 w-100"),
                dcc.Download(id="download-csv"),
            ], width=2),
        ], align="center")])], className="mb-4 shadow"),

        # ── KPI row ───────────────────────────────────────────────────────
        dbc.Row([dbc.Col(html.Div(id="kpi-row"), width=12)], className="mb-4"),

        # ── Tabbed charts ─────────────────────────────────────────────────
        dbc.Card([dbc.CardBody([dcc.Tabs(id="tabs", value="tab-overview", className="mb-3", children=[
            dcc.Tab(label="Overview", value="tab-overview", children=[dbc.Row([
                dbc.Col(dcc.Graph(id="fig-leave-bar"), width=12, className="mb-3"),
                dbc.Col(dcc.Graph(id="fig-leave-vs-working-line"), width=12, className="mb-3"),
                dbc.Col(dcc.Graph(id="fig-attendance-perc"), width=12),
            ])]),
            dcc.Tab(label="Trends", value="tab-trends", children=[dbc.Row([
                dbc.Col(dcc.Graph(id="fig-attendance-trend-ma"), width=12, className="mb-3"),
                dbc.Col(dcc.Graph(id="fig-mom-change"), width=12, className="mb-3"),
                dbc.Col(dcc.Graph(id="fig-cumulative-attendance"), width=12),
            ])]),
            dcc.Tab(label="Comparisons", value="tab-compare", children=[dbc.Row([
                dbc.Col(dcc.Graph(id="fig-heatmap-employee"), width=12, className="mb-3"),
                dbc.Col(dcc.Graph(id="fig-multi-employee-attendance"), width=12, className="mb-3"),
                dbc.Col(dcc.Graph(id="fig-top-leave-months"), width=12),
            ])]),
            dcc.Tab(label="Consolidated Report", value="tab-consolidated", children=[
                dbc.Row([dbc.Col([dbc.Card([dbc.CardBody([dbc.Row([
                    dbc.Col([dbc.Label("Select Year:"),
                             dcc.Dropdown(id="consolidated-year-dropdown",
                                          options=[{"label": y, "value": y} for y in years],
                                          value=years[-1], clearable=False)], width=2),
                    dbc.Col([dbc.Label("Select Month:"),
                             dcc.Dropdown(id="consolidated-month-dropdown",
                                          options=[{"label": m, "value": m} for m in month_order],
                                          value=month_order[0], clearable=False)], width=2),
                    dbc.Col([dbc.Label("Calculation Base:"),
                             dcc.Dropdown(id="consolidated-calculation-base-dropdown",
                                          options=[
                                              {"label": "Total Working Days", "value": "Total Working Days"},
                                              {"label": "Total Billable Days", "value": "Total Billable Days"},
                                          ], value="Total Working Days", clearable=False)], width=2),
                    dbc.Col([dbc.Label("Attendance Threshold (%)"),
                             dcc.Slider(id="consolidated-threshold-slider", min=50, max=100,
                                        step=1, value=90, marks={x: str(x) for x in range(50, 101, 10)},
                                        tooltip={"placement": "bottom", "always_visible": True})], width=4),
                    dbc.Col([dbc.Button("Download CSV", id="download-consolidated-csv-btn",
                                        color="success", className="mt-4 w-100"),
                             dcc.Download(id="download-consolidated-csv")], width=2),
                ], align="center")])])], className="mb-3")], width=12)]),
                dbc.Row([dbc.Col([dbc.Card([dbc.CardBody([
                    html.Div(id="consolidated-table-container")])
                ])], width=12)]),
            ]),
        ])])], className="shadow"),

    # ── Hidden stores for PNG export (appended after layout) ─────────────
    _store_ids = [
        "fig-leave-bar", "fig-leave-vs-working-line", "fig-attendance-perc",
        "fig-attendance-trend-ma", "fig-mom-change", "fig-cumulative-attendance",
        "fig-heatmap-employee", "fig-multi-employee-attendance", "fig-top-leave-months",
    ]
    dash_app.layout.children.extend([dcc.Store(id=f"store-{sid}") for sid in _store_ids])

    # ── Main callback ────────────────────────────────────────────────────
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
        Input("employee-dropdown", "value"),
        Input("year-dropdown", "value"),
        Input("calculation-base-dropdown", "value"),
        Input("threshold-slider", "value"),
    )
    def update_all(selected_employee, selected_year, calculation_base, threshold):
        df_emp = df[(df["Full Name"] == selected_employee) & (df["Year"] == selected_year)].copy()
        df_emp = df_emp.sort_values("Month_Year").reset_index(drop=True)
        df_year = df[df["Year"] == selected_year].copy()

        base_col = (calculation_base if calculation_base in df_emp.columns else "Total Working Days")
        df_emp["Attendance %"] = 100 - (df_emp["Leave Taken Days"] / df_emp[base_col] * 100)
        df_year["Attendance %"] = 100 - (df_year["Leave Taken Days"] / df_year[base_col] * 100)

        total_leave = int(df_emp["Leave Taken Days"].sum()) if not df_emp.empty else 0
        avg_att = round(df_emp["Attendance %"].mean(), 2) if not df_emp.empty else 0.0
        min_att_month = (df_emp.loc[df_emp["Attendance %"].idxmin(), "Month"] if not df_emp.empty else "—")
        alerts = df_emp[df_emp["Attendance %"] < 80]["Month"].tolist() if not df_emp.empty else []

        kpi_cards = dbc.Row([
            dbc.Col(kpi_card("Total Leave Days", total_leave, "danger"), width=3),
            dbc.Col(kpi_card("Average Attendance %", f"{avg_att}%", "primary"), width=3),
            dbc.Col(kpi_card("Lowest Attendance Month", min_att_month, "warning"), width=3),
            dbc.Col(kpi_card("Alerts (<80%)", ", ".join(alerts) if alerts else "None",
                             "success" if not alerts else "danger"), width=3),
        ], className="g-4")

        # Leave bar
        fig_leave_bar = px.bar(df_emp, x="Month_Year", y="Leave Taken Days", text="Leave Taken Days",
                               title=f"Leave Taken Days — {selected_employee} ({selected_year})",
                               color_discrete_sequence=["#ff7f0e"])
        fig_leave_bar.update_xaxes(ticktext=df_emp["Month_Abbr"], tickvals=df_emp["Month_Year"])
        fig_leave_bar.update_layout(template="plotly_white")

        # Leave vs working line
        fig_line = px.line(df_emp, x="Month_Year", y=["Leave Taken Days", base_col], markers=True,
                           title=f"Leave vs {base_col} — {selected_employee} ({selected_year})",
                           color_discrete_sequence=["#d62728", "#2ca02c"])
        fig_line.update_xaxes(ticktext=df_emp["Month_Abbr"], tickvals=df_emp["Month_Year"])
        fig_line.update_layout(template="plotly_white")

        # Attendance % bar
        colors = ["#d62728" if v < threshold else "#2ca02c" for v in df_emp["Attendance %"]]
        fig_att_perc = px.bar(df_emp, x="Month_Year", y="Attendance %",
                              text=df_emp["Attendance %"].round(1),
                              title=f"Attendance % — {selected_employee} ({selected_year}) [Threshold: {threshold}%]")
        fig_att_perc.update_traces(marker_color=colors)
        fig_att_perc.update_xaxes(ticktext=df_emp["Month_Abbr"], tickvals=df_emp["Month_Year"])
        fig_att_perc.update_layout(template="plotly_white")

        # 3-month MA
        df_emp["Attendance_MA"] = df_emp["Attendance %"].rolling(3, min_periods=1).mean()
        fig_trend = px.line(df_emp, x="Month_Year", y="Attendance_MA", markers=True,
                            title=f"3-Month MA Attendance — {selected_employee} ({selected_year})",
                            color_discrete_sequence=["#9467bd"])
        fig_trend.update_xaxes(ticktext=df_emp["Month_Abbr"], tickvals=df_emp["Month_Year"])
        fig_trend.update_layout(template="plotly_white")

        # MoM change
        df_emp["MoM_Change"] = df_emp["Attendance %"].diff().fillna(0.0)
        mom_colors = ["#d62728" if v < 0 else "#2ca02c" for v in df_emp["MoM_Change"]]
        fig_mom = px.bar(df_emp, x="Month_Year", y="MoM_Change", text=df_emp["MoM_Change"].round(1),
                         title=f"Month-over-Month Attendance Change — {selected_employee}")
        fig_mom.update_traces(marker_color=mom_colors)
        fig_mom.update_xaxes(ticktext=df_emp["Month_Abbr"], tickvals=df_emp["Month_Year"])
        fig_mom.update_layout(template="plotly_white")

        # Cumulative
        df_emp["Cum_Att"] = df_emp["Attendance %"].expanding().mean()
        fig_cum = px.line(df_emp, x="Month_Year", y="Cum_Att", markers=True,
                          title=f"Cumulative Attendance % — {selected_employee}",
                          color_discrete_sequence=["#17becf"])
        fig_cum.update_xaxes(ticktext=df_emp["Month_Abbr"], tickvals=df_emp["Month_Year"])
        fig_cum.update_layout(template="plotly_white")

        # Heatmap
        if not df_emp.empty:
            heat_df = df_emp.pivot(index="Full Name", columns="Month_Year", values="Leave Taken Days")
            fig_heat = px.imshow(heat_df, text_auto=True,
                                 title=f"Leave Heatmap — {selected_employee}", color_continuous_scale="Reds")
            fig_heat.update_xaxes(ticktext=df_emp["Month_Abbr"], tickvals=heat_df.columns)
            fig_heat.update_layout(template="plotly_white")
        else:
            fig_heat = go.Figure().update_layout(title="Leave Heatmap — No data", template="plotly_white")

        # Multi-employee
        multi = df_year.groupby(["Full Name", "Month_Year"], as_index=False).agg(
            {"Leave Taken Days": "sum", base_col: "sum"})
        multi["Attendance %"] = 100 - (multi["Leave Taken Days"] / multi[base_col] * 100)
        multi = multi.sort_values("Month_Year")
        fig_multi = px.bar(multi, x="Month_Year", y="Attendance %", color="Full Name", barmode="group",
                           title=f"Attendance % by Employee — {selected_year}")
        fig_multi.update_layout(template="plotly_white")

        # Top 5
        top5 = df_emp.sort_values("Leave Taken Days", ascending=False).head(5)
        fig_top = px.bar(top5, x="Month_Year", y="Leave Taken Days", text="Leave Taken Days",
                         title=f"Top 5 Leave Months — {selected_employee}",
                         color_discrete_sequence=["#e377c2"])
        fig_top.update_xaxes(ticktext=top5["Month_Abbr"], tickvals=top5["Month_Year"])
        fig_top.update_layout(template="plotly_white")

        return (kpi_cards, fig_leave_bar, fig_line, fig_att_perc,
                fig_trend, fig_mom, fig_cum, fig_heat, fig_multi, fig_top)

    # ── CSV download ─────────────────────────────────────────────────────
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
        base_col = calculation_base if calculation_base in dff.columns else "Total Working Days"
        dff["Attendance %"] = 100 - (dff["Leave Taken Days"] / dff[base_col] * 100)
        return dcc.send_data_frame(dff.to_csv, f"leave_{employee}_{year}.csv", index=False)

    # ── Consolidated table ───────────────────────────────────────────────
    @dash_app.callback(
        Output("consolidated-table-container", "children"),
        Input("consolidated-year-dropdown", "value"),
        Input("consolidated-month-dropdown", "value"),
        Input("consolidated-calculation-base-dropdown", "value"),
        Input("consolidated-threshold-slider", "value"),
    )
    def update_consolidated_table(selected_year, selected_month, calculation_base, threshold):
        dff = df[(df["Year"] == selected_year) & (df["Month"] == selected_month)].copy()
        if dff.empty:
            return html.P("No data available for selected year/month.")
        base_col = calculation_base if calculation_base in dff.columns else "Total Working Days"
        dff["Attendance %"] = 100 - (dff["Leave Taken Days"] / dff[base_col] * 100)

        table_header = [html.Thead(html.Tr([
            html.Th("Full Name"), html.Th("Leave Taken Days"),
            html.Th(calculation_base), html.Th("Attendance %"),
        ], className="table-primary"))]

        rows = []
        for _, row in dff.iterrows():
            color = "text-danger" if row["Attendance %"] < threshold else "text-success"
            rows.append(html.Tr([
                html.Td(row["Full Name"]),
                html.Td(row["Leave Taken Days"]),
                html.Td(row[calculation_base] if calculation_base in row else "N/A"),
                html.Td(f"{row['Attendance %']:.1f}%", className=f"font-weight-bold {color}"),
            ]))
        return dbc.Table(table_header + [html.Tbody(rows)],
                         striped=True, bordered=True, hover=True, responsive=True)

    # ── Consolidated CSV download ─────────────────────────────────────────
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
        base_col = calculation_base if calculation_base in dff.columns else "Total Working Days"
        dff["Attendance %"] = 100 - (dff["Leave Taken Days"] / dff[base_col] * 100)
        return dcc.send_data_frame(
            dff.to_csv, f"consolidated_{month}_{year}.csv", index=False
        )

    # ── Start Dash server (singleton) ────────────────────────────────────
    global _dash_thread, _dash_running

    if not _dash_running:
        def run_dash():
            global _dash_running
            _dash_running = True
            dash_app.run(port=DASH_PORT, host=DASH_HOST, debug=False, use_reloader=False)

        _dash_thread = threading.Thread(target=run_dash, daemon=True)
        _dash_thread.start()

    # ── Open Qt WebEngine dialog ─────────────────────────────────────────
    dialog = QDialog()
    dialog.setWindowTitle("Leave & Attendance Dashboard")
    dialog.showMaximized()

    layout = QVBoxLayout(dialog)
    web_view = QWebEngineView()
    web_view.setUrl(QUrl(f"http://{DASH_HOST}:{DASH_PORT}"))
    layout.addWidget(web_view)
    dialog.setLayout(layout)
    dialog.exec()
