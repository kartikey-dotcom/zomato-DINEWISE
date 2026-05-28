import streamlit as st
import os
import sys
from pathlib import Path

from src.config import get_settings
from src.data.repository import RestaurantRepository
from src.services.recommendation_service import build_recommendation_service, RecommendationService
from src.models.preferences import UserPreferences
from src.data import run_pipeline

@st.cache_resource
def get_cached_repository(data_path: Path) -> RestaurantRepository:
    repository = RestaurantRepository()
    repository.load(data_path)
    return repository

# 1. Page Configuration & Custom CSS Injection
st.set_page_config(
    page_title="DineWise",
    page_icon="🍴",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# Custom DineWise Crimson Theme styling
st.markdown(
    """
    <style>
    /* Global branding styles */
    .brand-title {
        color: #D32323;
        font-family: 'Outfit', 'Inter', sans-serif;
        font-weight: 800;
        font-size: 2.2rem;
        display: inline-block;
        vertical-align: middle;
        margin: 0;
    }
    .brand-subtitle {
        color: #6B7280;
        font-size: 0.95rem;
        margin-top: -5px;
        margin-bottom: 25px;
    }
    .fork-icon {
        color: #D32323;
        font-size: 2rem;
        display: inline-block;
        vertical-align: middle;
        margin-right: 10px;
    }
    
    /* Center container titles */
    .find-perfect-title {
        font-family: 'Outfit', 'Inter', sans-serif;
        font-weight: 700;
        font-size: 1.8rem;
        color: #111827;
        margin-top: 10px;
        margin-bottom: 20px;
    }
    
    /* Custom Styled Cards matching image 2 */
    .restaurant-card {
        background-color: #FFFFFF;
        border: 1px solid #E5E7EB;
        border-radius: 8px;
        padding: 20px;
        margin-bottom: 20px;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
    }
    
    .card-img-placeholder {
        background-color: #E5E7EB;
        height: 120px;
        border-radius: 6px;
        margin-bottom: 15px;
        display: flex;
        align-items: center;
        justify-content: center;
        color: #9CA3AF;
        font-size: 3rem;
    }
    
    .card-header-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 5px;
    }
    
    .card-title {
        font-size: 1.25rem;
        font-weight: 700;
        color: #111827;
        margin: 0;
    }
    
    .rating-badge {
        background-color: #FEF3C7;
        color: #D97706;
        padding: 4px 10px;
        border-radius: 4px;
        font-size: 0.9rem;
        font-weight: 700;
    }
    
    .card-metadata {
        font-size: 0.9rem;
        color: #6B7280;
        margin-bottom: 12px;
    }
    
    .explanation-box {
        border-left: 3px solid #D32323;
        background-color: #FEF2F2;
        padding: 12px 16px;
        border-radius: 0 6px 6px 0;
        font-size: 0.95rem;
        font-style: italic;
        color: #374151;
        line-height: 1.4;
    }
    
    /* AI Summary box styling */
    .summary-box {
        background-color: #F9FAFB;
        border: 1px solid #E5E7EB;
        border-radius: 8px;
        padding: 16px 20px;
        margin-bottom: 25px;
        color: #374151;
        font-size: 1rem;
        line-height: 1.5;
        display: flex;
        align-items: flex-start;
    }
    .summary-icon {
        font-size: 1.3rem;
        color: #D32323;
        margin-right: 12px;
        margin-top: 2px;
    }
    
    /* Customize default streamlit buttons to DineWise Crimson */
    div.stButton > button:first-child {
        background-color: #D32323;
        color: white;
        border: none;
        padding: 10px 24px;
        font-size: 1rem;
        font-weight: 600;
        border-radius: 6px;
        width: 100%;
        transition: all 0.2s ease;
    }
    div.stButton > button:first-child:hover {
        background-color: #B21B1B;
        color: white;
    }
    
    /* Segmented-style controls indicator (represented beautifully) */
    .highlight-band {
        background-color: #FEF2F2;
        border: 1px solid #FCA5A5;
        color: #B91C1C;
        padding: 6px 12px;
        border-radius: 4px;
        font-weight: 600;
        display: inline-block;
        margin-top: 5px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# 2. DineWise Brand Header
st.markdown(
    """
    <div style="text-align: center; margin-top: 10px;">
        <span class="fork-icon">🍴</span>
        <h1 class="brand-title">DineWise</h1>
        <div class="brand-subtitle">AI Restaurant Recommender</div>
    </div>
    """,
    unsafe_allow_html=True,
)

# 3. Load Settings & Check Ingestion State
settings = get_settings()

if not settings.data_path.exists():
    st.info("📥 Bootstrapping Zomato dataset (downloading, cleaning, and caching)... This happens only once and takes ~30-45s.")
    with st.spinner("Processing dataset from Hugging Face... Please wait."):
        try:
            settings.data_path.parent.mkdir(parents=True, exist_ok=True)
            run_pipeline.run(force_refresh=True)
            st.success("🎉 Dataset bootstrapped successfully! Loading application...")
            st.rerun()
        except Exception as e:
            st.error(f"Failed to bootstrap dataset: {e}")
            st.stop()

# Load repository (cached)
try:
    repo = get_cached_repository(settings.data_path)
except Exception as e:
    st.error(f"Error loading restaurant repository: {e}")
    st.stop()

# Instantiate service
service = build_recommendation_service(repository=repo, settings=settings)

# 4. Filter Panel Form Container ("Find Your Match")
st.markdown("<h2 class=\"find-perfect-title\">Find Your Match</h2>", unsafe_allow_html=True)

with st.container(border=True):
    # Location Selector (Populated from unique dataset localities)
    localities = repo.get_locations()
    
    # Select index for default neighborhood if present
    default_loc_idx = 0
    for idx, loc in enumerate(localities):
        if loc.lower() in {"indiranagar", "bellandur", "koramangala"}:
            default_loc_idx = idx
            break
            
    selected_locality = st.selectbox(
        "Location",
        options=localities,
        index=default_loc_idx,
        help="Select a neighborhood or city area"
    )
    
    # Budget segmented selection
    budget_choice = st.radio(
        "Budget",
        options=["Low", "Medium", "High"],
        index=1,
        horizontal=True,
        help="Low = budget-friendly, Medium = mid-range, High = premium dining"
    )
    
    # Cuisine text input
    cuisine_input = st.text_input(
        "Cuisine",
        value="Italian",
        placeholder="e.g. Italian, Chinese, North Indian, Mughlai..."
    )
    
    # Minimum Rating Slider (Matching star slider in Image 2)
    min_rating = st.slider(
        "Minimum Rating",
        min_value=0.0,
        max_value=5.0,
        value=4.0,
        step=0.1,
        format="%f ★"
    )
    
    # Additional Preferences
    additional_input = st.text_input(
        "Additional Preferences",
        value="family-friendly",
        placeholder="e.g. child-friendly, outdoor seating, quick service..."
    )
    
    # Search submit button
    submit_clicked = st.button("Find Matches")

# 5. Recommendation Results Stream
if submit_clicked:
    # Build User Preferences model
    try:
        preferences = UserPreferences(
            location=selected_locality,
            budget=budget_choice.lower(),
            cuisine=cuisine_input if cuisine_input.strip() else None,
            min_rating=min_rating,
            additional=additional_input if additional_input.strip() else None
        )
    except Exception as e:
        st.error(f"Invalid inputs: {e}")
        st.stop()
        
    st.markdown("<h3 style='margin-top:25px; margin-bottom:15px; color:#111827;'>Your Recommendations</h3>", unsafe_allow_html=True)
    
    with st.spinner("Consulting DineWise AI recommender engine..."):
        response = service.get_recommendations(preferences)
        
    # Check if empty states
    if not response.items:
        st.info("ℹ️ " + (response.metadata.get("message") or "No restaurants matched your filters. Try relaxing rating or budget constraints!"))
        st.stop()
        
    # Render Fallback Banner if LLM failed
    if response.metadata.get("fallback"):
        st.warning("⚠️ Offline Fallback Mode: AI explanations are temporarily offline. Displaying matches ranked directly by rating.")
        
    # Render AI Summary if present (matching star summary box in Image 2)
    if response.summary:
        st.markdown(
            f"""
            <div class="summary-box">
                <span class="summary-icon">✦</span>
                <div>{response.summary}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        
    # Map Cuisine to image placeholders Emojis for a premium touch
    def get_cuisine_emoji(cuisine_str: str) -> str:
        c = cuisine_str.lower()
        if "pizza" in c or "italian" in c or "pasta" in c:
            return "🍕"
        elif "chinese" in c or "noodle" in c or "asian" in c:
            return "🍜"
        elif "burger" in c or "fast" in c:
            return "🍔"
        elif "dessert" in c or "sweet" in c or "bakery" in c:
            return "🍰"
        elif "cafe" in c or "coffee" in c:
            return "☕"
        elif "beer" in c or "pub" in c or "bar" in c:
            return "🍺"
        elif "veg" in c or "salad" in c or "healthy" in c:
            return "🥗"
        elif "south indian" in c:
            return "🍛"
        return "🍽️"

    # Render top recommendation cards (Matching Toscano, Chianti, etc. from Image 2)
    for item in response.items:
        emoji = get_cuisine_emoji(item.cuisine)
        
        # Format estimated cost display
        cost_display = f"₹{int(item.estimated_cost):,} for two" if isinstance(item.estimated_cost, (int, float)) else str(item.estimated_cost)
        
        st.markdown(
            f"""
            <div class="restaurant-card">
                <!-- Large graphic placeholder -->
                <div class="card-img-placeholder">
                    {emoji}
                </div>
                <!-- Card Header -->
                <div class="card-header-row">
                    <div class="card-title">{item.rank}. {item.name}</div>
                    <div class="rating-badge">★ {item.rating:.1f}</div>
                </div>
                <!-- Metadata line -->
                <div class="card-metadata">
                    {item.cuisine} · {selected_locality} · {cost_display}
                </div>
                <!-- AI Explanation Box -->
                <div class="explanation-box">
                    "{item.explanation}"
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

# 6. Navigation Bar at the Bottom for Visual Completeness (Matching mockups)
st.markdown("<hr style='margin-top: 40px; border-color:#E5E7EB;'>", unsafe_allow_html=True)
st.markdown(
    """
    <div style="display: flex; justify-content: space-around; text-align: center; color: #6B7280; font-size: 0.85rem; padding-bottom: 20px;">
        <div>
            <div style="font-size:1.2rem; color:#D32323;">🧭</div>
            <div style="color:#D32323; font-weight:600;">Discover</div>
        </div>
        <div>
            <div style="font-size:1.2rem;">🔖</div>
            <div>Saved</div>
        </div>
        <div>
            <div style="font-size:1.2rem;">🕒</div>
            <div>Activity</div>
        </div>
        <div>
            <div style="font-size:1.2rem;">⚙️</div>
            <div>Settings</div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)
