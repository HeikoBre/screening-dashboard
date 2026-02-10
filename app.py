import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import io

# CSS
st.markdown("""
<style>
.main .block-container { font-size: 13px !important; }
h1 { font-size: 20px !important; }
h3 { font-size: 16px !important; }
h4 { font-size: 15px !important; }
.caption { font-size: 11px !important; }
</style>
""", unsafe_allow_html=True)

st.markdown("# Expertenreview gNBS")

# Session State
if 'df' not in st.session_state: st.session_state.df = None
if 'genes' not in st.session_state: st.session_state.genes = []
if 'gene_dict' not in st.session_state: st.session_state.gene_dict = {}
if 'summary_df' not in st.session_state: st.session_state.summary_df = None
if 'total_responses' not in st.session_state: st.session_state.total_responses = 0

# Upload
if st.session_state.df is None:
    uploaded_file = st.file_uploader('CSV hochladen', type='csv')
    if uploaded_file is not None:
        with st.spinner('Lade & analysiere...'):
            df = pd.read_csv(uploaded_file, sep=',', quotechar='"', encoding='utf-8-sig', low_memory=False)
            st.session_state.df = df
            st.session_state.total_responses = len(df)
            
            # Namens-Extraktion
            gene_dict = {}
            for col in df.columns:
                if 'Gen: ' in col and 'Erkrankung: ' in col and 'nationalen' in col and '[Kommentar]' not in col:
                    gene_start = col.find('Gen: ') + 5
                    gene_end = col.find(' Erkrankung: ', gene_start)
                    gene = col[gene_start:gene_end].strip()
                    
                    disease_start = col.find('Erkrankung: ', gene_start) + 12
                    disease_end = col.find('"', disease_start) if '"' in col[disease_start:] else len(col)
                    disease = col[disease_start:disease_end].strip()
                    
                    if gene: gene_dict[gene] = disease
            
            st.session_state.genes = sorted(gene_dict.keys())
            st.session_state.gene_dict = gene_dict
            
            # Summary Tabelle (numerisch, Yes/No)
            summary_data = []
            options = ['Ja', 'Nein', 'Ich kann diese Frage nicht beantworten']
            for gene in st.session_state.genes:
                nat_q_cols = [col for col in df.columns if f'Gen: {gene}' in col and 'nationalen' in col and '[Kommentar]' not in col]
                stud_q_cols = [col for col in df.columns if f'Gen: {gene}' in col and 'wissenschaftlicher' in col and '[Kommentar]' not in col]
                
                nat_data = df[nat_q_cols].stack().dropna()
                n_nat = len(nat_data)
                stud_data = df[stud_q_cols].stack().dropna()
                n_stud = len(stud_data)
                
                nat_ja = (nat_data == 'Ja').sum() / n_nat * 100 if n_nat > 0 else 0
                stud_ja = (stud_data == 'Ja').sum() / n_stud * 100 if n_stud > 0 else 0
                
                summary_data.append({
                    'Gen': gene,
                    'Erkrankung': st.session_state.gene_dict[gene],
                    'National_Ja_pct': round(nat_ja, 1),
                    'National_n': n_nat,
                    'Studie_Ja_pct': round(stud_ja, 1),
                    'Studie_n': n_stud,
                    'National_80': 'Yes' if nat_ja >= 80 else 'No'
                })
            
            st.session_state.summary_df = pd.DataFrame(summary_data)
            
        st.success(f'{len(st.session_state.genes)} Gene | {st.session_state.total_responses} Antworten')
        st.rerun()
else:
    if st.sidebar.button('Neue CSV 🗑️'): 
        for k in list(st.session_state.keys()): del st.session_state[k]
        st.rerun()

# Sidebar Export
if st.session_state.summary_df is not None:
    st.sidebar.markdown("### 📥 Export")
    
    # CSV mit Datum
    today = datetime.now().strftime("%Y%m%d")
    csv_buffer = io.StringIO()
    export_df = st.session_state.summary_df.copy()
    export_df.insert(0, 'Gesamt_Responses', st.session_state.total_responses)
    export_df.to_csv(csv_buffer, index=False)
    csv_data = csv_buffer.getvalue().encode('utf-8')
    
    st.sidebar.download_button(
        label=f'Download Zusammenfassung_{today}.csv',
        data=csv_data,
        file_name=f'gNBS_Expertenreview_Zusammenfassung_{today}.csv',
        mime='text/csv'
    )
    
    st.sidebar.markdown(f"**Gesamt:** {st.session_state.total_responses} Responses")
    st.sidebar.dataframe(st.session_state.summary_df, use_container_width=True, height=300)

