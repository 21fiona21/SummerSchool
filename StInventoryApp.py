# WebApp for viewing and editing the SHSG Inventorx Database

# Import Libraries
import sqlite3
import pandas as pd
import streamlit as st
from datetime import datetime, timedelta
from InventoryApp import Inventory, InventoryPerishable 
import matplotlib.pyplot as plt

# Connect to Database and query all entries
conn = sqlite3.connect('inventory.db')
query = "SELECT * FROM inventory"
df = pd.read_sql(query, conn)


# Create two columns to display logo and title next to each other
col1, col2 = st.columns([1, 5], gap="medium", vertical_alignment="center")
with col1:
    st.image("SHSG_Logo_Circle_100x100mm_RGB_green.6b31ace0.png", width=120)
with col2:
    st.markdown(f"""
        <div style='display: flex; align-items: center; height: 100%;'>
            <h1 style='margin-top: -20px; color: #008030;'>Inventory Manager</h1>
        </div>
    """, unsafe_allow_html=True)




st.write ("")
st.header("View Database") # The first part of the App we can wiew the database but not manipulate it
st.write ("")

# Section for displaying the database as a dataframe with filtering & sorting options:

# Create two columns to display checkboxes and radio buttons next to each other
col1, col2 = st.columns(2, vertical_alignment="top")
with col1:
    st.markdown("### Show:")
    # Checkboxes for non-perishables and perishables
    show_non_perishables = st.checkbox('Non-perishables', value=True)
    show_perishables = st.checkbox('Perishables', value=True)
with col2:
    st.markdown("### Sort by:")
    # Radiobuttons for sorting options
    sort_by = st.radio("Sort by:", ("ID", "Name", "Department", "Quantity", "Expiry Date"), index=0)

# Define what checkboxes should do
if show_non_perishables and not show_perishables:
    df = df[df['expiry_date'].isnull()]  # Show non-perishables
elif show_perishables and not show_non_perishables:
    df = df[df['expiry_date'].notnull()]  # Show perishables

st.write("")

# Define what checkboxes should do
if sort_by == "ID":
    df = df.sort_values(by="id")  # sort by ID, default
elif sort_by == "Name":
    df = df.sort_values(by="name")  # sort by name
elif sort_by == "Department":
    department_order = ["General", "ClubA", "ClubB", "ClubC"]
    df['department'] = pd.Categorical(df['department'], categories=department_order, ordered=True)
    df = df.sort_values(by="department")  # sort by departments
elif sort_by == "Quantity":
    df = df.sort_values(by="quantity", ascending=False)  # sort by quantity, descending
elif sort_by == "Expiry Date":
    df = df[df['expiry_date'].notnull()]  # only show perishables
    df = df.sort_values(by="expiry_date")  # sorted by expiry date, from closest to fathest

# Display table, use the database-id as index
st.dataframe(df.set_index('id'), use_container_width=True)

st.write("")
st.write("")


# Section for showing custom overviews for each department:

st.subheader("Department Overview")

# Create helpful definitions and functions to display custom information for each department in containers:

# Define number of items in every department and list of items
general_items = df[df['department'] == 'General'][['name', 'quantity', 'expiry_date']]
club_a_items = df[df['department'] == 'ClubA'][['name', 'quantity', 'expiry_date']]
club_b_items = df[df['department'] == 'ClubB'][['name', 'quantity', 'expiry_date']]
club_c_items = df[df['department'] == 'ClubC'][['name', 'quantity', 'expiry_date']]
general_count = general_items.shape[0]
club_a_count = club_a_items.shape[0]
club_b_count = club_b_items.shape[0]
club_c_count = club_c_items.shape[0]

# Get today's date
today = datetime.today().date()

# Funktion to find Items that will expire within 30 days from today
def find_expiring_items(items_df):
    expiring_items = []
    for _, row in items_df.iterrows():
        if pd.notnull(row['expiry_date']):
            expiry_date = datetime.strptime(row['expiry_date'], "%Y-%m-%d").date()
            days_left = (expiry_date - today).days
            if 0 < days_left <= 30:
                expiring_items.append(f"{row['name']} in <strong>{days_left}</strong> days")
    return expiring_items

