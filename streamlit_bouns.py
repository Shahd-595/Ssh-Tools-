import streamlit as st
from pymongo import MongoClient
import base64
from PIL import Image
import pandas as pd
import plotly.express as px
import re

# a very important resource
@st.cache_resource
def init_connection():
    client = MongoClient("mongodb://localhost:27017/")
    return client

client = init_connection()
db = client["BOOKS"]
books_collection = db["CLEANED_BOOKS"]
books_analysis = db["BOOKS_Association_Rules"]

st.sidebar.title("The Main List")

# background music
audio_file = open(r'C:\Users\DELL\Downloads\ambient-fantasy-314682.mp3', 'rb')
audio_bytes = audio_file.read()

# Encode the audio file to Base64
encoded_audio = base64.b64encode(audio_bytes).decode()

# Create an HTML audio tag with autoplay, loop, and hidden attributes
background_audio = f"""
    <audio autoplay loop hidden>
        <source src="data:audio/mp3;base64,{encoded_audio}" type="audio/mp3">
    </audio>
"""
# Inject the HTML into the Streamlit app
st.markdown(background_audio, unsafe_allow_html=True)

# make the sidebar and the header in the naive blue color
st.markdown(
    """
    <style>
    [data-testid="stSidebar"] {
    background-color: #001f3f; /* naive blue color code */
    color: white; /* change the writing to be white */
    }
    
    [data-testid="stSidebar"] * {
        color: white !important; /* it must be white  */
    }

    /* change header color */
    header[data-testid="stHeader"] {
        background-color: #001f3f;
    }

    /* hide the line between the header and the contact */
    header[data-testid="stHeader"]::after {
        background: none;
    }
    </style>
    """,
    unsafe_allow_html=True
)

options = ["Books", "Search Books" , "Analysis", "Visualization"]

# display the books
def show_books():
    st.title("BOOKS")

    # background color
    base_page = """
    <style>
    [data-testid="stAppViewContainer"] {
        background: linear-gradient(to right, #ff7e5f, #feb47b, #86a8e7, #91eae4);
    }
    </style>
    """
    st.markdown(base_page, unsafe_allow_html=True)

    #number of pages (20 books in one page)
    num_pages = 393

    # Get the current page number from session state, initialize to 1 if not present
    if "current_page" not in st.session_state:
        st.session_state["current_page"] = 1

    def next_page():
        if st.session_state["current_page"] < num_pages:
            st.session_state["current_page"] += 1

    def prev_page():
        if st.session_state["current_page"] > 1:
            st.session_state["current_page"] -= 1

    col1, col2 = st.columns([1, 1])
    with col1:
        st.button("Previous Page", on_click=prev_page)
    with col2:
        st.button("Next Page", on_click=next_page)

    st.write(f"Page {st.session_state['current_page']} of {num_pages}")

    # Calculate the number of documents to skip
    skip_amount = (st.session_state["current_page"] - 1) * 20

    # Fetch books for the current page
    books_on_page = books_collection.find().skip(skip_amount).limit(20)

    for book in books_on_page:
        with st.expander(book.get("title", "Untitled")):
            st.write(f"Title: {book.get('title', 'N/A')}")
            st.write(f"Author: {book.get('author', 'N/A')}")
            st.write(f"Publish Date: {book.get('publish_date', 'N/A')}")
            st.write(f"Language: {book.get('language', 'N/A')}")
            st.write(f"Subjects: {', '.join(book.get('cleaned_subjects', []))}")
            st.write(f"Pages Number: {book.get('num_pages', 'N/A')}")
            st.write(f"Edition Count: {book.get('edition_count', 'N/A')}")
            st.write(f"Covers Count: {book.get('covers_count', 'N/A')}")
            st.write(f"Average Rating: {book.get('average_rating', 'N/A')}")
            st.write(f"Rating Count: {book.get('rating_count', 'N/A')}")
            st.write(f"URL: {book.get('url', 'N/A')}")

