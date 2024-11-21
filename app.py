"""
Name: Agnes Szymanski
CS230: F2024 Section 6
Data: Boston Airbnb
URL:

Description: The Boston Airbnb Finder is a web applicattion built for users looking to explore
Boston. It (1) displays top-rated Airbnbs filtered by user-selected criteria (minimum rating
and neighborhoods) and presents results on an interactive map, (2) provides price distribution
information for Boston neighborhoods with dynamic charts, showing the average prices and price ranges,
(3) searches for the most affordable Airbnbs and displays them on an interactive map, and (4) features
a catalog of Boston's top restaurants with location and cuisine filters for easy navigation.
"""
import streamlit as st
import pandas as pd
import pydeck as pdk
import matplotlib.pyplot as plt

# Function to filter Airbnb listings based on price range and optionally by neighborhood
def filter_listings(data, min_price, max_price, neighborhood=None):
    if neighborhood: # If a neighborhood is specified
        # Return rows that meet the price range and neighborhood condition
        return data[(data['price'] >= min_price) &
                    (data['price'] <= max_price) &
                    (data['neighbourhood'] == neighborhood)]
    # Return rows that meet the price range condition only
    return data[(data['price'] >= min_price) & (data['price'] <= max_price)]

# Function for loading + cleaning
def load_data():
    try:
        # Load Airbnb listings from a CSV file
        listings = pd.read_csv("listings.csv")
        # Load neighborhood data from a CSV file
        neighbourhoods = pd.read_csv("neighbourhoods.csv")
        # Load reviews data from a CSV file
        reviews = pd.read_csv("reviews.csv")
        # Load restaurant data from an Excel file
        restaurants = pd.read_excel("restaurants.xlsx")  # Load the restaurants file
    except FileNotFoundError as e: # Handles file not found errors
        st.error(f"File not found: {e}")
        return None, None, None, None
    except pd.errors.ParserError as e:  # Handles CSV or Excel parsing errors
        st.error(f"Error parsing CSV or Excel files: {e}")
        return None, None, None, None

    # Drop rows in the listings data that have missing values in key columns
    listings = listings.dropna(subset=["price", "availability_365", "neighbourhood", "number_of_reviews"])
    # Convert the 'price' column to numeric, handling invalid values as NaN
    listings["price"] = pd.to_numeric(listings["price"], errors="coerce")
    # Convert the 'availability_365' column to numeric, handling invalid values as NaN
    listings["availability_365"] = pd.to_numeric(listings["availability_365"], errors="coerce")
    # Convert the 'number_of_reviews' column to numeric, handling invalid values as NaN
    listings["number_of_reviews"] = pd.to_numeric(listings["number_of_reviews"], errors="coerce")
    # Fill missing values in the 'reviews_per_month' column with 0
    listings["reviews_per_month"] = listings["reviews_per_month"].fillna(0)

    # Add a new column 'rating' to the listings DataFrame, calculating a rating based on reviews per month
    listings["rating"] = listings["reviews_per_month"].apply(lambda x: x * 5 if x * 5 <= 5 else 5)
    # Return the cleaned data
    return listings, neighbourhoods, reviews, restaurants

# Home Page
def main_page():
    st.title("Welcome to Boston Airbnb Finder!")

    st.write("""
        Are you searching for a nice Airbnb to stay in during your upcoming Boston getaway? 
        You've found the right place! Navigate this website to find out:

        - What the top-rated Airbnbs are in Boston
        - Which neighborhoods they're located in
        - And the cheapest options to get the best-rated Airbnbs
        - And some restaurant recommendations around the city

        Plan your stay efficiently and discover the hidden Airbnb gems that Boston has to offer!
    """)
    # Image of Boston skyline
    st.image("Main page pic.webp", use_container_width=True)

