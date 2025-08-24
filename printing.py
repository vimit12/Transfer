import pandas as pd
import dash
import calendar
df = pd.read_csv("sample_output.csv")
# df.columns.tolist()[1:]
# df.loc[1]
# Find column that has "521" in its name
col_521 = [col for col in df.columns if "521" in col][0]

# Group by that column
grouped = df.groupby(col_521)

# Example: get group sizes
# print(grouped.size())

for group_name, group_df in grouped:
    print("Group:", group_name)

    # Convert dates
    group_df['Start Date'] = pd.to_datetime(group_df['Start Date'])
    group_df['End Date'] = pd.to_datetime(group_df['End Date'])

    # Sort by start date
    group_df = group_df.sort_values(by='Start Date')

    # Dictionary to store leave dates per (year, month)
    month_year_leave_dates = {}

    for _, row in group_df.iterrows():
        start = row['Start Date']
        end = row['End Date']
        all_dates = pd.date_range(start, end)
        workdays = all_dates[~all_dates.weekday.isin([5, 6])]  # Exclude weekends

        for d in workdays:
            key = (d.year, d.month)
            if key in month_year_leave_dates:
                month_year_leave_dates[key].add(d)
            else:
                month_year_leave_dates[key] = {d}

    # Print summary per (year, month)
    for (year, month), dates in sorted(month_year_leave_dates.items()):
        dates_sorted = sorted(list(dates))
        dates_str = [d.strftime("%A, %B %d, %Y") for d in dates_sorted]
        month_name = dates_sorted[0].strftime("%B")

        # Calculate total working days in the month
        num_days_in_month = calendar.monthrange(year, month)[1]
        all_days_in_month = pd.date_range(start=f"{year}-{month:02d}-01", end=f"{year}-{month:02d}-{num_days_in_month}")
        total_working_days = len(all_days_in_month[~all_days_in_month.weekday.isin([5, 6])])

        print(
            f"Group Name: {group_name}, Month: {month_name}, Year: {year}, Leave Taken Days: {len(dates_sorted)}, Dates of Leave: {dates_str}, Total Working Days: {total_working_days}")
        break