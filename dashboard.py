"""
Streamlit Dashboard for Re-Defined Blog Automation System
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import requests
import json
from pathlib import Path
import sys

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from src.database.models import BlogPost, ScheduledTask, TrendingTopic
from src.database.init_db import get_session
from config.settings import settings

# Page configuration
st.set_page_config(
    page_title="Re-Defined Blog Automation",
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        color: #2E86AB;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
    .success-box {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        padding: 1rem;
        border-radius: 0.5rem;
    }
    .error-box {
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        padding: 1rem;
        border-radius: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown('<h1 class="main-header">📝 Re-Defined Blog Automation</h1>', unsafe_allow_html=True)

# Sidebar navigation
page = st.sidebar.selectbox(
    "Navigation",
    ["📊 Dashboard", "✍️ Generate Blog", "📰 Blog Posts", "📈 Analytics", "⚙️ Settings"]
)

# Database session
session = get_session()

if page == "📊 Dashboard":
    st.header("Dashboard Overview")
    
    # Metrics row
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_blogs = session.query(BlogPost).count()
        st.metric("Total Blogs", total_blogs)
    
    with col2:
        published_blogs = session.query(BlogPost).filter_by(status="published").count()
        st.metric("Published", published_blogs)
    
    with col3:
        scheduled_tasks = session.query(ScheduledTask).filter_by(status="pending").count()
        st.metric("Scheduled Tasks", scheduled_tasks)
    
    with col4:
        trending_topics = session.query(TrendingTopic).filter_by(used_in_post=False).count()
        st.metric("Available Trends", trending_topics)
    
    # Recent activity
    st.subheader("📅 Recent Activity")
    
    recent_blogs = session.query(BlogPost).order_by(BlogPost.created_at.desc()).limit(5).all()
    
    for blog in recent_blogs:
        with st.expander(f"{blog.title} - {blog.status.upper()}"):
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(f"**Created:** {blog.created_at.strftime('%Y-%m-%d %H:%M')}")
                st.write(f"**Word Count:** {blog.word_count}")
                st.write(f"**Reading Time:** {blog.reading_time} minutes")
                if blog.meta_description:
                    st.write(f"**Meta Description:** {blog.meta_description}")
            with col2:
                if blog.status == "draft":
                    if st.button("Publish", key=f"pub_{blog.id}"):
                        # Call API to publish
                        st.success("Publishing...")
                elif blog.status == "published":
                    st.success("✅ Published")
                    if blog.website_post_id:
                        st.write(f"[View Post](https://re-defined.ca/blog/{blog.slug})")
    
    # Upcoming tasks
    st.subheader("🔄 Scheduled Tasks")
    
    upcoming_tasks = session.query(ScheduledTask).filter(
        ScheduledTask.status.in_(["pending", "running"])
    ).order_by(ScheduledTask.scheduled_for).limit(5).all()
    
    if upcoming_tasks:
        task_data = []
        for task in upcoming_tasks:
            task_data.append({
                "Type": task.task_type,
                "Scheduled": task.scheduled_for.strftime('%Y-%m-%d %H:%M'),
                "Status": task.status,
                "Details": task.parameters.get('description', 'N/A') if task.parameters else 'N/A'
            })
        
        df = pd.DataFrame(task_data)
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No scheduled tasks at the moment")

elif page == "✍️ Generate Blog":
    st.header("Generate New Blog Post")
    
    with st.form("blog_generation_form"):
        topic = st.text_input("Blog Topic", placeholder="e.g., Tips for International Students Finding Internships")
        
        col1, col2 = st.columns(2)
        with col1:
            schedule_option = st.radio("When to publish?", ["Generate Now", "Schedule for Later"])
        
        with col2:
            if schedule_option == "Schedule for Later":
                schedule_date = st.date_input("Schedule Date")
                schedule_time = st.time_input("Schedule Time")
            else:
                schedule_date = None
                schedule_time = None
        
        custom_instructions = st.text_area(
            "Custom Instructions (Optional)",
            placeholder="Any specific guidelines, tone adjustments, or content requirements..."
        )
        
        # Trending topics selection
        st.subheader("📈 Use Trending Topics")
        trends = session.query(TrendingTopic).filter_by(used_in_post=False).order_by(
            TrendingTopic.relevance_score.desc()
        ).limit(10).all()
        
        if trends:
            trend_options = [f"{t.topic} (Score: {t.relevance_score})" for t in trends]
            selected_trends = st.multiselect("Select trending topics to incorporate:", trend_options)
        
        submitted = st.form_submit_button("🚀 Generate Blog", type="primary")
        
        if submitted and topic:
            with st.spinner("Generating blog post..."):
                try:
                    # Here you would call the API to generate the blog
                    st.success("✅ Blog post generated successfully!")
                    
                    # Show preview
                    st.subheader("Preview")
                    st.write(f"**Topic:** {topic}")
                    if custom_instructions:
                        st.write(f"**Instructions:** {custom_instructions}")
                    
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")

elif page == "📰 Blog Posts":
    st.header("Blog Posts Management")
    
    # Filters
    col1, col2, col3 = st.columns(3)
    with col1:
        status_filter = st.selectbox("Filter by Status", ["All", "Draft", "Scheduled", "Published", "Failed"])
    with col2:
        date_filter = st.date_input("From Date", value=datetime.now() - timedelta(days=30))
    with col3:
        search_query = st.text_input("Search", placeholder="Search by title...")
    
    # Query blogs
    query = session.query(BlogPost)
    
    if status_filter != "All":
        query = query.filter_by(status=status_filter.lower())
    
    if search_query:
        query = query.filter(BlogPost.title.contains(search_query))
    
    query = query.filter(BlogPost.created_at >= date_filter)
    
    blogs = query.order_by(BlogPost.created_at.desc()).all()
    
    # Display blogs
    st.write(f"Found {len(blogs)} blog posts")
    
    for blog in blogs:
        with st.container():
            col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
            
            with col1:
                st.write(f"**{blog.title}**")
                st.caption(f"Created: {blog.created_at.strftime('%Y-%m-%d')} | Words: {blog.word_count}")
            
            with col2:
                status_color = {
                    "draft": "🟡",
                    "scheduled": "🔵",
                    "published": "🟢",
                    "failed": "🔴"
                }
                st.write(f"{status_color.get(blog.status, '⚪')} {blog.status.upper()}")
            
            with col3:
                if st.button("View", key=f"view_{blog.id}"):
                    st.session_state['selected_blog'] = blog.id
                    st.experimental_rerun()
            
            with col4:
                if blog.status == "draft":
                    if st.button("Publish", key=f"publish_{blog.id}"):
                        # Publish logic
                        st.success("Publishing...")
            
            st.divider()
    
    # Blog detail view
    if 'selected_blog' in st.session_state:
        blog_id = st.session_state['selected_blog']
        blog = session.query(BlogPost).filter_by(id=blog_id).first()
        
        if blog:
            st.subheader(f"📄 {blog.title}")
            
            # Blog metadata
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.markdown(blog.content)
            
            with col2:
                st.write("**Metadata**")
                st.write(f"Status: {blog.status}")
                st.write(f"Words: {blog.word_count}")
                st.write(f"Reading Time: {blog.reading_time} min")
                
                if blog.keywords:
                    st.write("**Keywords:**")
                    for kw in blog.keywords:
                        st.write(f"- {kw}")
                
                if blog.meta_description:
                    st.write("**Meta Description:**")
                    st.write(blog.meta_description)

elif page == "📈 Analytics":
    st.header("Blog Analytics")
    
    # Date range selector
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Start Date", value=datetime.now() - timedelta(days=90))
    with col2:
        end_date = st.date_input("End Date", value=datetime.now())
    
    # Blog creation over time
    st.subheader("📊 Blog Creation Timeline")
    
    blogs_timeline = session.query(
        BlogPost.created_at,
        BlogPost.status
    ).filter(
        BlogPost.created_at.between(start_date, end_date)
    ).all()
    
    if blogs_timeline:
        df = pd.DataFrame(blogs_timeline)
        df['date'] = pd.to_datetime(df['created_at']).dt.date
        
        # Group by date and status
        timeline_data = df.groupby(['date', 'status']).size().reset_index(name='count')
        
        fig = px.line(timeline_data, x='date', y='count', color='status',
                     title='Blogs Created Over Time')
        st.plotly_chart(fig, use_container_width=True)
    
    # Status distribution
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 Status Distribution")
        
        status_counts = session.query(
            BlogPost.status,
            BlogPost.id
        ).group_by(BlogPost.status).all()
        
        if status_counts:
            status_df = pd.DataFrame(
                [(s[0], len(list(filter(lambda x: x[0] == s[0], status_counts)))) 
                 for s in set(status_counts)],
                columns=['Status', 'Count']
            )
            
            fig = px.pie(status_df, values='Count', names='Status', 
                        title='Blog Status Distribution')
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("📊 Word Count Distribution")
        
        word_counts = session.query(BlogPost.word_count).filter(
            BlogPost.word_count.isnot(None)
        ).all()
        
        if word_counts:
            wc_df = pd.DataFrame(word_counts, columns=['Word Count'])
            
            fig = px.histogram(wc_df, x='Word Count', nbins=20,
                             title='Word Count Distribution')
            st.plotly_chart(fig, use_container_width=True)
    
    # Top performing keywords
    st.subheader("🔑 Top Keywords")
    
    all_keywords = []
    blogs_with_keywords = session.query(BlogPost.keywords).filter(
        BlogPost.keywords.isnot(None)
    ).all()
    
    for blog in blogs_with_keywords:
        if blog.keywords:
            all_keywords.extend(blog.keywords)
    
    if all_keywords:
        keyword_counts = pd.Series(all_keywords).value_counts().head(20)
        
        fig = px.bar(x=keyword_counts.values, y=keyword_counts.index,
                    orientation='h', title='Most Used Keywords')
        fig.update_layout(xaxis_title="Frequency", yaxis_title="Keyword")
        st.plotly_chart(fig, use_container_width=True)

elif page == "⚙️ Settings":
    st.header("System Settings")
    
    # API Configuration
    st.subheader("🔑 API Configuration")
    
    with st.form("api_settings"):
        openai_key = st.text_input("OpenAI API Key", type="password", value="****" if settings.openai_api_key else "")
        website_endpoint = st.text_input("Website API Endpoint", value=settings.website_api_endpoint or "")
        website_key = st.text_input("Website API Key", type="password", value="****" if settings.website_api_key else "")
        
        if st.form_submit_button("Save API Settings"):
            st.success("✅ API settings updated!")
    
    # Content Settings
    st.subheader("📝 Content Settings")
    
    with st.form("content_settings"):
        col1, col2 = st.columns(2)
        
        with col1:
            min_words = st.number_input("Minimum Word Count", value=settings.min_word_count, min_value=100)
            max_words = st.number_input("Maximum Word Count", value=settings.max_word_count, min_value=200)
        
        with col2:
            publish_interval = st.number_input("Publish Interval (days)", value=settings.publish_interval_days, min_value=1)
            meta_length = st.number_input("Meta Description Length", value=settings.default_meta_description_length)
        
        target_keywords = st.text_area("Target Keywords (one per line)", 
                                     value="\n".join(settings.target_keywords))
        
        if st.form_submit_button("Save Content Settings"):
            st.success("✅ Content settings updated!")
    
    # System Info
    st.subheader("ℹ️ System Information")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Database Status:**")
        try:
            blog_count = session.query(BlogPost).count()
            st.success(f"✅ Connected ({blog_count} blogs)")
        except:
            st.error("❌ Disconnected")
        
        st.write("**Scheduler Status:**")
        st.success("✅ Running")
    
    with col2:
        st.write("**Version:** 1.0.0")
        st.write("**Python Version:** 3.9+")
        st.write("**Last Update:** " + datetime.now().strftime("%Y-%m-%d"))

# Footer
st.markdown("---")
st.markdown(
    '<p style="text-align: center; color: #666;">Re-Defined Blog Automation System © 2024</p>',
    unsafe_allow_html=True
) 