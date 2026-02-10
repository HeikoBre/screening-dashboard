import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# CSS
st.markdown("""
<style>
.main .block-container { font-size: 13px !important; }
h1 { font-size: 20px !important; }
h3 { font-size: 16px !important; }
h4 { font-size: 13px !important; }
.caption { font-size: 11px !important; }
</style>
""", unsafe_allow_html=True)

st.markdown("# Genomisches Neugeborenenscreening")

# Session State
if 'df' not in st.session_state: st.session_state.df = None
if 'genes' not in st.session_state: st.session_state.genes = []
if 'gene_dict' not in st.session_state: st.session_state.gene_dict = {}

# Upload
if st.session_state.df is None:
    uploaded_file = st.file_uploader('CSV hochladen', type='csv')
    if uploaded_file is not None:
        with st.spinner('Lade...'):
            df = pd.read_csv(uploaded_file, sep=',', quotechar='"', encoding='utf-8-sig', low_memory=False)
            st.session_state.df = df
            
            # Fix: Vollständige Namen (korrektes Parsing)
            gene_dict = {}
            for col in df.columns:
                if 'Gen: ' in col and 'Erkrankung: ' in col and 'nationalen' in col and '[Kommentar]' not in col:
                    # Gen: nach "Gen: " bis "Erkrankung: "
                    gene_start = col.find('Gen: ') + 5
                    gene_end = col.find(' Erkrankung: ', gene_start)
                    gene = col[gene_start:gene_end].strip()
                    
                    # Erkrankung: nach "Erkrankung: " bis nächstes " oder Ende
                    disease_start = col.find('Erkrankung: ', gene_start) + 12
                    disease_end = col.find('"', disease_start)
                    if disease_end == -1: disease_end = len(col)
                    disease = col[disease_start:disease_end].strip()
                    
                    if gene: gene_dict[gene] = disease
            st.session_state.genes = sorted(gene_dict.keys())
            st.session_state.gene_dict = gene_dict
            
        st.success(f'{len(st.session_state.genes)} Gene')
        st.rerun()
else:
    if st.sidebar.button('Neue CSV'): 
        for k in list(st.session_state.keys()): del st.session_state[k]
        st.rerun()

# Tabs
if st.session_state.df is not None:
    df = st.session_state.df
    tabs = st.tabs(st.session_state.genes)
    
    for tab_idx, tab in enumerate(tabs):
        with tab:
            gene = st.session_state.genes[tab_idx]
            disease = st.session_state.gene_dict.get(gene, '')
            
            st.markdown(f"**_{gene}_**")
            st.markdown(f"*{disease}*")
            
            # Spalten finden
            nat_q_cols = [col for col in df.columns if f'Gen: {gene}' in col and 'nationalen' in col and '[Kommentar]' not in col]
            nat_kom_cols = [col for col in df.columns if f'Gen: {gene}' in col and 'nationalen' in col and '[Kommentar]' in col]
            stud_q_cols = [col for col in df.columns if f'Gen: {gene}' in col and 'wissenschaftlicher' in col and '[Kommentar]' not in col]
            stud_kom_cols = [col for col in df.columns if f'Gen: {gene}' in col and 'wissenschaftlicher' in col and '[Kommentar]' in col]

            # 3 EXAKTE Optionen
            options = ['Ja', 'Nein', 'Ich kann diese Frage nicht beantworten']
            
            left_col, right_col = st.columns(2)
            
            with left_col:
                st.markdown("#### Nationales Screening")
                nat_data = df[nat_q_cols].stack().dropna()
                n_total = len(nat_data)
                
                fig_nat = go.Figure()
                colors = {
                    'Ja': '#000000', 
                    'Nein': '#4B5563', 
                    'Ich kann diese Frage nicht beantworten': '#D1D5DB'
                }
                legend_order = ['Ja', 'Nein', 'Ich kann diese Frage nicht beantworten']
                for opt in legend_order:
                    pct = (nat_data == opt).sum() / n_total * 100 if n_total > 0 else 0
                    fig_nat.add_trace(go.Bar(name=opt[:3], x=[''], y=[pct], 
                                             marker_color=colors[opt],
                                             text=f'{pct:.0f}%' if pct > 0 else '', 
                                             textposition='inside', textfont_size=11))
                fig_nat.update_layout(barmode='stack', height=220, margin=dict(b=0,t=0,l=0,r=0), 
                                      yaxis_range=[0,100], bargap=0, showlegend=False)
                st.plotly_chart(fig_nat, use_container_width=True, key=f'nat_full_{gene}_{tab_idx}')
                
                ja_pct = (nat_data == 'Ja').sum() / n_total * 100 if n_total > 0 else 0
                st.caption(f'n={n_total} | Ja: {"✅ ≥80%" if ja_pct >= 80 else "<80%"}')

            with right_col:
                st.markdown("#### Wissenschaftliche Studie")
                stud_data = df[stud_q_cols].stack().dropna()
                n_total_stud = len(stud_data)
                
                fig_stud = go.Figure()
                for opt in legend_order:
                    pct = (stud_data == opt).sum() / n_total_stud * 100 if n_total_stud > 0 else 0
                    fig_stud.add_trace(go.Bar(name=opt[:3], x=[''], y=[pct], 
                                              marker_color=colors[opt],
                                              text=f'{pct:.0f}%' if pct > 0 else '', 
                                              textposition='inside', textfont_size=11))
                fig_stud.update_layout(barmode='stack', height=220, margin=dict(b=0,t=0,l=0,r=0), 
                                       yaxis_range=[0,100], bargap=0, showlegend=False)
                st.plotly_chart(fig_stud, use_container_width=True, key=f'stud_full_{gene}_{tab_idx}')
                
                ja_pct_stud = (stud_data == 'Ja').sum() / n_total_stud * 100 if n_total_stud > 0 else 0
                st.caption(f'n={n_total_stud} | Ja: {"✅ ≥80%" if ja_pct_stud >= 80 else "<80%"}')

            # Kommentare
            st.markdown("#### Kommentare")
            nat_comments = [str(c) for c in df[nat_kom_cols].stack().dropna() if str(c).strip()]
            stud_comments = [str(c) for c in df[stud_kom_cols].stack().dropna() if str(c).strip()]
            
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("**National:**")
                for c in nat_comments[:3]: st.caption(f"• {c}")
                if not nat_comments: st.caption("Keine")
            with c2:
                st.markdown("**Studie:**")
                for c in stud_comments[:3]: st.caption(f"• {c}")
                if not stud_comments: st.caption("Keine")