# search for books
def show_search_books():

    # background color
    base_page = """
    <style>
    [data-testid="stAppViewContainer"] {
        background: linear-gradient(to left, #92a8d1, #034f84, #f7cac9, #f7786b);
    }
    </style>
    """
    st.markdown(base_page, unsafe_allow_html=True)
    # search for book by title
    search_term = st.text_input("Search by Title:")

    # get the unique values for the 'publish date' and 'language'
    publish_dates = books_collection.distinct("publish_date")
    languages = books_collection.distinct("language")

    # Extract unique cleaned subjects from MongoDB
    subjects = books_collection.aggregate([
        {"$project": {"subjects": {"$split": ["$subjects", ","]}}},
        {"$unwind": "$subjects"},
        {"$project": {"subject": {"$trim": {"input": {"$toLower": "$subjects"}}}}},
        {"$match": {"subject": {"$ne": ""}}},
        {"$group": {"_id": "$subject"}}
    ])

    def is_valid_subject(subj):
        if not subj:
            return False
        cleaned_subj = re.sub(r'[\d\-\&\(\)\.\*]+', '', subj).strip()
        return (
                len(cleaned_subj) >= 3 and
                sum(c.isalpha() for c in cleaned_subj) >= 3
        )
    unique_subjects = sorted({doc["_id"] for doc in subjects if is_valid_subject(doc.get("_id", ""))})
    # choices keys
    selected_date = st.selectbox("Filter by Publish Date:", ["All"] + list(publish_dates))
    selected_language = st.selectbox("Filter by Language:", ["All"] + list(languages))
    selected_subject = st.selectbox("Filter by Subject:", ["All"] + unique_subjects)

    # Build MongoDB query based on search and filters
    query = {}
    if search_term:
        query["title"] = {"$regex": search_term, "$options": "i"}  # Case-insensitive search
    if selected_date != "All":
        query["publish_date"] = selected_date
    if selected_language != "All":
        query["language"] = selected_language
    if selected_subject != "All":
        query["subjects"] = {"$regex": f"(?i){re.escape(selected_subject)}"}

    # Retrieve books based on the query
    found_books = books_collection.find(query)

    # Display search results and details on expand
    for book in found_books:
        with st.expander(book.get("title", "Untitled")):
            st.write(f"Title: {book.get('title', 'N/A')}")
            st.write(f"Author: {book.get('author', 'N/A')}")
            st.write(f"Publish Date: {book.get('publish_date', 'N/A')}")
            st.write(f"Language: {book.get('language', 'N/A')}")
            st.write(f"Subjects: {', '.join(book.get('cleaned_subjects', []))}")
            st.write(f"Pages Number: {book.get('num_pages', 'N/A')}")
            st.write(f"Edition Count: {book.get('edition_count', 'N/A')}")
            st.write(f"Covers Count: {book.get('covers_count', 'N/A')}")
            st.write(f"Average Rating: {book.get('average_rating', 'N/A')}")
            st.write(f"Rating Count: {book.get('rating_count', 'N/A')}")
            st.write(f"URL: {book.get('url', 'N/A')}")

# display the association rules
def show_analysis():

    # background color
    base_page = """
        <style>
        [data-testid="stAppViewContainer"] {
            background: linear-gradient(to right, #b2b2b2, #f4e1d2, #f18973, #bc5a45);
        }
        </style>
        """
    st.markdown(base_page, unsafe_allow_html=True)

    st.title("ASSOCIATION RULES")
    analysis_results = books_analysis.find()  # extract the information

    # display the information
    for result in analysis_results:
        title = f"{result.get('antecedents_str', 'Untitled')} ---> {result.get('consequents_str', 'Untitled')}"
        with st.expander(title):
            st.write(f"Antecedents: {result.get('antecedents_str', 'N/A')}")
            st.write(f"Consequences: {result.get('consequents_str', 'N/A')}")
            st.write(f"Support: {result.get('support', 'N/A')}")
            st.write(f"Confidence: {result.get('confidence', 'N/A')}")
            st.write(f"lift: {result.get('lift', 'N/A')}")