# Define design & formatting rules for the containers
st.markdown("""
    <style>
    .custom-container-general {
        background-color: #98FB98;  /* Green for General */
        padding: 15px;
        border-radius: 10px;
        margin: 10px 0;
    }
    .custom-container-clubA {
        background-color: #ADD8E6;  /* Blue for ClubA */
        padding: 15px;
        border-radius: 10px;
        margin: 10px 0;
    }
    .custom-container-clubB {
        background-color: #D8BFD8;  /* Purple for ClubB */
        padding: 15px;
        border-radius: 10px;
        margin: 10px 0;
    }
    .custom-container-clubC {
        background-color: #FFB6C1;  /* Pink for ClubC */
        padding: 15px;
        border-radius: 10px;
        margin: 10px 0;
    }
    .item-list {
        list-style-type: none;
        padding-left: 20px;
    }
    .item-list li {
        display: flex;
        justify-content: space-between;
        padding: 5px 0;
    }
    .item-name {
        flex: 1;
    }
    .item-quantity {
        text-align: left;
        padding-right: 40px;
        flex: 0;
    }
    .warning {
        color: red;
        font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

# Support function to display items in a list
def format_items(items_df):
    return "".join([
        f"<li style='margin-left: 20px; list-style-type: none;'><strong>-</strong> <span class='item-name'>{row['name']}:</span><span class='item-quantity'>{row['quantity']}</span></li>"
        for _, row in items_df.iterrows()
    ])

# Create two columns with two containers each. The definitions and funktions defined before are being 
# called to format containers and  their content
col1, col2 = st.columns(2)

# First column first container: Dept. General
with col1:
    # create a header, say how many registerd items there are, display simpe list of registered items
    container_content_general = f"""
        <div class="custom-container-general">
            <h4>General</h4>
            <p><strong>{general_count}</strong> Registered items:</p>
            <ul class='item-list'>{format_items(general_items)}</ul>
    """
    # If there are registered perishable items within the department that will expire soon, include a warning
    expiring_items_general = find_expiring_items(general_items)
    if expiring_items_general:
        container_content_general += "<div style='color: red; font-weight: bold; font-size: 18px;'>🚨 Attention!</div>"
        container_content_general += "<div style='color: red; font-size: 16px;'><strong>Some of your items will expire soon:</strong></div>"
        # List all items about to expire and calculate how many days are left
        for item in expiring_items_general:
            parts = item.split(' ')
            name = ' '.join(parts[:-3])
            days_left = parts[-2]
            container_content_general += f"<div style='color: red; font-size: 16px;'>- <strong style='font-weight: bold;'>{name}</strong> will expire in <strong style='font-weight: bold;'>{days_left}</strong> days</div>"

    # End of container
    container_content_general += "</div>"
    # Show whole container at once
    st.markdown(container_content_general, unsafe_allow_html=True)

# First column second container: Dept. ClubB - analogue to container "General"
with col1:
    container_content_club_b = f"""
        <div class="custom-container-clubB">
            <h4>ClubB</h4>
            <p><strong>{club_b_count}</strong> Registered items:</p>
            <ul class='item-list'>{format_items(club_b_items)}</ul>
    """
    expiring_items_club_b = find_expiring_items(club_b_items)
    if expiring_items_club_b:
        container_content_club_b += "<div style='color: red; font-weight: bold; font-size: 18px;'>🚨 Attention!</div>"
        container_content_club_b += "<div style='color: red; font-size: 16px;'><strong>Some of your items will expire soon:</strong></div>"
        for item in expiring_items_club_b:
            parts = item.split(' ')
            name = ' '.join(parts[:-3])
            days_left = parts[-2]
            container_content_club_b += f"<div style='color: red; font-size: 16px;'>- <strong style='font-weight: bold;'>{name}</strong> will expire in <strong style='font-weight: bold;'>{days_left}</strong> days</div>"

    container_content_club_b += "</div>"
    st.markdown(container_content_club_b, unsafe_allow_html=True)

# Second column first container: Dept. ClubA - analogue to container "General"
with col2:
    container_content_club_a = f"""
        <div class="custom-container-clubA">
            <h4>ClubA</h4>
            <p><strong>{club_a_count}</strong> Registered items:</p>
            <ul class='item-list'>{format_items(club_a_items)}</ul>
    """
    expiring_items_club_a = find_expiring_items(club_a_items)
    if expiring_items_club_a:
        container_content_club_a += "<div style='color: red; font-weight: bold; font-size: 18px;'>🚨 Attention!</div>"
        container_content_club_a += "<div style='color: red; font-size: 16px;'><strong>Some of your items will expire soon:</strong></div>"
        for item in expiring_items_club_a:
            parts = item.split(' ')
            name = ' '.join(parts[:-3])
            days_left = parts[-2]
            container_content_club_a += f"<div style='color: red; font-size: 16px;'>- <strong style='font-weight: bold;'>{name}</strong> will expire in <strong style='font-weight: bold;'>{days_left}</strong> days</div>"
    
    container_content_club_a += "</div>"
    st.markdown(container_content_club_a, unsafe_allow_html=True)

# Second column second container: Dept. ClubC - analogue to container "General"
with col2:
    container_content_club_c = f"""
        <div class="custom-container-clubC">
            <h4>ClubC</h4>
            <p><strong>{club_c_count}</strong> Registered items:</p>
            <ul class='item-list'>{format_items(club_c_items)}</ul>
    """
    expiring_items_club_c = find_expiring_items(club_c_items)
    if expiring_items_club_c:
        container_content_club_c += "<div style='color: red; font-weight: bold; font-size: 18px;'>🚨 Attention!</div>"
        container_content_club_c += "<div style='color: red; font-size: 16px;'><strong>Some of your items will expire soon:</strong></div>"
        for item in expiring_items_club_c:
            parts = item.split(' ')
            name = ' '.join(parts[:-3])
            days_left = parts[-2]
            container_content_club_c += f"<div style='color: red; font-size: 16px;'>- <strong style='font-weight: bold;'>{name}</strong> will expire in <strong style='font-weight: bold;'>{days_left}</strong> days</div>"
   
    container_content_club_c += "</div>"
    st.markdown(container_content_club_c, unsafe_allow_html=True)


st.write("")
st.write("")
st.write("")

# Section for viewing graphs & statistict of the inventory:

st.subheader("Inventory Insights")
st.write("")
st.write("")

# Create two colums to display charts next to each other
# Before creating the columns, we globally define a new data frame first, because wen want to use it for two charts in differnt columns...
# It's derrived from the original one, but sorted by epiry date, to make expiry-pie-chart creation easier & and show perishables df
df_piechart2 = df.copy()
df_piechart2['expiry_date'] = pd.to_datetime(df_piechart2['expiry_date'], errors='coerce').dt.date  # Nur das Datum verwenden
df_piechart2 = df_piechart2.sort_values(by=['expiry_date'], ascending=[False])
df_piechart2 = pd.concat([df_piechart2[df_piechart2['expiry_date'].isna()], df_piechart2.dropna(subset=['expiry_date'])])

col1, col2 = st.columns(2)
with col1:
    # Pie chart for showing department share of inventory:
    # Create a new data frame from original one - sorted by department
    df['department'] = pd.Categorical(df['department'], categories=['General', 'ClubA', 'ClubB', 'ClubC'], ordered=True)
    df_piechart = df.sort_values('department')
    # Calculate total sum of quantity of all items
    total_quantity = df_piechart['quantity'].sum()
    # Define & assign colors for each department
    colors = {
        'General': '#98FB98',  # Sanftes Grün
        'ClubA': '#ADD8E6',    # Helles Blau
        'ClubB': '#D8BFD8',    # Sanftes Lila
        'ClubC': '#FFB6C1'     # Sanftes Rosa-Rot
    }
    item_colors = [colors[dept] for dept in df_piechart['department']]
    # Calculate the percentage for each department
    department_totals = df_piechart.groupby('department')['quantity'].sum()
    percentages = (department_totals / total_quantity) * 100
    # Create pie chart
    fig, ax = plt.subplots(figsize=(10, 10))
    ax.pie(df_piechart['quantity'], labels=None, colors=item_colors, autopct=None, startangle=90, counterclock=False,
        wedgeprops={'edgecolor': 'grey', 'linewidth': 0.3})
    # Define labels for the legend with percentages
    legend_labels = [f'{dept}: {percentages[dept]:.1f}%' for dept in colors.keys()]
    # Create legend
    handles = [plt.Rectangle((0, 0), 1, 1, color=colors[dept]) for dept in colors.keys()]
    ax.set_title("Share of Quantity by Department", fontsize=20, fontweight='bold')
    ax.legend(handles, legend_labels, title="Departments", loc="upper right", frameon=False)
    ax.axis('equal')
    # Display the plot in Streamlit
    st.pyplot(fig)


    st.write("")
    st.write("")


    # Pie chart for showing relation of perishables and non-perishables:
    # This chart makes use of the df_piechart2 dataframe defined before the columns

    # define today's date and date in 30 days
    today = datetime.today().date()
    thirty_days_from_now = today + timedelta(days=30)

    # Define & assign colours for items
    def get_color(expiry_date):
        if pd.isna(expiry_date):
            return '#98FB98'  # Green for non-perishables
        elif expiry_date <= thirty_days_from_now:
            return '#FF6347'  # Red for perishables expiring within 30 days
        else:
            return '#FFA500'  # Orange for other perishables
    # Assign colors for each item
    df_piechart2['color'] = df_piechart2['expiry_date'].apply(get_color)
    # Calculate the total quantity for each color category
    non_perishables_count = sum(df_piechart2['color'] == '#98FB98')
    perishables_count = sum(df_piechart2['color'] == '#FFA500')
    expiring_soon_count = sum(df_piechart2['color'] == '#FF6347')
    total_count = len(df_piechart2)
    # Calculate percentages
    non_perishables_pct = (non_perishables_count / total_count) * 100
    perishables_pct = (perishables_count / total_count) * 100
    expiring_soon_pct = (expiring_soon_count / total_count) * 100
    # Create pie chart
    fig, ax = plt.subplots(figsize=(10, 10))
    ax.pie([1] * len(df_piechart2), labels=None, colors=df_piechart2['color'], startangle=90, counterclock=False, wedgeprops={'edgecolor': 'grey', 'linewidth': 0.5})
    # Define labels for the legend with percentages
    legend_labels = [
        f'Non-perish.: {non_perishables_pct:.1f}%', 
        f'Perish.: {perishables_pct:.1f}%', 
        f'Exp. 30 d.: {expiring_soon_pct:.1f}%'
    ]
    legend_colors = ['#98FB98', '#FFA500', '#FF6347'] 
    # Create legend
    handles = [plt.Rectangle((0, 0), 1, 1, color=color) for color in legend_colors]
    ax.set_title("Items by Expiry Date", fontsize=20, fontweight='bold')
    ax.legend(handles, legend_labels, title="Expiry Status", loc="upper right", frameon=False)
    ax.axis('equal')  # Make sure pie is drawn as a circle
    # Display the plot in Streamlit
    st.pyplot(fig)




with col2:
    # Bar chart for showing total quantity of unique items, show departments:
   
    # calculate total quantity of items with same name, group by name and department
    df_barchart = df.groupby(['name', 'department'], as_index=False)['quantity'].sum()
    total_quantities = df_barchart.groupby('name')['quantity'].sum().reset_index()
    total_quantities = total_quantities.sort_values(by='quantity', ascending=True)
    # Define & assign colours for every department
    colors = {
        'General': '#98FB98',  # Sanftes Grün
        'ClubA': '#ADD8E6',    # Helles Blau
        'ClubB': '#D8BFD8',    # Sanftes Lila
        'ClubC': '#FFB6C1'     # Sanftes Rot
    }
    df_barchart['color'] = df_barchart['department'].map(colors)
    # Create bar chart
    fig, ax = plt.subplots(figsize=(7, 8))
    # Remove margines ("box" around chart)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(False)
    ax.spines['bottom'].set_visible(False)
    # Initialize a dictionary for saving total quantity of every item
    cumulative_quantity = {name: 0 for name in total_quantities['name']}
    # For every name, stack the bars in the defined colours based on the defined order of departments
    for name in total_quantities['name']:
        item_data = df_barchart[df_barchart['name'] == name]
        for _, row in item_data.iterrows():
            ax.barh(name, row['quantity'], left=cumulative_quantity[name], color=row['color'])
            cumulative_quantity[name] += row['quantity']
    # Define no labeling on axes
    ax.set_xlabel('')
    ax.set_ylabel('')
    ax.set_title('Items by total Quantity and Department', fontsize=18, fontweight='bold')
    st.pyplot(fig)

    st.write("")
    st.write("")
    st.write("")

    
    # Show smaller, adjusted df with items about to expire, sorted from closest date to farthest. it uses the df_pychart2 defined before the columns
    st.markdown("<h3 style='font-weight: bold; font-size: 15px; text-align: center;'>Next items to expire</h3>", unsafe_allow_html=True)
    st.dataframe(df_piechart2.drop(columns=['quantity', 'id', "color"]).dropna(subset=['expiry_date']).sort_values(by='expiry_date', ascending=True).set_index('name'), use_container_width=True, height=300)



st.write("")
st.write("")
st.write("")



st.header("Edit Database") # The second part of the App is for editing the database
st.write("")

departments = Inventory.VALID_DEPARTMENTS  # Use own list of valid departments

st.write("Add a new item to the current inventory:")

# Streamlit form widget for entering item attributes of new items
with st.form(key='item_form'):
    name = st.text_input('Item name') # Enter name
    department = st.selectbox('Department', departments)  # Dropdown for department selection
    quantity = st.number_input('Quantity', min_value=0, format="%i", value=0)  # Enter quantity, restricted to non-negative
    is_perishable = st.selectbox('Is item perishable?', ["No", "Yes"]) # perishable yes/no
    expiry_date = st.date_input('Enter the expiry date')  # Always displayed, but doesnt affect functinality if "no" is selected
    # Button to commit new item to database
    submit_button = st.form_submit_button(label='Add item') 
    if submit_button:
        # Exta pop-up button
        @st.dialog('Confirm Addition')
        def confirm_addition(name, department, quantity, expiry_date):
            st.write(f"Do you want to add {name} to the inventory?")
            if st.button('Yes'):
                # Add to database
                with sqlite3.connect('inventory.db') as conn:
                    if is_perishable == "Yes":
                        item = InventoryPerishable(name, department, quantity, expiry_date.strftime("%Y-%m-%d"))
                    else:
                        item = Inventory(name, department, quantity)
                    item.create_item(conn)
                    st.success('Item added!')
        # display confirmation message
        confirm_addition(name, department, quantity, expiry_date)

st.write("")
st.write("")

st.write("Remove an item from the current inventory:")

# Streamlit form widget for entering id of itm to delete
delete_id_option = st.text_input("Enter the ID of the item you want to delete", key='delete_id')

# Preview button to show all attributes of item to delete
if st.button('Preview'):
    query = "SELECT * FROM inventory"
    df = pd.read_sql(query, conn)
    item_data = df[df['id'] == int(delete_id_option)]
    if not item_data.empty:
        st.write("Item's Details:")
        st.dataframe(item_data)
    else:
        st.write("No item found with the specified ID.")

# Dialoge pop-up info for asking if it really should be deleted 
@st.dialog('Confirm Deletion')

# Define a function for what shouls happen after clicking "delete", all within dialog pop-up window
def confirm_delete(delete_id_option):
    st.write(f"Are you sure you want to delete item with ID {delete_id_option}?")
    if st.button('Yes'):
        with sqlite3.connect('inventory.db') as conn:
            query = "DELETE FROM inventory WHERE id = ?"
            cur = conn.cursor()
            cur.execute(query,(int(delete_id_option),))
            conn.commit()
            if cur.rowcount:
                st.success(f'Item {delete_id_option} removed successfully!')
            else:
                st.error(f'Failed to remove item {delete_id_option}. Please try again.')

# Button that triggers dialog
if st.button('Delete'):
    confirm_delete(delete_id_option)
   
# close connection to database
conn.close()