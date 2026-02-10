import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Session State für persistente Daten
if 'df' not in st.session_state:
    st.session_state.df = None
if 'genes' not in st.session_state:
    st.session_state.genes = []

st.title('🧬 Dashboard: Genomisches Neugeborenenscreening')

# Einmaliger Upload (nur wenn keine Daten)
if st.session_state.df is None:
    uploaded_file = st.file_uploader('📁 CSV einmalig hochladen', type='csv', key='upload')
    if uploaded_file is not None:
        with st.spinner('Lade Daten...'):
            df = pd.read_csv(uploaded_file, sep=',', quotechar='"', encoding='utf-8-sig', low_memory=False)
            st.session_state.df = df
            
            # Gene extrahieren
            gene_list = []
            for col in df.columns:
                if 'Gen: ' in col and 'Erkrankung: ' in col and 'nationalen' in col and '[Kommentar]' not in col:
                    gene = col.split('Gen: ')[1].split('  Erkrankung:')[0].strip()
                    gene_list.append(gene)
            st.session_state.genes = list(set(gene_list))
            
        st.success(f'✅ Geladen: {len(st.session_state.df)} Antworten, {len(st.session_state.genes)} Gene')
        st.rerun()  # Sofort refresh
else:
    # Reset-Button (optional)
    if st.sidebar.button('🔄 Neue CSV laden', type='secondary'):
        st.session_state.df = None
        st.session_state.genes = []
        st.rerun()

# Haupt-Interface (nur wenn Daten da)
if st.session_state.df is not None and st.session_state.genes:
    df = st.session_state.df
    genes = st.session_state.genes
    
    # Sidebar-Auswahl (clean)
    st.sidebar.header('Auswahl')
    selected_gene = st.sidebar.selectbox('Gen/Erkrankung:', genes)
    
    # Spalten finden
    nat_q_cols = [col for col in df.columns if f'Gen: {selected_gene}' in col and 'nationalen' in col and '[Kommentar]' not in col]
    nat_kom_cols = [col for col in df.columns if f'Gen: {selected_gene}' in col and 'nationalen' in col and '[Kommentar]' in col]
    stud_q_cols = [col for col in df.columns if f'Gen: {selected_gene}' in col and 'wissenschaftlicher' in col and '[Kommentar]' not in col]
    stud_kom_cols = [col for col in df.columns if f'Gen: {selected_gene}' in col and 'wissenschaftlicher' in col and '[Kommentar]' in col]

    # Nationale Screening
    col1, col2 = st.columns(2)
    with col1:
        st.subheader('🏛️ Nationales Screening')
        nat_data = df[nat_q_cols].stack().dropna()
        nat_data = nat_data[nat_data.isin(['Ja', 'Nein'])]
        ja_nat_pct = (nat_data == 'Ja').mean() * 100 if len(nat_data) > 0 else 0
        total_nat = len(nat_data)
        
        fig_nat = go.Figure(go.Bar(x=['Ja %'], y=[ja_nat_pct], 
                                   marker_color='green' if ja_nat_pct >= 80 else 'orange',
                                   text=f'{ja_nat_pct:.1f}%<br>(n={total_nat})', 
                                   textposition='auto', textfont_size=16))
        fig_nat.update_layout(height=300, yaxis=dict(range=[0,100], title='Prozentsatz'), 
                              title=f'{selected_gene}', showlegend=False, margin=dict(t=60))
        st.plotly_chart(fig_nat, use_container_width=True)
        
        st.metric('Zustimmung', f'{ja_nat_pct:.1f}%', '✅ ≥80%' if ja_nat_pct >= 80 else '❌ <80%')

    with col2:
        st.subheader('🔬 Wissenschaftliche Studie')
        stud_data = df[stud_q_cols].stack().dropna()
        stud_data = stud_data[stud_data.isin(['Ja', 'Nein'])]
        ja_stud_pct = (stud_data == 'Ja').mean() * 100 if len(stud_data) > 0 else 0
        total_stud = len(stud_data)
        
        fig_stud = go.Figure(go.Bar(x=['Ja %'], y=[ja_stud_pct], 
                                    marker_color='blue' if ja_stud_pct >= 80 else 'lightblue',
                                    text=f'{ja_stud_pct:.1f}%<br>(n={total_stud})', 
                                    textposition='auto', textfont_size=16))
        fig_stud.update_layout(height=300, yaxis=dict(range=[0,100], title='Prozentsatz'), 
                               title=f'{selected_gene}', showlegend=False, margin=dict(t=60))
        st.plotly_chart(fig_stud, use_container_width=True)
        
        st.metric('Zustimmung', f'{ja_stud_pct:.1f}%', '✅ ≥80%' if ja_stud_pct >= 80 else '❌ <80%')

    # Kommentare unten
    st.subheader('💬 Kommentare')
    nat_comments = [c for c in df[nat_kom_cols].stack().dropna() if str(c).strip()]
    stud_comments = [c for c in df[stud_kom_cols].stack().dropna() if str(c).strip()]
    
    tab1, tab2 = st.tabs(['National', 'Studie'])
    with tab1:
        if nat_comments:
            st.markdown('**'.join(nat_comments))
        else:
            st.info('Keine Kommentare.')
    with tab2:
        if stud_comments:
            st.markdown('**'.join(stud_comments))
        else:
            st.info('Keine Kommentare.')
            
else:
    st.info('📤 Bitte laden Sie zuerst die CSV-Datei hoch.')
