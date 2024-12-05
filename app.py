# Import necessary libraries
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go  # Import graph_objects for the bar chart

# Clear cache
st.cache_data.clear()
st.cache_resource.clear()

# Enable wide mode
st.set_page_config(page_title="Dynamic Sunburst Diagram of 2024 Grants", layout="wide")

# Base Salesforce URL
SALESFORCE_BASE_URL = "https://hewlett.lightning.force.com/lightning/r/Request__c/"

# Streamlit app title
st.title("Dynamic Sunburst Diagram of 2024 Grants")

# Path to the default data file (ensure this file exists in your project directory)
DEFAULT_FILE_PATH = "default_grants_data.xlsx"

# Initialize session state for filters
if "selected_program" not in st.session_state:
	st.session_state["selected_program"] = "All"
if "selected_strategy" not in st.session_state:
	st.session_state["selected_strategy"] = "All"

# Define a function to reset filters
def reset_filters():
	st.session_state["selected_program"] = "All"
	st.session_state["selected_strategy"] = "All"

# Load default data if available
if DEFAULT_FILE_PATH:
	try:
		default_df = pd.read_excel(DEFAULT_FILE_PATH, sheet_name="2024 Grants GMS Export")

		# Define hierarchy and value columns
		hierarchy_columns = ["Top Level Primary Program", "Primary Strategy", "Organization: Organization Name", "Project Title", "Request: ID"]
		value_column = "Amount"

		# Filter relevant columns
		sunburst_data = default_df[hierarchy_columns + [value_column]].copy()

		# Clean data: Remove rows with missing or zero values in the hierarchy or Amount column
		sunburst_data.dropna(subset=hierarchy_columns + [value_column], inplace=True)
		sunburst_data = sunburst_data[sunburst_data[value_column] > 0]

		# Check if data is non-empty
		if sunburst_data.empty:
			st.warning("No default data available to display. Please upload a dataset.")
		else:
			# Sidebar filtering
			st.sidebar.header("Filter Options")

			selected_program = st.sidebar.selectbox(
				"Select Top Level Program:",
				options=["All"] + list(sunburst_data["Top Level Primary Program"].unique()),
				key="selected_program"
			)

			if selected_program != "All":
				strategies = sunburst_data[sunburst_data["Top Level Primary Program"] == selected_program]["Primary Strategy"].unique()
			else:
				strategies = sunburst_data["Primary Strategy"].unique()

			selected_strategy = st.sidebar.selectbox(
				"Select Primary Strategy:",
				options=["All"] + list(strategies),
				key="selected_strategy"
			)

			st.sidebar.button("Reset Filters", on_click=reset_filters)

			# Apply filters and update metrics dynamically with a loading spinner
			with st.spinner("Updating data..."):
				filtered_data = sunburst_data.copy()

				# Apply program filter
				if selected_program != "All":
					filtered_data = filtered_data[filtered_data["Top Level Primary Program"] == selected_program]

				# Apply strategy filter
				if selected_strategy != "All":
					filtered_data = filtered_data[filtered_data["Primary Strategy"] == selected_strategy]

				# Convert "Amount" column to numeric
				filtered_data["Amount"] = pd.to_numeric(filtered_data["Amount"], errors="coerce")

				# Calculate metrics
				total_records = len(filtered_data)
				total_amount = filtered_data["Amount"].sum()

				# Median and mean calculations
				median_all = sunburst_data["Amount"].median()  # Median for all data
				mean_all = sunburst_data["Amount"].mean()  # Mean for all data

				if not filtered_data.empty:
					median_filtered = filtered_data["Amount"].median()  # Median for filtered data
					mean_filtered = filtered_data["Amount"].mean()  # Mean for filtered data
				else:
					median_filtered = None
					mean_filtered = None

				# Create Salesforce link column
				filtered_data["Salesforce Link"] = filtered_data.apply(
					lambda row: f'<a href="{SALESFORCE_BASE_URL}{row["Request: ID"]}/view" target="_blank">{row["Project Title"]}</a>',
					axis=1
				)

				# Drop the raw Salesforce ID column
				filtered_data.drop(columns=["Request: ID"], inplace=True)

				# Create Sunburst Diagram
				fig = px.sunburst(
					filtered_data,
					path=["Top Level Primary Program", "Primary Strategy", "Organization: Organization Name", "Project Title"],
					values=value_column,
					title="Grants Distribution Hierarchy (2024)",
					color=value_column,
					color_continuous_scale="Viridis",
					width=1000,
					height=800
				)

			# Display the Sunburst Diagram
			st.plotly_chart(fig, use_container_width=True)

			# Add widgets to display metrics
			st.markdown("---")  # Divider

			# First row: Total Records and Total Amount
			row1_col1, row1_col2 = st.columns(2)
			with row1_col1:
				st.metric("Total Records", total_records)
			with row1_col2:
				st.metric("Total Amount", f"${total_amount:,.2f}")
			
			st.markdown("---")  # Divider
			
			# Second row: Median (All Grants), Median (Filtered)
			row2_col1, row2_col2 = st.columns(2)
			with row2_col1:
				st.metric("Median (All Grants)", f"${median_all:,.2f}")
			with row2_col2:
				if median_filtered is not None:
					st.metric("Median (Filtered)", f"${median_filtered:,.2f}")
				else:
					st.metric("Median (Filtered)", "No Data")
			
			st.markdown("---")  # Divider
			
			# Third row: Mean (All Grants) and Mean (Filtered)
			row3_col1, row3_col2 = st.columns(2)
			with row3_col1:
				st.metric("Mean (All Grants)", f"${mean_all:,.2f}")
			with row3_col2:
				if mean_filtered is not None:
					st.metric("Mean (Filtered)", f"${mean_filtered:,.2f}")
				else:
					st.metric("Mean (Filtered)", "No Data")

			# Reorder columns for the table
			table_columns = ["Top Level Primary Program", "Primary Strategy", "Organization: Organization Name", "Salesforce Link", "Amount"]
			filtered_data = filtered_data[table_columns]

			# Format the Amount column as currency
			filtered_data["Amount"] = filtered_data["Amount"].apply(lambda x: f"${x:,.2f}")

			# Display the filtered table
			st.subheader("Filtered Data Table")
			
			# Render the table with clickable links
			st.markdown(
				filtered_data.to_html(escape=False, index=False),
				unsafe_allow_html=True
			)
			
			# Allow users to download the filtered data as a CSV file
			csv = filtered_data.to_csv(index=False)  # Convert DataFrame to CSV
			st.download_button(
				label="Download Filtered Data as CSV",
				data=csv,
				file_name="filtered_data.csv",
				mime="text/csv",
			)

			# Render the table with clickable links
			st.markdown(
				filtered_data.to_html(escape=False, index=False),
				unsafe_allow_html=True
			)
	except Exception as e:
		st.error(f"Error loading default data: {e}")

# File uploader for custom user uploads
uploaded_file = st.file_uploader("Upload the Grants Excel File", type=["xlsx"])

if uploaded_file is not None:
	st.info("Custom data handling not fully implemented here. Follow similar steps as above for uploaded data.")