# display the plots and dashboards
def show_visualization():

    # background color
    base_page = """
        <style>
        [data-testid="stAppViewContainer"] {
            background: linear-gradient(to right, #f9d5e5, #eeac99, #e06377, #c83349);
        }
        </style>
    """
    st.markdown(base_page, unsafe_allow_html=True)

    st.title("VISUALIZATION")

    visuals = [
        "Boxplots Of The Distribution",
        "Dashboard Of Book Titles Analysis",
        "Dashboard Of Language Based Book Statistics",
        "Dashboard Of Author Based Book Statistics",
        "The Frequency Of Top Frequent Subjects",
        "The Frequency of the Genres",
        "Published Books per Publish Date",
        "Dashboard1 Of KMeans Clustering Analysis",
        "Dashboard2 Of KMeans Clustering Analysis",
        "Network Graph For Association Rules",
        "MatrixPlot Of Lift Between Antecedents And Consequents",
        "Interactive Scatter Plot of Association Rules"
    ]

    selected_plot = None

    for visual in visuals:
        if st.button(visual):
            selected_plot = visual

    # Based on selection, display something
    if selected_plot == "Boxplots Of The Distribution":
        st.write("Boxplots Of The Distribution")
        img = Image.open("Boxplots_Of_TheDistribution.png")
        st.image(img, caption="Boxplots Of The Distribution", use_container_width=True)

    elif selected_plot == "Dashboard Of Book Titles Analysis":
        st.write("Dashboard Of Book Titles Analysis")
        img = Image.open("Dashboard_Of_BookTitlesAnalysis.png")
        st.image(img, caption="Dashboard Of Book Titles Analysis", use_container_width=True)

    elif selected_plot == "Dashboard Of Language Based Book Statistics":
        st.write("Dashboard Of Language Based Book Statistics")
        img = Image.open("Dashboard_Of_LanguageBasedBookStatistics.png")
        st.image(img, caption="Dashboard Of Language Based Book Statistics", use_container_width=True)

    elif selected_plot == "Dashboard Of Author Based Book Statistics":
        st.write("Dashboard Of Author Based Book Statistics")
        img = Image.open("Dashboard_Of_AuthorBasedBookStatistics.png")
        st.image(img, caption="Dashboard Of Author Based Book Statistics", use_container_width=True)

    elif selected_plot == "The Frequency Of Top Frequent Subjects":
        st.write("The Frequency Of Top Frequent Subjects")
        img = Image.open("TheFrequency_Of_TopFrequentSuubjects.png")
        st.image(img, caption="The Frequency Of Top Frequent Subjects", use_container_width=True)

    elif selected_plot == "The Frequency of the Genres":
        st.write("The Frequency of the Genres")
        img = Image.open("The_Frequency_of_the_Genres.png")
        st.image(img, caption="The Frequency of the Genres", use_container_width=True)

    elif selected_plot == "Published Books per Publish Date":
        st.write("Published Books per Publish Date")
        img = Image.open("Published_Books_per_PublishDate.png")
        st.image(img, caption="Published Books per Publish Date", use_container_width=True)

    elif selected_plot == "Dashboard1 Of KMeans Clustering Analysis":
        st.write("Dashboard1 Of KMeans Clustering Analysis")
        img = Image.open("Dashboard1_Of_KMeans_Clustering_Analysis.png")
        st.image(img, caption="Dashboard1 Of KMeans Clustering Analysis", use_container_width=True)

    elif selected_plot == "Dashboard2 Of KMeans Clustering Analysis":
        st.write("Dashboard2 Of KMeans Clustering Analysis")
        img = Image.open("Dashboard2_Of_KMeans_Clustering_Analysis.png")
        st.image(img, caption="Dashboard2 Of KMeans Clustering Analysis", use_container_width=True)

    elif selected_plot == "Network Graph For Association Rules":
        st.write("Network Graph For Association Rules")
        img = Image.open("Network_Graph_For_AssociationRules.png")
        st.image(img, caption="Network Graph For Association Rules", use_container_width=True)

    elif selected_plot == "MatrixPlot Of Lift Between Antecedents And Consequents":
        st.write("MatrixPlot Of Lift Between Antecedents And Consequents")
        img = Image.open("MatrixPlot_Of_LiftBetweenAntecedentsAndConsequents.png")
        st.image(img, caption="MatrixPlot Of Lift Between Antecedents And Consequents", use_container_width=True)

    elif selected_plot == "Interactive Scatter Plot of Association Rules":
        st.write("Interactive Scatter Plot of Association Rules")
        #convert MongoDB data to a DataFrame
        rules = pd.DataFrame(list(books_analysis.find()))
        # Data cleaning: Convert frozenset to a readable string
        rules['antecedents'] = rules['antecedents'].apply(
            lambda x: ', '.join(x) if isinstance(x, list) or isinstance(x, set) else str(x))
        rules['consequents'] = rules['consequents'].apply(
            lambda x: ', '.join(x) if isinstance(x, list) or isinstance(x, set) else str(x))

        #draw a scatter plot using Plotly
        fig = px.scatter(
            rules,x='support', y='confidence',size='lift',color='lift',
            hover_data={'antecedents': True,'consequents': True,'support': True,'confidence': True,'lift': True},
            title='Interactive Scatter Plot of Association Rules',
            labels={'support': 'Support','confidence': 'Confidence','lift': 'Lift','antecedents': 'Antecedents','consequents': 'Consequents' },
            color_continuous_scale='Viridis')

        fig.update_layout( width=1000,height=700,title_font_size=24)

        # Display the interactive plot in Streamlit
        st.plotly_chart(fig, use_container_width=True)

# Loop to create a button for each option
selected_option = st.sidebar.radio("Navigate", options)

if selected_option == "Visualization":
    show_visualization()
elif selected_option == "Books":
    show_books()
elif selected_option == "Search Books":
    show_search_books()
elif selected_option == "Analysis":
    show_analysis()
