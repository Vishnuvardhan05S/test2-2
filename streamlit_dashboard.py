"""
MFlix Analytics Dashboard
=========================
An interactive dashboard for exploring the MFlix movie database on Azure Cosmos DB.

This dashboard provides:
- Overview metrics and KPIs
- Movie analytics by genre and ratings
- Temporal trends in movie production and ratings
- Geographic visualization of theater locations
- User engagement analysis
- Interactive search and filtering capabilities
"""

import streamlit as st
import pymongo
from pymongo import MongoClient
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import folium
from streamlit_folium import folium_static
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Page configuration
st.set_page_config(
    page_title="MFlix Analytics Dashboard",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        padding: 1rem 0;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 2rem;
    }
</style>
""", unsafe_allow_html=True)

# Database connection with caching
@st.cache_resource
def get_database_connection():
    """Connect to Azure Cosmos DB"""
    CONNECTION_STRING = "mongodb+srv://mflixadmin:mongodb%40123@assingment-db.global.mongocluster.cosmos.azure.com/?tls=true&authMechanism=SCRAM-SHA-256&retrywrites=false&maxIdleTimeMS=120000&tlsAllowInvalidCertificates=true"
    try:
        client = MongoClient(
            CONNECTION_STRING,
            tls=True,
            tlsAllowInvalidCertificates=True,
            serverSelectionTimeoutMS=60000,
            connectTimeoutMS=60000,
            socketTimeoutMS=60000
        )
        # Note: database name is case-sensitive - use lowercase 'sample_mflix'
        db = client['sample_mflix']
        return db
    except Exception as e:
        st.error(f"Database connection failed: {e}")
        return None

# Data loading functions with caching
@st.cache_data(ttl=3600)
def get_overview_stats(_db):
    """Get overview statistics"""
    stats = {
        'total_movies': _db['movies'].count_documents({}),
        'total_users': _db['users'].count_documents({}),
        'total_comments': _db['comments'].count_documents({}),
        'total_theaters': _db['theaters'].count_documents({})
    }
    
    # Average rating
    avg_rating_pipeline = [
        {"$match": {"imdb.rating": {"$exists": True, "$ne": None}}},
        {"$group": {"_id": None, "avg_rating": {"$avg": "$imdb.rating"}}}
    ]
    avg_rating = list(_db['movies'].aggregate(avg_rating_pipeline))
    stats['avg_rating'] = avg_rating[0]['avg_rating'] if avg_rating else 0
    
    return stats

@st.cache_data(ttl=3600)
def get_genre_distribution(_db):
    """Get genre distribution"""
    pipeline = [
        {"$match": {"genres": {"$exists": True, "$ne": []}}},
        {"$unwind": "$genres"},
        {"$group": {"_id": "$genres", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 20}
    ]
    data = list(_db['movies'].aggregate(pipeline))
    return pd.DataFrame(data).rename(columns={'_id': 'Genre', 'count': 'Count'})

@st.cache_data(ttl=3600)
def get_rating_distribution(_db):
    """Get IMDb rating distribution"""
    pipeline = [
        {"$match": {"imdb.rating": {"$exists": True, "$ne": None}}},
        {"$project": {"rating": "$imdb.rating"}},
        {"$limit": 10000}
    ]
    data = list(_db['movies'].aggregate(pipeline))
    return pd.DataFrame(data)

@st.cache_data(ttl=3600)
def get_movies_by_decade(_db):
    """Get movies released by decade"""
    pipeline = [
        {"$match": {"year": {"$exists": True, "$ne": None, "$gte": 1900}}},
        {"$project": {"decade": {"$subtract": ["$year", {"$mod": ["$year", 10]}]}}},
        {"$group": {"_id": "$decade", "count": {"$sum": 1}}},
        {"$sort": {"_id": 1}}
    ]
    data = list(_db['movies'].aggregate(pipeline))
    return pd.DataFrame(data).rename(columns={'_id': 'Decade', 'count': 'Count'})

@st.cache_data(ttl=3600)
def get_top_rated_movies(_db, limit=10):
    """Get top rated movies"""
    pipeline = [
        {"$match": {
            "imdb.rating": {"$exists": True, "$ne": None},
            "imdb.votes": {"$gte": 1000}
        }},
        {"$project": {
            "title": 1,
            "year": 1,
            "genres": 1,
            "rating": "$imdb.rating",
            "votes": "$imdb.votes"
        }},
        {"$sort": {"rating": -1}},
        {"$limit": limit}
    ]
    data = list(_db['movies'].aggregate(pipeline))
    return pd.DataFrame(data)

@st.cache_data(ttl=3600)
def get_theater_locations(_db):
    """Get theater locations"""
    pipeline = [
        {"$match": {"location.geo.coordinates": {"$exists": True}}},
        {"$project": {
            "city": "$location.address.city",
            "state": "$location.address.state",
            "coordinates": "$location.geo.coordinates"
        }},
        {"$limit": 500}
    ]
    data = list(_db['theaters'].aggregate(pipeline))
    return data

@st.cache_data(ttl=3600)
def get_comment_trends(_db):
    """Get comment activity over time"""
    pipeline = [
        {"$match": {"date": {"$exists": True}}},
        {"$project": {
            "year": {"$year": "$date"},
            "month": {"$month": "$date"}
        }},
        {"$group": {
            "_id": {"year": "$year", "month": "$month"},
            "count": {"$sum": 1}
        }},
        {"$sort": {"_id.year": 1, "_id.month": 1}},
        {"$limit": 100}
    ]
    data = list(_db['comments'].aggregate(pipeline))
    if data:
        df = pd.DataFrame(data)
        df['date'] = pd.to_datetime(df['_id'].apply(lambda x: f"{x['year']}-{x['month']}-01"))
        df = df.rename(columns={'count': 'Comments'})
        return df[['date', 'Comments']]
    return pd.DataFrame()

@st.cache_data(ttl=3600)
def search_movies(_db, query, genre_filter=None, year_range=None):
    """Search movies by title"""
    match_condition = {}
    
    if query:
        match_condition["title"] = {"$regex": query, "$options": "i"}
    
    if genre_filter and genre_filter != "All":
        match_condition["genres"] = genre_filter
    
    if year_range:
        match_condition["year"] = {"$gte": year_range[0], "$lte": year_range[1]}
    
    pipeline = [
        {"$match": match_condition},
        {"$project": {
            "title": 1,
            "year": 1,
            "genres": 1,
            "rating": "$imdb.rating",
            "plot": 1
        }},
        {"$limit": 50}
    ]
    
    data = list(_db['movies'].aggregate(pipeline))
    return pd.DataFrame(data)

# Main application
def main():
    # Header
    st.markdown('<div class="main-header">🎬 MFlix Analytics Dashboard</div>', unsafe_allow_html=True)
    st.markdown("---")
    
    # Connect to database
    db = get_database_connection()
    if db is None:
        st.error("❌ Failed to connect to database. Please check your connection settings.")
        return
    
    # Sidebar
    with st.sidebar:
        st.image("https://img.icons8.com/color/96/000000/movie-projector.png", width=100)
        st.title("Navigation")
        page = st.radio(
            "Select a page:",
            ["📊 Overview", "🎬 Movie Analytics", "📈 Temporal Trends", 
             "🗺️ Geographic View", "💬 User Engagement", "🔍 Search Movies"]
        )
        
        st.markdown("---")
        st.markdown("### About")
        st.info("""
        This dashboard provides insights into the MFlix movie database,
        including movie ratings, genres, user engagement, and geographic distribution.
        
        **Data Source**: Azure Cosmos DB
        """)
    
    # Page routing
    if page == "📊 Overview":
        show_overview(db)
    elif page == "🎬 Movie Analytics":
        show_movie_analytics(db)
    elif page == "📈 Temporal Trends":
        show_temporal_trends(db)
    elif page == "🗺️ Geographic View":
        show_geographic_view(db)
    elif page == "💬 User Engagement":
        show_user_engagement(db)
    elif page == "🔍 Search Movies":
        show_search(db)

def show_overview(db):
    """Overview page with key metrics"""
    st.header("📊 Platform Overview")
    
    # Get statistics
    stats = get_overview_stats(db)
    
    # Display metrics
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("Total Movies", f"{stats['total_movies']:,}")
    with col2:
        st.metric("Registered Users", f"{stats['total_users']:,}")
    with col3:
        st.metric("User Comments", f"{stats['total_comments']:,}")
    with col4:
        st.metric("Theaters", f"{stats['total_theaters']:,}")
    with col5:
        st.metric("Avg Rating", f"{stats['avg_rating']:.2f}/10")
    
    st.markdown("---")
    
    # Charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🎭 Top Genres")
        genre_df = get_genre_distribution(db)
        fig = px.bar(genre_df.head(10), x='Count', y='Genre', orientation='h',
                     color='Count', color_continuous_scale='viridis')
        fig.update_layout(height=400, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("⭐ Rating Distribution")
        rating_df = get_rating_distribution(db)
        fig = px.histogram(rating_df, x='rating', nbins=20,
                          labels={'rating': 'IMDb Rating', 'count': 'Number of Movies'})
        fig.update_layout(height=400, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

def show_movie_analytics(db):
    """Movie analytics page"""
    st.header("🎬 Movie Analytics")
    
    tab1, tab2 = st.tabs(["Top Rated Movies", "Genre Analysis"])
    
    with tab1:
        st.subheader("🏆 Top Rated Movies (min. 1000 votes)")
        top_movies = get_top_rated_movies(db, limit=20)
        
        if not top_movies.empty:
            top_movies['genres_str'] = top_movies['genres'].apply(lambda x: ', '.join(x) if isinstance(x, list) else '')
            
            # Display as a nice table
            for idx, row in top_movies.iterrows():
                col1, col2, col3 = st.columns([3, 1, 1])
                with col1:
                    st.write(f"**{idx+1}. {row['title']}** ({row['year']})")
                    st.caption(row['genres_str'])
                with col2:
                    st.metric("Rating", f"{row['rating']:.1f}/10")
                with col3:
                    st.metric("Votes", f"{row['votes']:,}")
                st.markdown("---")
    
    with tab2:
        st.subheader("📊 Genre Performance")
        
        # Genre rating analysis
        pipeline = [
            {"$match": {
                "genres": {"$exists": True, "$ne": []},
                "imdb.rating": {"$exists": True, "$ne": None}
            }},
            {"$unwind": "$genres"},
            {"$group": {
                "_id": "$genres",
                "avg_rating": {"$avg": "$imdb.rating"},
                "count": {"$sum": 1}
            }},
            {"$match": {"count": {"$gte": 50}}},
            {"$sort": {"avg_rating": -1}},
            {"$limit": 15}
        ]
        
        genre_ratings = list(db['movies'].aggregate(pipeline))
        genre_ratings_df = pd.DataFrame(genre_ratings)
        genre_ratings_df.columns = ['Genre', 'Avg Rating', 'Movie Count']
        
        col1, col2 = st.columns(2)
        
        with col1:
            fig = px.bar(genre_ratings_df, x='Avg Rating', y='Genre', orientation='h',
                        color='Avg Rating', color_continuous_scale='rdylgn')
            fig.update_layout(height=500, title="Average Rating by Genre")
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            fig = px.scatter(genre_ratings_df, x='Movie Count', y='Avg Rating',
                           size='Movie Count', color='Avg Rating',
                           hover_data=['Genre'], text='Genre',
                           color_continuous_scale='viridis')
            fig.update_layout(height=500, title="Genre Rating vs Popularity")
            st.plotly_chart(fig, use_container_width=True)

def show_temporal_trends(db):
    """Temporal trends page"""
    st.header("📈 Temporal Trends")
    
    # Movies by decade
    st.subheader("🎬 Movie Production by Decade")
    decade_df = get_movies_by_decade(db)
    
    fig = go.Figure()
    fig.add_trace(go.Bar(x=decade_df['Decade'], y=decade_df['Count'],
                         marker_color='steelblue', name='Movies'))
    fig.add_trace(go.Scatter(x=decade_df['Decade'], y=decade_df['Count'],
                            mode='lines+markers', name='Trend',
                            line=dict(color='red', width=2)))
    fig.update_layout(height=400, xaxis_title='Decade', yaxis_title='Number of Movies')
    st.plotly_chart(fig, use_container_width=True)
    
    # Rating trends
    st.subheader("⭐ Rating Trends Over Time")
    
    pipeline = [
        {"$match": {
            "year": {"$exists": True, "$ne": None, "$gte": 1950},
            "imdb.rating": {"$exists": True, "$ne": None}
        }},
        {"$project": {
            "decade": {"$subtract": ["$year", {"$mod": ["$year", 10]}]},
            "rating": "$imdb.rating"
        }},
        {"$group": {
            "_id": "$decade",
            "avg_rating": {"$avg": "$rating"},
            "count": {"$sum": 1}
        }},
        {"$sort": {"_id": 1}}
    ]
    
    rating_trend = list(db['movies'].aggregate(pipeline))
    rating_trend_df = pd.DataFrame(rating_trend)
    rating_trend_df.columns = ['Decade', 'Avg Rating', 'Count']
    
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(
        go.Scatter(x=rating_trend_df['Decade'], y=rating_trend_df['Avg Rating'],
                  mode='lines+markers', name='Avg Rating', line=dict(color='green', width=3)),
        secondary_y=False
    )
    fig.add_trace(
        go.Bar(x=rating_trend_df['Decade'], y=rating_trend_df['Count'],
              name='Movie Count', marker_color='lightblue', opacity=0.5),
        secondary_y=True
    )
    fig.update_xaxes(title_text="Decade")
    fig.update_yaxes(title_text="Average Rating", secondary_y=False)
    fig.update_yaxes(title_text="Movie Count", secondary_y=True)
    fig.update_layout(height=400)
    st.plotly_chart(fig, use_container_width=True)

def show_geographic_view(db):
    """Geographic visualization page"""
    st.header("🗺️ Theater Geographic Distribution")
    
    st.info("Showing theater locations across the United States")
    
    # Get theater data
    theaters = get_theater_locations(db)
    
    if theaters:
        # Create map centered on US
        m = folium.Map(location=[39.8283, -98.5795], zoom_start=4)
        
        # Add markers
        for theater in theaters[:200]:  # Limit to 200 for performance
            if 'coordinates' in theater and theater['coordinates']:
                coords = theater['coordinates']
                if len(coords) >= 2:
                    # MongoDB stores [longitude, latitude]
                    try:
                        lon, lat = float(coords[0]), float(coords[1])
                        folium.CircleMarker(
                            location=[lat, lon],
                            radius=3,
                            popup=f"{theater.get('city', 'Unknown')}, {theater.get('state', '')}",
                            color='red',
                            fill=True,
                            fillColor='red'
                        ).add_to(m)
                    except:
                        pass
        
        # Display map
        folium_static(m, width=1200, height=600)
        
        # State distribution
        st.subheader("📊 Theaters by State")
        
        pipeline = [
            {"$match": {"location.address.state": {"$exists": True}}},
            {"$group": {"_id": "$location.address.state", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 15}
        ]
        
        state_data = list(db['theaters'].aggregate(pipeline))
        state_df = pd.DataFrame(state_data).rename(columns={'_id': 'State', 'count': 'Count'})
        
        fig = px.bar(state_df, x='State', y='Count', color='Count',
                    color_continuous_scale='reds')
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)

def show_user_engagement(db):
    """User engagement page"""
    st.header("💬 User Engagement Analysis")
    
    stats = get_overview_stats(db)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Comments", f"{stats['total_comments']:,}")
    with col2:
        st.metric("Total Users", f"{stats['total_users']:,}")
    with col3:
        comments_per_user = stats['total_comments'] / stats['total_users'] if stats['total_users'] > 0 else 0
        st.metric("Comments per User", f"{comments_per_user:.2f}")
    
    st.markdown("---")
    
    # Comment trends
    st.subheader("📈 Comment Activity Over Time")
    comment_trends = get_comment_trends(db)
    
    if not comment_trends.empty:
        fig = px.line(comment_trends, x='date', y='Comments',
                     title='User Comments Over Time')
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
    
    # Most commented movies
    st.subheader("🔥 Most Discussed Movies")
    
    pipeline = [
        {"$group": {"_id": "$movie_id", "comment_count": {"$sum": 1}}},
        {"$sort": {"comment_count": -1}},
        {"$limit": 10},
        {"$lookup": {
            "from": "movies",
            "localField": "_id",
            "foreignField": "_id",
            "as": "movie_info"
        }},
        {"$unwind": "$movie_info"},
        {"$project": {
            "title": "$movie_info.title",
            "year": "$movie_info.year",
            "comment_count": 1
        }}
    ]
    
    most_commented = list(db['comments'].aggregate(pipeline))
    
    if most_commented:
        for idx, movie in enumerate(most_commented, 1):
            col1, col2 = st.columns([4, 1])
            with col1:
                st.write(f"**{idx}. {movie['title']}** ({movie.get('year', 'N/A')})")
            with col2:
                st.metric("Comments", movie['comment_count'])

def show_search(db):
    """Search and filter movies"""
    st.header("🔍 Search Movies")
    
    # Get available genres
    genres = ['All'] + sorted(db['movies'].distinct('genres'))
    
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        search_query = st.text_input("Search by title", "")
    with col2:
        genre_filter = st.selectbox("Genre", genres)
    with col3:
        year_range = st.slider("Year Range", 1900, 2020, (1990, 2020))
    
    if st.button("Search") or search_query:
        results = search_movies(db, search_query, 
                              genre_filter if genre_filter != 'All' else None,
                              year_range)
        
        st.subheader(f"Found {len(results)} movies")
        
        if not results.empty:
            for idx, row in results.iterrows():
                with st.expander(f"{row['title']} ({row.get('year', 'N/A')})"):
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.write("**Plot:**")
                        st.write(row.get('plot', 'No plot available'))
                        if 'genres' in row and isinstance(row['genres'], list):
                            st.write("**Genres:**", ', '.join(row['genres']))
                    with col2:
                        if 'rating' in row and row['rating']:
                            st.metric("Rating", f"{row['rating']:.1f}/10")

if __name__ == "__main__":
    main()

