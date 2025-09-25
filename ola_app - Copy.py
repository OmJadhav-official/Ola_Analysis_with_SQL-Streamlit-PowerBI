import streamlit as st
import pandas as pd
import mysql.connector
from mysql.connector import Error
import matplotlib.pyplot as plt
import seaborn as sns
from contextlib import contextmanager

# --- Page Config ---
st.set_page_config(page_title="Ola Rides Insights", layout="wide")
st.title("🚗 Ola Rides Insights Dashboard")
st.caption("Powered by MySQL + Streamlit")

# --- DB Connection ---
@contextmanager
def get_connection():
    conn = None
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="PASTE YOUR USERNAME HERE",
            password="PASTE YOUR PSWD HERE",
            database="ola",
            autocommit=True
        )
        yield conn
    finally:
        if conn and conn.is_connected():
            conn.close()

def run_query(sql):
    with get_connection() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(sql)
        rows = cursor.fetchall()
        df = pd.DataFrame(rows)
    return df

# --- Query Dictionary ---
QUERIES = {
    "1. Retrieve all successful bookings": """
        SELECT * FROM rides
        WHERE booking_status = 'Success'
        ORDER BY ride_datetime DESC
        LIMIT 1000;
    """,
    "2. Average ride distance per vehicle type": """
        SELECT vehicle_type, ROUND(AVG(ride_distance), 2) AS avg_ride_distance
        FROM rides
        GROUP BY vehicle_type
        ORDER BY avg_ride_distance DESC;
    """,
    "3. Daily success KPIs (from view if present)": """
        SELECT * FROM v_daily_trends
        ORDER BY ride_date DESC
        LIMIT 365;
    """,
    "4. Top 5 customers by number of rides": """
        SELECT customer_id, COUNT(*) AS total_rides
        FROM rides
        GROUP BY customer_id
        ORDER BY total_rides DESC
        LIMIT 5;
    """,
    "5. Driver cancel due to personal & car-related issues": """
        SELECT COUNT(*) AS driver_cancel_personal_car_issues
        FROM rides
        WHERE booking_status = 'Cancelled by Driver'
          AND reason_cancel_driver = 'Personal & Car related issues';
    """,
    "6. Max and Min driver ratings for Prime Sedan": """
        SELECT MAX(driver_ratings) AS max_driver_rating,
               MIN(driver_ratings) AS min_driver_rating
        FROM rides
        WHERE vehicle_type = 'Prime Sedan';
    """,
    "7. Rides paid via UPI": """
        SELECT * FROM rides
        WHERE payment_method = 'UPI'
        ORDER BY ride_datetime DESC
        LIMIT 1000;
    """,
    "8. Average customer rating per vehicle type": """
        SELECT vehicle_type, ROUND(AVG(customer_rating), 2) AS avg_customer_rating
        FROM rides
        GROUP BY vehicle_type
        ORDER BY avg_customer_rating DESC;
    """,
    "9. Total booking value of successful rides": """
        SELECT ROUND(SUM(booking_value), 2) AS total_success_revenue
        FROM rides
        WHERE booking_status = 'Success';
    """,
    "10. Incomplete rides with reason": """
        SELECT booking_id, customer_id, vehicle_type,
               pickup_location, drop_location, incomplete_reason
        FROM rides
        WHERE booking_status = 'Incomplete'
        ORDER BY booking_id DESC
        LIMIT 1000;
    """
}

# --- Sidebar Controls ---
st.sidebar.header("Controls")
selected_query_name = st.sidebar.selectbox("Select an insight", list(QUERIES.keys()), index=0)

# Optional row limit slider for large queries
if selected_query_name in [
    "1. Retrieve all successful bookings",
    "7. Rides paid via UPI",
    "10. Incomplete rides with reason"
]:
    limit_val = st.slider("Max rows to display", 100, 5000, 1000, step=100)
    sql_to_run = QUERIES[selected_query_name].replace("LIMIT 1000", f"LIMIT {limit_val}")
else:
    sql_to_run = QUERIES[selected_query_name]

# --- Run Query and Display ---
st.subheader(selected_query_name)

try:
    df = run_query(sql_to_run)
    if df.empty:
        st.info("No rows returned.")
    else:
        st.write(f"Rows: {df.shape[0]} | Columns: {df.shape[1]}")

        # --- Visualizations ---
        if selected_query_name == "2. Average ride distance per vehicle type":
            fig, ax = plt.subplots()
            sns.barplot(data=df, x="vehicle_type", y="avg_ride_distance", ax=ax, palette="Blues_d")
            ax.set_title("Average Ride Distance by Vehicle Type")
            st.pyplot(fig)

        elif selected_query_name == "8. Average customer rating per vehicle type":
            fig, ax = plt.subplots()
            sns.barplot(data=df, x="vehicle_type", y="avg_customer_rating", ax=ax, palette="Greens_d")
            ax.set_title("Average Customer Rating by Vehicle Type")
            st.pyplot(fig)

        elif selected_query_name == "4. Top 5 customers by number of rides":
            fig, ax = plt.subplots()
            sns.barplot(data=df, x="customer_id", y="total_rides", ax=ax, palette="Purples_d")
            ax.set_title("Top 5 Customers by Ride Count")
            st.pyplot(fig)

        elif selected_query_name == "3. Daily success KPIs (from view if present)":
            if "ride_date" in df.columns and "success_rides" in df.columns:
                df_sorted = df.sort_values("ride_date")
                fig, ax = plt.subplots()
                ax.plot(df_sorted["ride_date"], df_sorted["success_rides"], marker="o")
                ax.set_title("Daily Successful Rides")
                st.pyplot(fig)

        elif selected_query_name == "9. Total booking value of successful rides":
            st.metric("Total Success Revenue", str(df.iloc[0, 0]))

        elif selected_query_name == "6. Max and Min driver ratings for Prime Sedan":
            col1, col2 = st.columns(2)
            col1.metric("Max Driver Rating", str(df["max_driver_rating"].iloc[0]))
            col2.metric("Min Driver Rating", str(df["min_driver_rating"].iloc[0]))

        elif selected_query_name == "5. Driver cancel due to personal & car-related issues":
            st.metric("Driver Cancels (Personal & Car issues)", str(df.iloc[0, 0]))

        # --- Data Table ---
        with st.expander("View data", expanded=True):
            st.dataframe(df, use_container_width=True)

except Error as e:
    st.error("MySQL Error: " + str(e))
except Exception as ex:
    st.error("Error: " + str(ex))

# --- Footer ---
st.markdown("---")
st.caption("Tip: Use the sidebar to switch between insights. For help importing the dump, refer to your setup guide.")