# Tabs (Visualisierung mit erweiterter Anzeige)
if st.session_state.df is not None:
    df = st.session_state.df
    tabs = st.tabs(st.session_state.genes)
    
    for tab_idx, tab in enumerate(tabs):
        with tab:
            gene = st.session_state.genes[tab_idx]
            disease = st.session_state.gene_dict.get(gene, '')
            
            col1, col2 = st.columns([1,3])
            with col1: st.markdown(f"**_{gene}_**")
            with col2: st.markdown(disease)
            
            nat_q_cols = [col for col in df.columns if f'Gen: {gene}' in col and 'nationalen' in col and '[Kommentar]' not in col]
            nat_kom_cols = [col for col in df.columns if f'Gen: {gene}' in col and 'nationalen' in col and '[Kommentar]' in col]
            stud_q_cols = [col for col in df.columns if f'Gen: {gene}' in col and 'wissenschaftlicher' in col and '[Kommentar]' not in col]
            stud_kom_cols = [col for col in df.columns if f'Gen: {gene}' in col and 'wissenschaftlicher' in col and '[Kommentar]' in col]

            options = ['Ja', 'Nein', 'Ich kann diese Frage nicht beantworten']
            
            left_col, right_col = st.columns(2)
            
            with left_col:
                st.markdown("#### Nationales Screening")
                nat_data = df[nat_q_cols].stack().dropna()
                n_total = len(nat_data)
                
                fig_nat = go.Figure()
                colors = {'Ja': '#ACF3AE', 'Nein': '#C43D5A', 'Ich kann diese Frage nicht beantworten': '#DDDDDD'}
                for opt in options:
                    pct = (nat_data == opt).sum() / n_total * 100 if n_total > 0 else 0
                    if pct > 0:
                        fig_nat.add_trace(go.Bar(name=opt[:3], x=[''], y=[pct], marker_color=colors[opt],
                                                 text=f'{pct:.0f}%', textposition='inside', textfont_size=11, width=0.3))
                fig_nat.update_layout(barmode='stack', height=220, margin=dict(b=0,t=0,l=0,r=0), yaxis_range=[0,100], bargap=0, showlegend=False, width=100)
                st.plotly_chart(fig_nat, use_container_width=True, key=f'nat_viz_{gene}_{tab_idx}')
                
                # Erweiterte Anzeige
                ja_count = (nat_data == 'Ja').sum()
                nein_count = (nat_data == 'Nein').sum()
                weiss_nicht_count = (nat_data == 'Ich kann diese Frage nicht beantworten').sum()
                ja_pct = ja_count / n_total * 100 if n_total > 0 else 0
                
                st.caption(f'**Gesamt:** n={n_total}')
                st.caption(f'Ja: {ja_count} | Nein: {nein_count} | Weiß nicht: {weiss_nicht_count}')
                st.caption(f'Cut-Off: {"✅ ≥80%" if ja_pct >= 80 else "❌ <80%"}')

            with right_col:
                st.markdown("#### Wissenschaftliche Studie")
                stud_data = df[stud_q_cols].stack().dropna()
                n_total_stud = len(stud_data)
                
                fig_stud = go.Figure()
                for opt in options:
                    pct = (stud_data == opt).sum() / n_total_stud * 100 if n_total_stud > 0 else 0
                    if pct > 0:
                        fig_stud.add_trace(go.Bar(name=opt[:3], x=[''], y=[pct], marker_color=colors[opt],
                                                  text=f'{pct:.0f}%', textposition='inside', textfont_size=11, width=0.3))
                fig_stud.update_layout(barmode='stack', height=220, margin=dict(b=0,t=0,l=0,r=0), yaxis_range=[0,100], bargap=0, showlegend=False, width=100)
                st.plotly_chart(fig_stud, use_container_width=True, key=f'stud_viz_{gene}_{tab_idx}')
                
                # Erweiterte Anzeige
                ja_count_stud = (stud_data == 'Ja').sum()
                nein_count_stud = (stud_data == 'Nein').sum()
                weiss_nicht_count_stud = (stud_data == 'Ich kann diese Frage nicht beantworten').sum()
                ja_pct_stud = ja_count_stud / n_total_stud * 100 if n_total_stud > 0 else 0
                
                st.caption(f'**Gesamt:** n={n_total_stud}')
                st.caption(f'Ja: {ja_count_stud} | Nein: {nein_count_stud} | Weiß nicht: {weiss_nicht_count_stud}')
                st.caption(f'Cut-Off: {"✅ ≥80%" if ja_pct_stud >= 80 else "❌ <80%"}')

            # Kommentare
            st.markdown("<h4 style='font-size: 17px;'>Kommentare</h4>", unsafe_allow_html=True)
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
