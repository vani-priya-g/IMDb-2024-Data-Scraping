import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import plotly.express as px
import numpy as np
import pymysql
from sqlalchemy import create_engine
from streamlit_option_menu import option_menu

# Connect to MySQL database
def get_connection():
    user = '2REwzv5VwDdF1d2.root'
    password = '5FVuwLbpjH2oFJFV'
    host = 'gateway01.ap-southeast-1.prod.aws.tidbcloud.com'
    port = '4000'
    database = 'imdb2024_db'
    engine = create_engine("mysql+mysqlconnector://2REwzv5VwDdF1d2.root:5FVuwLbpjH2oFJFV@gateway01.ap-southeast-1.prod.aws.tidbcloud.com:4000/imdb2024_db")
    return engine

def load_data():
    try:
        engine = get_connection()
        query = "SELECT * FROM movies_2024"  # Adjust to your actual table/fields
        df = pd.read_sql(query, engine)
        df['Duration_hours'] = df['Duration'] / 60
        return df
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return pd.DataFrame()  # Return empty DataFrame if loading fails

df = load_data()
if df.empty:
    st.stop()

# ---- SIDEBAR FILTERS ----
st.sidebar.header("🔍 Filters")

# Genre selection
genres = ["All"] + sorted(df['Genre'].dropna().unique())
selected_genre = st.sidebar.selectbox("🎭 Select Genre", genres)

# Votes range
votes_min, votes_max = int(df['Votes'].min()), int(df['Votes'].max())
vote_range = st.sidebar.slider("🗳️ Votes Range", min_value=votes_min, max_value=votes_max,
                               value=(10000, votes_max), step=1000)

# Rating range
rating_min, rating_max = float(df['Rating'].min()), float(df['Rating'].max())
rating_range = st.sidebar.slider("⭐ Rating Range", min_value=rating_min, max_value=rating_max,
                                 value=(rating_min, rating_max), step=0.1)

# Duration range
duration_min, duration_max = int(df['Duration'].min()), int(df['Duration'].max())
duration_range = st.sidebar.slider("⏱️ Duration (min)", min_value=duration_min, max_value=duration_max,
                                   value=(duration_min, duration_max), step=5)

# Apply filters
filtered_df = df.copy()

if selected_genre != "All":
    filtered_df = filtered_df[filtered_df['Genre'] == selected_genre]

filtered_df = filtered_df[
    (filtered_df['Votes'] >= vote_range[0]) & (filtered_df['Votes'] <= vote_range[1]) &
    (filtered_df['Rating'] >= rating_range[0]) & (filtered_df['Rating'] <= rating_range[1]) &
    (filtered_df['Duration'] >= duration_range[0]) & (filtered_df['Duration'] <= duration_range[1])
]

# ---- NAVIGATION MENU ----
selected = option_menu(
    menu_title=None,
    options=[
        "Overview", "Top Movies", "Genre Analysis", 
        "Durations", "Ratings", "Votes Correlation"
    ],
    icons=["house", "star", "bar-chart", "clock", "graph-up", "scatter-chart"],
    orientation="horizontal"
)

# ---- OVERVIEW ----
if selected == "Overview":
    st.title("🎬 IMDb 2024 - Movie Data Dashboard")
    st.markdown("Explore trends in movie ratings, genres, votes and durations for 2024.")
    st.metric("Total Movies", len(df))
    st.metric("Genres Available", df['Genre'].nunique())
    st.metric("Highest Rated Movie", df.loc[df['Rating'].idxmax()]['Title'])

# ---- TOP MOVIES ----
elif selected == "Top Movies":
    st.header("⭐ Top 10 Movies by Rating and Votes")
    top_movies = filtered_df.sort_values(by=['Rating', 'Votes'], ascending=False).head(10)
    st.dataframe(top_movies[['Title', 'Rating', 'Votes']])

# ---- GENRE ANALYSIS ----
elif selected == "Genre Analysis":
    st.header("🎭 Genre Distribution")
    genre_counts = df['Genre'].value_counts()
    st.plotly_chart(px.bar(
        x=genre_counts.index, y=genre_counts.values,
        labels={'x': 'Genre', 'y': 'Count'},
        title="Number of Movies per Genre"
    ))

    st.subheader("📈 Average Votes by Genre")
    avg_votes = df.groupby('Genre')['Votes'].mean().sort_values()
    st.plotly_chart(px.bar(
        x=avg_votes.index, y=avg_votes.values,
        labels={'x': 'Genre', 'y': 'Avg Votes'}
    ))

    st.subheader("🏆 Top-Rated Movie by Genre")
    top_by_genre = df.loc[df.groupby('Genre')['Rating'].idxmax()][['Genre', 'Title', 'Rating']]
    st.dataframe(top_by_genre)

# ---- DURATION ----
elif selected == "Durations":
    st.header("⏱️ Average Duration by Genre")
    avg_duration = df.groupby('Genre')['Duration'].mean().sort_values()
    st.plotly_chart(px.bar(
        x=avg_duration.index, y=avg_duration.values,
        labels={'x': 'Genre', 'y': 'Avg Duration (min)'}
    ))

    st.subheader("🎞️ Duration Extremes")
    shortest = df.loc[df['Duration'].idxmin()]
    longest = df.loc[df['Duration'].idxmax()]
    st.metric("Shortest Movie", f"{shortest['Title']} ({shortest['Duration']} min)")
    st.metric("Longest Movie", f"{longest['Title']} ({longest['Duration']} min)")

# ---- RATINGS ----
elif selected == "Ratings":
    st.header("⭐ Rating Distribution")
    fig, ax = plt.subplots()
    sns.histplot(df['Rating'], bins=20, kde=True, ax=ax)
    st.pyplot(fig)

    st.subheader("🔥 Ratings by Genre Heatmap")
    rating_heatmap = df.groupby('Genre')['Rating'].mean().reset_index()
    pivot = rating_heatmap.pivot_table(values='Rating', index='Genre')
    fig, ax = plt.subplots()
    sns.heatmap(pivot, annot=True, cmap="YlGnBu", ax=ax)
    st.pyplot(fig)

# ---- VOTE CORRELATION ----
elif selected == "Votes Correlation":
    st.header("📊 Correlation: Rating vs Votes")
    fig = px.scatter(
        df, x='Votes', y='Rating',
        hover_data=['Title'],
        title="Ratings vs Votes",
        trendline="ols"
    )
    st.plotly_chart(fig)

# ---- END ----
st.markdown("---")
st.caption("Built with ❤️ using Streamlit | IMDb 2024 Data")