# Query 1
#Function for the top-rated Airbnbs page
def top_rated_airbnbs_page(listings, neighbourhoods):
    st.title("Top-Rated Airbnbs in Boston")

    # Adds slider for filtering by minimum rating
    min_rating = st.slider("Minimum Rating (1-5)", min_value=1.0, max_value=5.0, step=0.1, value=4.5)
    # Add a multiselect for filtering by neighborhoods
    selected_neighborhoods = st.multiselect(
        "Select Neighborhood(s) around Boston", neighbourhoods['neighbourhood'].unique()
    )

    # Error-handling when rating column doesn't show up
    if 'rating' not in listings.columns:
        listings['rating'] = listings['reviews_per_month'] * 5

    # Filters listings to include only those with a rating greater than or equal to the minimum rating
    filtered_data = listings[listings['rating'] >= min_rating]

    # Extract the names of Airbnbs with high ratings
    high_rating_names = [name for name in filtered_data['name'] if len(name) > 0]
    st.write(f"Airbnbs with Rating >= {min_rating}:")
    # Filters if specified neighborhoods
    if selected_neighborhoods:
        filtered_data = filtered_data[filtered_data['neighbourhood'].isin(selected_neighborhoods)]

    # Map
    map_data = filtered_data[['latitude', 'longitude', 'name', 'price', 'rating']]
    tooltip = {
        "html": "<b>Name:</b> {name}<br><b>Price:</b> ${price}<br><b>Rating:</b> {rating}",
        "style": {"backgroundColor": "steelblue", "color": "white"}
    }
    # Initial view for the map
    view_state = pdk.ViewState(
        latitude=filtered_data['latitude'].mean(),
        longitude=filtered_data['longitude'].mean(),
        zoom=13,
        pitch=0
    )
    # Define scatterplot layer for the map
    layer = pdk.Layer(
        "ScatterplotLayer",
        data=map_data,
        get_position="[longitude, latitude]",
        get_color="[200, 30, 0, 160]",
        get_radius=100,
        pickable=True,
    )
    # Combines layer and view state into a complete deck
    deck = pdk.Deck(
        layers=[layer],
        initial_view_state=view_state,
        tooltip=tooltip
    )
    st.pydeck_chart(deck)

# Query 2
# Function to show price distribution
def price_distribution_page(listings, neighbourhoods):
    #page title
    st.title("Price Distribution of Airbnbs in a Selected Neighborhood")

    # Adds dropdown menu
    neighborhood = st.selectbox(
        "Select Neighborhood(s) around Boston",
        ['All'] + list(neighbourhoods['neighbourhood'].unique())
    )
    # Adds slider
    price_range = st.slider(
        "Select Price Range",
        min_value=int(listings['price'].min()),
        max_value=int(listings['price'].max()),
        value=(50, 300)  # Default range
    )

    # Filters listings based on the selected neighborhood and price range
    if neighborhood == 'All': # Checking for ALL selections
        filtered_data = listings[
            (listings['price'] >= price_range[0]) & # Filter listings with prices greater than or equal to min price
            (listings['price'] <= price_range[1]) # Filter listings with prices less than or equal to max price
        ]
    else: # Used when specific neighborhood is selected
        filtered_data = listings[
            (listings['neighbourhood'] == neighborhood) & # Filter selected neighborhood
            (listings['price'] >= price_range[0]) & # Filter listings with prices greater than or equal to min price
            (listings['price'] <= price_range[1]) # Filter listings with prices less than or equal to max price
        ]

    # Dynamic message showing filtering range
    if neighborhood == 'All': # If ALL is selected
        st.write(
            f"### Showing data for all neighborhoods within the price range ${price_range[0]} to ${price_range[1]}")
    else: # Specific neighborhood
        st.write(
            f"### Showing data for {neighborhood} within the price range ${price_range[0]:,.0f} to ${price_range[1]:,.0f}")

    # Creates a pivot table to calculate the average price per neighborhood
    price_pivot = pd.pivot_table(
        filtered_data,  # Filtered data from user input
        values="price",  # Average price, aggregate function
        index="neighbourhood", # Grouping by neighborhood
        aggfunc="mean" # Calculate mean price, aggregate function
    ).round(2).reset_index() # Round prices to two decimal places + reset index

    # Display pivot table in Streamlit
    st.write("### Average Price by Neighborhood:")
    st.dataframe(price_pivot,height=300, width=600) # Show pivot table

    # Create bar chart for the price distribution
    st.write(f"### Price Distribution for {'All Neighborhoods' if neighborhood == 'All' else neighborhood}")
    # Create new figure and axis for plotting
    fig, ax = plt.subplots()
    # Use index of filtered data for the x-axis
    ax.bar(filtered_data.index, filtered_data['price'], color='skyblue', edgecolor='black')
    # Use price column for the y-axis
    ax.set_title(f"Price Distribution in {neighborhood}")
    # X-axis label
    ax.set_xlabel("Listings")
    # Y-axis label
    ax.set_ylabel("Price (in $)")
    # Display chart
    st.pyplot(fig)

    # Query 3
    # Function for most affordable Airbnbs
