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
        # Ordina per rating decrescente - FIX per l'errore
        if 'Rating_Clean' in filtered_df.columns and not filtered_df['Rating_Clean'].isna().all():
            filtered_df = filtered_df.sort_values('Rating_Clean', ascending=False, na_last=True)
        else:
            # Se non ci sono rating validi, ordina per nome
            filtered_df = filtered_df.sort_values('Name', na_last=True)
        
        for i, (_, film) in enumerate(filtered_df.head(50).iterrows(), 1):
            # Gestione sicura dei valori che potrebbero essere None/NaN
            rating = film['Rating_Clean'] if pd.notna(film['Rating_Clean']) else 'N/A'
            year = f" ({int(film['Year_Clean'])})" if pd.notna(film['Year_Clean']) else ""
            duration = f" | ⏱️ {int(film['Duration_Clean'])}min" if pd.notna(film['Duration_Clean']) else ""
            
            # Gestione sicura del nome e regista
            film_name = film['Name'] if pd.notna(film['Name']) else 'Film senza titolo'
            director_name = film['Director'] if pd.notna(film['Director']) else 'Regista sconosciuto'
            
            # Evidenzia great movies solo se il rating è un numero valido
            title_style = "font-weight: bold; color: #FF6B6B;" if (pd.notna(film['Rating_Clean']) and float(str(rating).replace('N/A', '0')) >= 7.5) else ""
            
            st.markdown(f"""
            <div class="film-card">
                <span style="{title_style}">{i}. {film_name}</span>{year}<br>
                <small>🎭 {director_name} | ⭐ {rating}/10{duration}</small>
            </div>
            """, unsafe_allow_html=True)
        
        if len(filtered_df) > 50:
            st.info(f"Mostrati i primi 50 risultati di {len(filtered_df)}")

