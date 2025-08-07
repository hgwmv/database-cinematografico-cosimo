import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from datetime import datetime
import warnings
import os

warnings.filterwarnings('ignore')

# Configurazione pagina
st.set_page_config(
    page_title="🎬 Database Cinematografico Cosimo",
    page_icon="🎬",
    layout="wide"
)

# Stile CSS personalizzato
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        color: #FF6B6B;
        text-align: center;
        margin-bottom: 2rem;
    }
    .stats-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 10px;
        border-left: 5px solid #FF6B6B;
    }
    .film-card {
        background-color: #ffffff;
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin-bottom: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_database():
    """Carica il database con caching"""
    try:
        df = pd.read_csv('cosimo-film-visti-excel.csv', sep=';', encoding='cp1252')
        
        # Pulizia dati
        df['Rating_Clean'] = pd.to_numeric(df['Rating 10'].str.replace(',', '.'), errors='coerce')
        df['Year_Clean'] = pd.to_numeric(df['Year'], errors='coerce')
        df['Duration_Clean'] = pd.to_numeric(df['Duration'], errors='coerce')
        df['Watch_Date'] = pd.to_datetime(df['Watched Date'], format='%d/%m/%Y', errors='coerce')
        
        return df
    except Exception as e:
        st.error(f"Errore nel caricamento del database: {e}")
        return pd.DataFrame()

def main():
    # Header principale
    st.markdown('<h1 class="main-header">🎬 Database Cinematografico Cosimo</h1>', unsafe_allow_html=True)
    
    # Carica dati
    df = load_database()
    
    if df.empty:
        st.error("Impossibile caricare il database. Assicurati che il file CSV sia presente.")
        return
    
    # Sidebar per navigazione
    st.sidebar.title("🎮 Menu Principale")
    
    menu = st.sidebar.selectbox(
        "Scegli una sezione:",
        [
            "📊 Dashboard Generale",
            "🔍 Ricerca Film",
            "🏆 Top Film",
            "🎭 Analisi Registi",
            "👥 Film in Compagnia",
            "📈 Grafici e Statistiche",
            "📅 Analisi Temporale"
        ]
    )
    
    # Sezioni principali
    if menu == "📊 Dashboard Generale":
        show_dashboard(df)
    elif menu == "🔍 Ricerca Film":
        show_search(df)
    elif menu == "🏆 Top Film":
        show_top_films(df)
    elif menu == "🎭 Analisi Registi":
        show_directors_analysis(df)
    elif menu == "👥 Film in Compagnia":
        show_companions_analysis(df)
    elif menu == "📈 Grafici e Statistiche":
        show_charts(df)
    elif menu == "📅 Analisi Temporale":
        show_temporal_analysis(df)

def show_dashboard(df):
    """Dashboard principale con statistiche generali"""
    st.header("📊 Dashboard Generale")
    
    # Statistiche principali in colonne
    col1, col2, col3, col4 = st.columns(4)
    
    df_valid = df[df['Rating_Clean'].notna()]
    df_features = df[df['Duration_Clean'] >= 40]
    df_shorts = df[df['Duration_Clean'] < 40]
    
    with col1:
        st.markdown("""
        <div class="stats-card">
            <h3>🎬 Film Totali</h3>
            <h2>{:,} film</h2>
        </div>
        """.format(len(df)), unsafe_allow_html=True)
    
    with col2:
        avg_rating = df_valid['Rating_Clean'].mean() if len(df_valid) > 0 else 0
        st.markdown("""
        <div class="stats-card">
            <h3>⭐ Rating Medio</h3>
            <h2>{:.2f}/10</h2>
        </div>
        """.format(avg_rating), unsafe_allow_html=True)
    
    with col3:
        great_movies = len(df_valid[df_valid['Rating_Clean'] >= 7.5])
        st.markdown("""
        <div class="stats-card">
            <h3>🏆 Great Movies</h3>
            <h2>{} film</h2>
        </div>
        """.format(great_movies), unsafe_allow_html=True)
    
    with col4:
        st.markdown("""
        <div class="stats-card">
            <h3>📽️ Lungometraggi</h3>
            <h2>{:,}</h2>
        </div>
        """.format(len(df_features)), unsafe_allow_html=True)
    
    # Ultimi film aggiunti
    st.subheader("🕒 Ultimi Film Aggiunti")
    if len(df[df['Watch_Date'].notna()]) > 0:
        recent_films = df[df['Watch_Date'].notna()].nlargest(10, 'Watch_Date')
        
        for _, film in recent_films.iterrows():
            rating = film['Rating_Clean'] if pd.notna(film['Rating_Clean']) else 'N/A'
            watch_date = film['Watch_Date'].strftime('%d/%m/%Y') if pd.notna(film['Watch_Date']) else 'N/A'
            year = f" ({int(film['Year_Clean'])})" if pd.notna(film['Year_Clean']) else ""
            
            st.markdown(f"""
            <div class="film-card">
                <strong>{film['Name']}</strong>{year} - {film['Director']}<br>
                <small>⭐ {rating}/10 | 📅 Visto: {watch_date}</small>
            </div>
            """, unsafe_allow_html=True)

def show_search(df):
    """Sezione ricerca film"""
    st.header("🔍 Ricerca Film")
    
    # Filtri di ricerca
    col1, col2 = st.columns(2)
    
    with col1:
        search_term = st.text_input("🎬 Cerca per titolo:", "")
        search_director = st.text_input("🎭 Cerca per regista:", "")
    
    with col2:
        search_year = st.number_input("📅 Anno:", min_value=1888, max_value=2030, value=None)
        min_rating = st.slider("⭐ Rating minimo:", 0.0, 10.0, 0.0, 0.5)
    
    # Applica filtri
    filtered_df = df.copy()
    
    if search_term:
        filtered_df = filtered_df[filtered_df['Name'].str.contains(search_term, case=False, na=False)]
    
    if search_director:
        filtered_df = filtered_df[filtered_df['Director'].str.contains(search_director, case=False, na=False)]
    
    if search_year:
        filtered_df = filtered_df[filtered_df['Year_Clean'] == search_year]
    
    if min_rating > 0:
        filtered_df = filtered_df[filtered_df['Rating_Clean'] >= min_rating]
    
    # Risultati
    st.subheader(f"📋 Risultati ({len(filtered_df)} film)")
    
    if len(filtered_df) > 0:
        # Ordina per rating decrescente
        filtered_df = filtered_df.sort_values('Rating_Clean', ascending=False, na_last=True)
        
        for i, (_, film) in enumerate(filtered_df.head(50).iterrows(), 1):
            rating = film['Rating_Clean'] if pd.notna(film['Rating_Clean']) else 'N/A'
            year = f" ({int(film['Year_Clean'])})" if pd.notna(film['Year_Clean']) else ""
            duration = f" | ⏱️ {int(film['Duration_Clean'])}min" if pd.notna(film['Duration_Clean']) else ""
            
            # Evidenzia great movies
            title_style = "font-weight: bold; color: #FF6B6B;" if pd.notna(film['Rating_Clean']) and film['Rating_Clean'] >= 7.5 else ""
            
            st.markdown(f"""
            <div class="film-card">
                <span style="{title_style}">{i}. {film['Name']}</span>{year}<br>
                <small>🎭 {film['Director']} | ⭐ {rating}/10{duration}</small>
            </div>
            """, unsafe_allow_html=True)
        
        if len(filtered_df) > 50:
            st.info(f"Mostrati i primi 50 risultati di {len(filtered_df)}")

def show_top_films(df):
    """Top film per anno/decade"""
    st.header("🏆 Top Film")
    
    tab1, tab2, tab3 = st.tabs(["📅 Per Anno", "📊 Per Decennio", "🌟 Migliori Assoluti"])
    
    with tab1:
        col1, col2 = st.columns(2)
        with col1:
            selected_year = st.selectbox("Scegli anno:", sorted(df['Year_Clean'].dropna().unique(), reverse=True))
        with col2:
            top_n = st.slider("Numero film:", 5, 50, 10)
        
        if selected_year:
            year_films = df[df['Year_Clean'] == selected_year]
            year_films_rated = year_films[year_films['Rating_Clean'].notna()]
            
            if len(year_films_rated) > 0:
                top_films = year_films_rated.nlargest(top_n, 'Rating_Clean')
                
                st.subheader(f"🏆 Top {top_n} Film del {int(selected_year)}")
                
                for i, (_, film) in enumerate(top_films.iterrows(), 1):
                    st.markdown(f"""
                    <div class="film-card">
                        <strong>{i}. {film['Name']}</strong><br>
                        <small>🎭 {film['Director']} | ⭐ {film['Rating_Clean']}/10</small>
                    </div>
                    """, unsafe_allow_html=True)
    
    with tab2:
        decades = list(range(1920, 2030, 10))
        selected_decade = st.selectbox("Scegli decennio:", decades, index=len(decades)-3)
        
        decade_films = df[(df['Year_Clean'] >= selected_decade) & (df['Year_Clean'] < selected_decade + 10)]
        decade_films_rated = decade_films[decade_films['Rating_Clean'].notna()]
        
        if len(decade_films_rated) > 0:
            top_decade = decade_films_rated.nlargest(15, 'Rating_Clean')
            
            st.subheader(f"🏆 Top Film anni {selected_decade}s")
            
            for i, (_, film) in enumerate(top_decade.iterrows(), 1):
                year = f" ({int(film['Year_Clean'])})" if pd.notna(film['Year_Clean']) else ""
                st.markdown(f"""
                <div class="film-card">
                    <strong>{i}. {film['Name']}</strong>{year}<br>
                    <small>🎭 {film['Director']} | ⭐ {film['Rating_Clean']}/10</small>
                </div>
                """, unsafe_allow_html=True)
    
    with tab3:
        df_rated = df[df['Rating_Clean'].notna()]
        top_absolute = df_rated.nlargest(25, 'Rating_Clean')
        
        st.subheader("🌟 I 25 Migliori Film di Sempre")
        
        for i, (_, film) in enumerate(top_absolute.iterrows(), 1):
            year = f" ({int(film['Year_Clean'])})" if pd.notna(film['Year_Clean']) else ""
            st.markdown(f"""
            <div class="film-card">
                <strong>{i}. {film['Name']}</strong>{year}<br>
                <small>🎭 {film['Director']} | ⭐ {film['Rating_Clean']}/10</small>
            </div>
            """, unsafe_allow_html=True)

def show_directors_analysis(df):
    """Analisi registi"""
    st.header("🎭 Analisi Registi")
    
    # Normalizzazione registi (come nel codice originale)
    def normalize_director_name(director):
        if pd.isna(director) or director == '':
            return 'Sconosciuto'
        
        director = str(director).strip()
        
        collaborations = {
            'joel coen': 'Joel & Ethan Coen',
            'ethan coen': 'Joel & Ethan Coen',
            'joel & ethan coen': 'Joel & Ethan Coen',
            'ethan & joel coen': 'Joel & Ethan Coen',
            'coen brothers': 'Joel & Ethan Coen',
            'fratelli coen': 'Joel & Ethan Coen',
        }
        
        director_lower = director.lower()
        for key, value in collaborations.items():
            if key in director_lower:
                return value
        
        return director
    
    df['Director_Normalized'] = df['Director'].apply(normalize_director_name)
    df_features = df[df['Duration_Clean'] >= 40]
    
    tab1, tab2 = st.tabs(["📊 Classifiche Registi", "🔍 Dettagli Regista"])
    
    with tab1:
        # Top registi per numero film
        director_counts = df_features['Director_Normalized'].value_counts()
        director_counts = director_counts[director_counts.index != 'Sconosciuto'].head(20)
        
        st.subheader("🎬 Top 20 Registi per Numero Film")
        
        for i, (director, count) in enumerate(director_counts.items(), 1):
            director_films = df_features[df_features['Director_Normalized'] == director]
            director_films_rated = director_films[director_films['Rating_Clean'].notna()]
            avg_rating = director_films_rated['Rating_Clean'].mean() if len(director_films_rated) > 0 else 0
            great_movies = len(director_films_rated[director_films_rated['Rating_Clean'] >= 7.5])
            
            st.markdown(f"""
            <div class="film-card">
                <strong>{i}. {director}</strong><br>
                <small>🎬 {count} film | ⭐ {avg_rating:.2f}/10 | 🏆 {great_movies} great movies</small>
            </div>
            """, unsafe_allow_html=True)
    
    with tab2:
        # Selezione regista
        directors_list = sorted([d for d in df['Director_Normalized'].unique() if d != 'Sconosciuto'])
        selected_director = st.selectbox("Scegli un regista:", directors_list)
        
        if selected_director:
            director_films = df[df['Director_Normalized'] == selected_director]
            director_films_rated = director_films[director_films['Rating_Clean'].notna()]
            
            # Statistiche regista
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("🎬 Film Totali", len(director_films))
            with col2:
                avg_rating = director_films_rated['Rating_Clean'].mean() if len(director_films_rated) > 0 else 0
                st.metric("⭐ Rating Medio", f"{avg_rating:.2f}/10")
            with col3:
                great_movies = len(director_films_rated[director_films_rated['Rating_Clean'] >= 7.5])
                st.metric("🏆 Great Movies", great_movies)
            
            # Filmografia
            st.subheader(f"🎬 Filmografia di {selected_director}")
            
            if len(director_films_rated) > 0:
                chronological_films = director_films_rated.sort_values('Year_Clean', ascending=True)
                
                for _, film in chronological_films.iterrows():
                    rating = film['Rating_Clean']
                    year = f" ({int(film['Year_Clean'])})" if pd.notna(film['Year_Clean']) else ""
                    duration = f" - {int(film['Duration_Clean'])}min" if pd.notna(film['Duration_Clean']) else ""
                    
                    title_style = "font-weight: bold; color: #FF6B6B;" if rating >= 7.5 else ""
                    
                    st.markdown(f"""
                    <div class="film-card">
                        <span style="{title_style}">{film['Name']}</span>{year}{duration}<br>
                        <small>⭐ {rating}/10</small>
                    </div>
                    """, unsafe_allow_html=True)

def show_companions_analysis(df):
    """Analisi film visti in compagnia"""
    st.header("👥 Film in Compagnia")
    st.info("Questa sezione richiede i tag diario nel CSV per funzionare completamente")
    
    # Placeholder per l'analisi compagni
    st.subheader("🔜 Funzionalità in arrivo")
    st.write("L'analisi dei compagni verrà implementata quando i tag diario saranno disponibili nel dataset.")

def show_charts(df):
    """Grafici e visualizzazioni"""
    st.header("📈 Grafici e Statistiche")
    
    tab1, tab2 = st.tabs(["📊 Distribuzione Rating", "⏱️ Attività nel Tempo"])
    
    with tab1:
        df_valid = df[df['Rating_Clean'].notna()]
        
        if len(df_valid) > 0:
            fig, ax = plt.subplots(figsize=(10, 6))
            
            # Istogramma rating
            ax.hist(df_valid['Rating_Clean'], bins=20, alpha=0.7, color='lightblue', edgecolor='black')
            ax.axvline(df_valid['Rating_Clean'].mean(), color='red', linestyle='--', 
                      label=f'Media: {df_valid["Rating_Clean"].mean():.2f}')
            
            ax.set_xlabel('Rating')
            ax.set_ylabel('Numero Film')
            ax.set_title('Distribuzione Rating Film')
            ax.legend()
            ax.grid(True, alpha=0.3)
            
            st.pyplot(fig)
            
            # Statistiche
            st.subheader("📊 Statistiche Rating")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Media", f"{df_valid['Rating_Clean'].mean():.2f}")
            with col2:
                st.metric("Mediana", f"{df_valid['Rating_Clean'].median():.2f}")
            with col3:
                st.metric("Max", f"{df_valid['Rating_Clean'].max():.1f}")
            with col4:
                st.metric("Min", f"{df_valid['Rating_Clean'].min():.1f}")
    
    with tab2:
        df_timeline = df[df['Watch_Date'].notna()]
        
        if len(df_timeline) > 0:
            # Attività mensile
            df_timeline['Year_Month'] = df_timeline['Watch_Date'].dt.to_period('M')
            monthly_activity = df_timeline.groupby('Year_Month').size()
            
            fig, ax = plt.subplots(figsize=(12, 6))
            monthly_activity.plot(kind='line', ax=ax, color='steelblue', marker='o')
            ax.set_title('Attività Cinematografica nel Tempo')
            ax.set_xlabel('Mese')
            ax.set_ylabel('Film Visti')
            ax.grid(True, alpha=0.3)
            
            st.pyplot(fig)
            
            # Statistiche temporali
            st.subheader("📅 Statistiche Temporali")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Primo Film", df_timeline['Watch_Date'].min().strftime('%d/%m/%Y'))
            with col2:
                st.metric("Ultimo Film", df_timeline['Watch_Date'].max().strftime('%d/%m/%Y'))
            with col3:
                days_span = (df_timeline['Watch_Date'].max() - df_timeline['Watch_Date'].min()).days
                st.metric("Giorni di Attività", f"{days_span:,}")

def show_temporal_analysis(df):
    """Analisi temporale dettagliata"""
    st.header("📅 Analisi Temporale")
    
    tab1, tab2 = st.tabs(["📊 Per Anno", "📈 Tendenze"])
    
    with tab1:
        # Selezione anno
        years_available = sorted(df['Year_Clean'].dropna().unique(), reverse=True)
        selected_year = st.selectbox("Analizza anno:", years_available)
        
        if selected_year:
            year_films = df[df['Year_Clean'] == selected_year]
            year_films_rated = year_films[year_films['Rating_Clean'].notna()]
            
            # Statistiche anno
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("🎬 Film", len(year_films))
            with col2:
                avg_rating = year_films_rated['Rating_Clean'].mean() if len(year_films_rated) > 0 else 0
                st.metric("⭐ Rating Medio", f"{avg_rating:.2f}")
            with col3:
                great_movies = len(year_films_rated[year_films_rated['Rating_Clean'] >= 7.5])
                st.metric("🏆 Great Movies", great_movies)
            with col4:
                if len(year_films_rated) > 0:
                    best_film = year_films_rated.loc[year_films_rated['Rating_Clean'].idxmax()]
                    st.metric("🥇 Miglior Film", f"{best_film['Rating_Clean']:.1f}/10")
    
    with tab2:
        # Tendenze per decennio
        df_valid = df[df['Rating_Clean'].notna() & df['Year_Clean'].notna()]
        
        if len(df_valid) > 0:
            # Raggruppa per decennio
            df_valid['Decade'] = (df_valid['Year_Clean'] // 10) * 10
            decade_stats = df_valid.groupby('Decade').agg({
                'Rating_Clean': ['mean', 'count'],
                'Name': 'count'
            }).round(2)
            
            st.subheader("📊 Statistiche per Decennio")
            
            for decade in sorted(df_valid['Decade'].unique()):
                decade_data = df_valid[df_valid['Decade'] == decade]
                avg_rating = decade_data['Rating_Clean'].mean()
                film_count = len(decade_data)
                great_movies = len(decade_data[decade_data['Rating_Clean'] >= 7.5])
                
                st.markdown(f"""
                <div class="film-card">
                    <strong>Anni {int(decade)}s</strong><br>
                    <small>🎬 {film_count} film | ⭐ {avg_rating:.2f}/10 | 🏆 {great_movies} great movies</small>
                </div>
                """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()