def most_affordable_airbnbs_page(listings):
    # Page title
    st.title("Most Affordable Airbnbs in Boston")

    # Dropdown menu
    selected_neighborhood = st.selectbox(
        "Select a neighborhood that has the best price distribution for you, and look for the cheapest Airbnb in that area! Dont be scared to try new neighborhoods and explore places you haven't been yet!", #Label
        ['All'] + list(listings['neighbourhood'].unique()) # Including ALL and unique neighborhood names
    )
    #Filter listings for affordable options (price < 200)
    affordable_data = filter_listings(listings, 0, 200, neighborhood=None if selected_neighborhood == 'All' else selected_neighborhood)
    # Sort filtered data by price in ascending order and select top 10
    affordable_data = affordable_data.sort_values(by='price').head(10)

    # Data for map to display affordable Airbnbs
    map_data = affordable_data[['latitude', 'longitude', 'name', 'price', 'rating']] #Selecting columns for mao
    tooltip = {
        "html": "<b>Name:</b> {name}<br>" # Put name in tooltip
                "<b>Price:</b> ${price}<br>" # Display price in tooltip
                "<b>Rating:</b> {rating}", #nDisplay rating in tooltip
        "style": {"backgroundColor": "steelblue", "color": "white"} # Tooltip style
    }
    # Initial map view
    view_state = pdk.ViewState(
        latitude=affordable_data['latitude'].mean(), # Set map center latitude
        longitude=affordable_data['longitude'].mean(), # Set map center longitude
        zoom=12, # zoom level
        pitch=0 # Pitch angle
    )
    # Define scatterplot layer for the map
    layer = pdk.Layer(
        "ScatterplotLayer", # Using ScatterplotLayer type
        data=map_data, # Data for scatterplot
        get_position="[longitude, latitude]", #Specifying position with longitude and latitude
        get_color="[0, 200, 30, 160]", # Color of points
        get_radius=120, # Set radius of points
        pickable=True, #enable scrolling
    )
    # combine layer + view for complete map
    deck = pdk.Deck(
        layers=[layer], #Add the scatterplot layer
        initial_view_state=view_state,# Set initial view state
        tooltip=tooltip # Tooltip
    )
    #Display
    st.pydeck_chart(deck)

# Extra restaurant page
def restaurant_page(restaurants):
    #title
    st.title("Boston Restaurants")
    st.write("Now that you found a place to stay, you must explore the neighborhood! What better way than discovering the  best restaurants in Boston!")

    st.write("Browse through the 50 most popular restaurants around Boston, OR scroll down for a personalized experience. All you have to do is enter your location and the type of cuisine you want, and Boston Airbnb Finder will do the rest!")
    # Show restaurant catalogue
    st.dataframe(restaurants)

    # Filters for location and cuisine
    location = st.selectbox("Select a Location", ["All"] + list(restaurants["Location"].unique()))
    cuisine = st.selectbox("Select a Cuisine", ["All"] + list(restaurants["Cuisine"].unique()))

    # Copy restaurant data for filtering
    filtered_data = restaurants.copy()  # Make copy of data to avoid messing up original
    # Apply location if selected
    if location != "All":
        filtered_data = filtered_data[filtered_data["Location"] == location]
    # Apply cuisine if selected
    if cuisine != "All":
        filtered_data = filtered_data[filtered_data["Cuisine"] == cuisine]

    # Display filtered restaurants as a table
    st.write("### Available Restaurants:")
    st.dataframe(filtered_data)

# Main
def main():
    st.markdown("""<style>.stApp {background-color: #9e99e8;}</style>""", unsafe_allow_html=True)

    st.sidebar.title("Your perfect Airbnb awaits...")
    page = st.sidebar.selectbox(
        "Choose a Page",
        options=["Home", "Top-Rated Airbnbs", "Price Distribution", "Most Affordable Airbnbs", "Boston Restaurants"],
        format_func=lambda x: {
            "Home": "🏠 Home",
            "Top-Rated Airbnbs": "⭐ Top-Rated Airbnbs",
            "Price Distribution": "💰 Price Distribution",
            "Most Affordable Airbnbs": "🏡 Most Affordable Airbnbs",
            "Boston Restaurants": "🍽️ Boston Restaurants"
        }[x]
    )
    # Load data post error handling
    listings, neighbourhoods, reviews, restaurants = load_data() #load all datasets

    # Check if data loading was successful
    if listings is None or neighbourhoods is None or reviews is None or restaurants is None:
        st.error("Error loading data. Please check the file paths and try again.") # Error message if data is missing
        return  # If data loading fails stop running


    # Navigate to user selected page
    if page == "Home":
        main_page() # Show home page
    elif page == "Top-Rated Airbnbs":
        top_rated_airbnbs_page(listings, neighbourhoods) # Show top-rated Airbnbs page
    elif page == "Price Distribution":
        price_distribution_page(listings, neighbourhoods) # Show price distribution page
    elif page == "Most Affordable Airbnbs":
        most_affordable_airbnbs_page(listings) # Show most affordable Airbnbs page
    elif page == "Boston Restaurants":
        restaurant_page(restaurants)  # Show Boston restaurants page

if __name__ == "__main__":
    main()