def show_top_films(df):
    """Top film per anno/decade"""
    st.header("🏆 Top Film")
    
    tab1, tab2, tab3, tab4 = st.tabs(["📅 Per Anno", "📊 Per Decennio", "🌟 Film 10/10", "🎬 Great Movies"])
    
    with tab1:
        col1, col2 = st.columns(2)
        with col1:
            years_list = sorted([int(year) for year in df['Year_Clean'].dropna().unique()], reverse=True)
            selected_year = st.selectbox("Scegli anno:", years_list)
        with col2:
            top_n = st.slider("Numero film:", 5, 100, 10)
        
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
        col1, col2 = st.columns(2)
        with col1:
            decades = list(range(1920, 2030, 10))
            selected_decade = st.selectbox("Scegli decennio:", decades, index=len(decades)-3)
        with col2:
            top_n_decade = st.slider("Numero film:", 5, 100, 15, key="decade_slider")
        
        decade_films = df[(df['Year_Clean'] >= selected_decade) & (df['Year_Clean'] < selected_decade + 10)]
        decade_films_rated = decade_films[decade_films['Rating_Clean'].notna()]
        
        if len(decade_films_rated) > 0:
            top_decade = decade_films_rated.nlargest(top_n_decade, 'Rating_Clean')
            
            st.subheader(f"🏆 Top {top_n_decade} Film anni {selected_decade}s")
            
            for i, (_, film) in enumerate(top_decade.iterrows(), 1):
                year = f" ({int(film['Year_Clean'])})" if pd.notna(film['Year_Clean']) else ""
                st.markdown(f"""
                <div class="film-card">
                    <strong>{i}. {film['Name']}</strong>{year}<br>
                    <small>🎭 {film['Director']} | ⭐ {film['Rating_Clean']}/10</small>
                </div>
                """, unsafe_allow_html=True)
    
    with tab3:
        # Film con voto 10/10
        df_rated = df[df['Rating_Clean'].notna()]
        perfect_films = df_rated[df_rated['Rating_Clean'] == 10.0]
        
        if len(perfect_films) > 0:
            # Ordina per anno (cronologico)
            perfect_films_sorted = perfect_films.sort_values('Year_Clean', ascending=True)
            
            st.subheader(f"🌟 I Miei Film 10/10 ({len(perfect_films)} film)")
            
            for i, (_, film) in enumerate(perfect_films_sorted.iterrows(), 1):
                year = f" ({int(film['Year_Clean'])})" if pd.notna(film['Year_Clean']) else ""
                st.markdown(f"""
                <div class="film-card">
                    <strong>{i}. {film['Name']}</strong>{year}<br>
                    <small>🎭 {film['Director']} | ⭐ {film['Rating_Clean']}/10</small>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("Nessun film con voto 10/10 trovato nel database")
    
    with tab4:
        # Great Movies (7.5+)
        df_rated = df[df['Rating_Clean'].notna()]
        great_films = df_rated[df_rated['Rating_Clean'] >= 7.5]
        
        if len(great_films) > 0:
            # Ordina per anno (cronologico)
            great_films_sorted = great_films.sort_values('Year_Clean', ascending=True)
            
            st.subheader(f"🎬 Great Movies - 7.5+ ({len(great_films)} film)")
            
            # Mostra con paginazione ogni 50 film
            films_per_page = 50
            total_pages = (len(great_films_sorted) + films_per_page - 1) // films_per_page
            
            if total_pages > 1:
                page = st.selectbox("Pagina:", range(1, total_pages + 1))
                start_idx = (page - 1) * films_per_page
                end_idx = start_idx + films_per_page
                films_to_show = great_films_sorted.iloc[start_idx:end_idx]
            else:
                films_to_show = great_films_sorted
            
            for i, (_, film) in enumerate(films_to_show.iterrows(), 1):
                year = f" ({int(film['Year_Clean'])})" if pd.notna(film['Year_Clean']) else ""
                rating = film['Rating_Clean']
                st.markdown(f"""
                <div class="film-card">
                    <strong>{film['Name']}</strong>{year}<br>
                    <small>🎭 {film['Director']} | ⭐ {rating}/10</small>
                </div>
                """, unsafe_allow_html=True)
            
            if total_pages > 1:
                st.info(f"Pagina {page} di {total_pages} - {len(great_films)} great movies totali")
        else:
            st.info("Nessun Great Movie (7.5+) trovato nel database")

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
    
    # Controlla se esiste la colonna tag diario
    tag_column = None
    possible_columns = ['Tag Diario', 'tag diario', 'Tag_Diario', 'tag_diario', 'Diario Tag', 'diario_tag']
    
    for col in df.columns:
        if any(tag_col.lower() in col.lower() for tag_col in possible_columns):
            tag_column = col
            break
    
    if not tag_column:
        st.error("❌ Colonna 'Tag Diario' non trovata nel database")
        st.info("💡 Colonne disponibili nel CSV:")
        st.write(list(df.columns))
        return
    
    st.info(f"📊 Analizzando la colonna: '{tag_column}'")
    
    # Dizionario dei compagni
    companions = {
        'c:c': 'Claudia (mamma)',
        'c:a': 'Ale (babbo)', 
        'c:p': 'Priamo',
        'c:r': 'Rebecca',
        'c:k': 'Kenta',
        'd:m': 'Marco Grifò',
        'c:mo': 'Monica',
        'd:p': 'Priamo',
        'c:av': 'Alessandro Valenti',
        'd:r': 'Rebecca',
        'd:k': 'Kenta', 
        'c:m': 'Marco Grifò',
        'd:l': 'Leonardo Romagnoli',
        'c:l': 'Leonardo Romagnoli',
        'c:d': 'Dario',
        'd:sm': 'Simone Malaspina',
        'c:sm': 'Simone Malaspina',
        'd:av': 'Alessandro Valenti',
        'd:d': 'Dario'
    }
    
    # Trova film con tag di compagnia
    companion_films = {}
    
    for tag, name in companions.items():
        # Cerca film che contengono questo tag
        mask = df[tag_column].astype(str).str.contains(tag, case=False, na=False)
        films = df[mask].copy()
        
        if len(films) > 0:
            if name not in companion_films:
                companion_films[name] = pd.DataFrame()
            
            # Unisci i film senza duplicati
            companion_films[name] = pd.concat([companion_films[name], films]).drop_duplicates()
    
    if not companion_films:
        st.warning("❌ Nessun film trovato con tag di compagnia")
        st.info("💡 Tags cercati: c:c, c:a, c:p, c:r, d:m, etc.")
        
        # Mostra esempi di contenuti nella colonna tag
        sample_tags = df[tag_column].dropna().head(10)
        if len(sample_tags) > 0:
            st.info("📝 Esempi di contenuti nella colonna tag:")
            for tag in sample_tags:
                st.write(f"- '{tag}'")
        return
    
    # Calcola statistiche
    all_companion_film_indices = set()
    for films in companion_films.values():
        all_companion_film_indices.update(films.index)
    
    total_companion_films = len(all_companion_film_indices)
    total_films = len(df)
    companion_percentage = (total_companion_films / total_films) * 100
    
    # Statistiche generali
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("🎬 Film Totali", f"{total_films:,}")
    with col2:
        st.metric("👥 Film in Compagnia", f"{total_companion_films:,}")
    with col3:
        st.metric("📈 Percentuale", f"{companion_percentage:.1f}%")
    
    # Top compagni
    companion_counts = [(name, len(films)) for name, films in companion_films.items()]
    companion_counts.sort(key=lambda x: x[1], reverse=True)
    
    st.subheader("🏆 Classifica Compagni di Visione")
    
    for i, (name, count) in enumerate(companion_counts, 1):
        films = companion_films[name]
        films_with_rating = films[films['Rating_Clean'].notna()]
        
        if len(films_with_rating) > 0:
            avg_rating = films_with_rating['Rating_Clean'].mean()
            great_movies = len(films_with_rating[films_with_rating['Rating_Clean'] >= 7.5])
            rating_info = f" | ⭐ {avg_rating:.2f}/10 | 🏆 {great_movies} great movies"
        else:
            rating_info = " | ⭐ N/A"
        
        percentage = (count / total_companion_films) * 100
        st.markdown(f"""
        <div class="film-card">
            <strong>{i}. {name}</strong><br>
            <small>🎬 {count} film ({percentage:.1f}%){rating_info}</small>
        </div>
        """, unsafe_allow_html=True)
    
    # Dettagli per compagno selezionato
    st.subheader("🔍 Dettagli Compagno")
    selected_companion = st.selectbox("Scegli un compagno:", list(companion_films.keys()))
    
    if selected_companion:
        films = companion_films[selected_companion]
        films_with_rating = films[films['Rating_Clean'].notna()]
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("🎬 Film Insieme", len(films))
        with col2:
            if len(films_with_rating) > 0:
                avg_rating = films_with_rating['Rating_Clean'].mean()
                st.metric("⭐ Rating Medio", f"{avg_rating:.2f}/10")
            else:
                st.metric("⭐ Rating Medio", "N/A")
        with col3:
            great_movies = len(films_with_rating[films_with_rating['Rating_Clean'] >= 7.5])
            st.metric("🏆 Great Movies", great_movies)
        
        # Lista film con questo compagno
        if len(films_with_rating) > 0:
            st.subheader(f"🎬 Film visti con {selected_companion}")
            
            # Ordina per rating decrescente
            top_films = films_with_rating.sort_values('Rating_Clean', ascending=False)
            
            for i, (_, film) in enumerate(top_films.head(20).iterrows(), 1):
                rating = film['Rating_Clean']
                year = f" ({int(film['Year_Clean'])})" if pd.notna(film['Year_Clean']) else ""
                director = film['Director'] if pd.notna(film['Director']) else "Sconosciuto"
                
                title_style = "font-weight: bold; color: #FF6B6B;" if rating >= 7.5 else ""
                
                st.markdown(f"""
                <div class="film-card">
                    <span style="{title_style}">{i}. {film['Name']}</span>{year}<br>
                    <small>🎭 {director} | ⭐ {rating}/10</small>
                </div>
                """, unsafe_allow_html=True)
            
            if len(top_films) > 20:
                st.info(f"Mostrati i primi 20 di {len(top_films)} film con rating")

def show_charts(df):
    """Grafici e visualizzazioni"""
    st.header("📈 Grafici e Statistiche")
    
    tab1, tab2 = st.tabs(["📊 Distribuzione Rating", "⏱️ Attività nel Tempo"])
    
    with tab1:
        df_valid = df[df['Rating_Clean'].notna()]
        
        if len(df_valid) > 0:
            fig, ax = plt.subplots(figsize=(12, 8))
            
            # Arrotondo per difetto i rating (come nel codice originale)
            df_simplified = df_valid.copy()
            df_simplified['Rating_Simplified'] = df_valid['Rating_Clean'].apply(lambda x: int(x))
            
            # Creo bins per voti interi da 2 a 10 (incluso)
            bins = list(range(2, 11)) + [11]  # Da 2 a 11, così il bin 10 include i voti 10.0
            
            ax.hist(df_simplified['Rating_Simplified'], bins=bins, alpha=0.7, color='lightblue', 
                    edgecolor='black', width=0.8, align='left')
            
            # Statistiche sui voti semplificati
            mean_rating = df_simplified['Rating_Simplified'].mean()
            median_rating = df_simplified['Rating_Simplified'].median()
            
            # Linee statistiche
            ax.axvline(mean_rating, color='red', linestyle='--', linewidth=2, label=f'Media: {mean_rating:.1f}')
            ax.axvline(median_rating, color='green', linestyle='--', linewidth=2, label=f'Mediana: {median_rating:.0f}')
            
            ax.set_xlabel('Rating (voti interi)')
            ax.set_ylabel('Numero di Film')
            ax.set_title('📊 Distribuzione Rating Film')
            ax.legend()
            ax.grid(True, alpha=0.3)
            
            # Imposta i tick per voti interi da 2 a 10
            ax.set_xticks(range(2, 11))
            ax.set_xlim(1.5, 10.5)  # Limiti per centrare le barre
            
            st.pyplot(fig)
            
            # Statistiche
            st.subheader("📊 Statistiche Rating")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Media", f"{mean_rating:.1f}")
            with col2:
                st.metric("Mediana", f"{median_rating:.0f}")
            with col3:
                st.metric("Max", f"{df_simplified['Rating_Simplified'].max()}")
            with col4:
                st.metric("Min", f"{df_simplified['Rating_Simplified'].min()}")
            
            # Statistiche aggiuntive
            great_movies = len(df_valid[df_valid['Rating_Clean'] >= 7.5])
            great_percentage = (great_movies / len(df_valid)) * 100
            
            st.markdown(f"""
            <div class="stats-card">
                <h4>🏆 Great Movies (7.5+)</h4>
                <h3>{great_movies} film ({great_percentage:.1f}%)</h3>
                <p>📊 Film totali con rating: {len(df_valid)}</p>
            </div>
            """, unsafe_allow_html=True)
    
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
        years_available = sorted([int(year) for year in df['Year_Clean'].dropna().unique()], reverse=True)
        selected_year = st.selectbox("Scegli anno:", years_available)
        
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