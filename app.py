import streamlit as st
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# ---------------- PAGE CONFIG ----------------
st.set_page_config(
    page_title="AI Product Recommender",
    page_icon="🛒",
    layout="wide"
)

# ---------------- IMAGE SIZE FIX ----------------
st.markdown("""
<style>
img {
    height: 220px;
    object-fit: contain;
}
</style>
""", unsafe_allow_html=True)

# ---------------- LOAD DATA ----------------
@st.cache_data
def load_data():
    trending = pd.read_csv("models/trending_products.csv")
    data = pd.read_csv("models/clean_data.csv")
    return trending, data

trending_products, train_data = load_data()

# ---------------- FIX IMAGE URLS ----------------
train_data["ImageURL"] = train_data["ImageURL"].astype(str).apply(lambda x: x.split("|")[0])
trending_products["ImageURL"] = trending_products["ImageURL"].astype(str).apply(lambda x: x.split("|")[0])

# ---------------- FEATURE ENGINEERING ----------------
train_data["Tags"] = (
    train_data["Category"].astype(str) + " " +
    train_data["Brand"].astype(str) + " " +
    train_data["Name"].astype(str)
)

# ---------------- BUILD SIMILARITY MATRIX ----------------
@st.cache_resource
def build_similarity(data):

    tfidf = TfidfVectorizer(stop_words="english")

    tfidf_matrix = tfidf.fit_transform(data["Tags"])

    similarity = cosine_similarity(tfidf_matrix)

    return similarity

similarity_matrix = build_similarity(train_data)

# ---------------- RECOMMEND FUNCTION ----------------
def recommend(product):

    if product not in train_data["Name"].values:
        return pd.DataFrame()

    index = train_data[train_data["Name"] == product].index[0]

    scores = list(enumerate(similarity_matrix[index]))

    scores = sorted(scores, key=lambda x: x[1], reverse=True)

    scores = scores[1:21]  # always generate top 20

    indices = [i[0] for i in scores]

    results = train_data.iloc[indices][
        ["Name","Brand","Rating","ReviewCount","ImageURL"]
    ]

    results["Similarity"] = [round(s[1]*100,2) for s in scores]

    return results

# ---------------- SESSION STATE ----------------
if "history" not in st.session_state:
    st.session_state.history = []

# ---------------- TITLE ----------------
st.title("🛒 AI-Powered Product Recommendation System")


st.divider()

# ---------------- SEARCH SECTION ----------------
col1, col2, col3 = st.columns([4,1,1])

with col1:
    product_name = st.selectbox(
        "Search Product",
        train_data["Name"].unique()
    )

with col2:
    num_recommend = st.slider(
        "Recommendations",
        1,
        10,
        5
    )

with col3:
    recommend_button = st.button("Recommend")

# ---------------- RECOMMENDATION SECTION ----------------
if recommend_button:

    results = recommend(product_name)

    results = results.head(num_recommend)

    st.session_state.history.append(product_name)

    if results.empty:
        st.warning("Product not found.")

    else:

        st.subheader("🎯 Recommended Products")

        cols = st.columns(num_recommend)

        for i, col in enumerate(cols):

            with col:

                default_img = "https://via.placeholder.com/300?text=No+Image"

                img = results.iloc[i]["ImageURL"]

                if pd.isna(img) or img == "":
                    img = default_img

                with st.container(border=True):

                    st.image(img, use_container_width=True)

                    st.write(f"**{results.iloc[i]['Name']}**")

                    st.write(f"⭐ Rating: {results.iloc[i]['Rating']}")

                    st.write(f"Brand: {results.iloc[i]['Brand']}")

                    st.write(f"Reviews: {results.iloc[i]['ReviewCount']}")

                    st.write(f"Similarity: {results.iloc[i]['Similarity']}%")

                    st.progress(int(results.iloc[i]["Similarity"]))

# ---------------- TRENDING PRODUCTS ----------------
st.divider()

st.header("🔥 Trending Products")

cols = st.columns(4)

for i, col in enumerate(cols):

    with col:

        default_img = "https://via.placeholder.com/300?text=No+Image"

        img = trending_products.iloc[i]["ImageURL"]

        if pd.isna(img) or img == "":
            img = default_img

        with st.container(border=True):

            st.image(img, use_container_width=True)

            st.write(
                f"**{trending_products.iloc[i]['Name']}**"
            )

            if "Rating" in trending_products.columns:

                st.write(
                    f"⭐ {trending_products.iloc[i]['Rating']}"
                )

# ---------------- SEARCH HISTORY ----------------
if st.session_state.history:

    st.divider()

    st.subheader("🕘 Your Search History")

    for item in st.session_state.history[-5:]:

        st.write("•", item)