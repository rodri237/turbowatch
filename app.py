"""
app.py — Application principale Streamlit
Maintenance Prédictive des Turbines Hydrauliques Industrielles
Auteur : Ingénieur Logiciel Senior
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
from pydantic import ValidationError

# Imports locaux
from models import ReleverCapteur, TurbineID, Technicien, calculer_statut
from database import (
    initialiser_bdd,
    inserer_releve,
    lire_releves,
    obtenir_statistiques,
    lire_alertes,
    compter_releves,
)

# ─────────────────────────────────────────────
# Configuration Streamlit (doit être la 1ère commande)
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="TurboWatch — Maintenance Prédictive",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────
# CSS personnalisé — Thème industriel sombre
# ─────────────────────────────────────────────
CSS_GLOBAL = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Rajdhani:wght@400;500;600;700&family=Share+Tech+Mono&family=Exo+2:wght@300;400;600&display=swap');

/* ── Variables de couleur ── */
:root {
    --amber:       #F59E0B;
    --amber-dark:  #B45309;
    --amber-glow:  rgba(245,158,11,0.15);
    --rouge:       #EF4444;
    --vert:        #10B981;
    --bleu:        #3B82F6;
    --bg-deep:     #0A0C10;
    --bg-card:     #111318;
    --bg-panel:    #161A22;
    --border:      rgba(245,158,11,0.25);
    --text-dim:    #6B7280;
    --text-main:   #D1D5DB;
    --text-bright: #F9FAFB;
}

/* ── Base ── */
html, body, [class*="css"] {
    font-family: 'Exo 2', sans-serif;
    background-color: var(--bg-deep) !important;
    color: var(--text-main) !important;
}

/* ── En-tête héro ── */
.hero-header {
    background: linear-gradient(135deg, #0A0C10 0%, #111827 40%, #0A0C10 100%);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 2rem 2.5rem;
    margin-bottom: 1.5rem;
    position: relative;
    overflow: hidden;
}
.hero-header::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    background: linear-gradient(90deg, transparent, var(--amber), transparent);
}
.hero-title {
    font-family: 'Rajdhani', sans-serif;
    font-size: 2.6rem;
    font-weight: 700;
    color: var(--amber);
    margin: 0;
    letter-spacing: 3px;
    text-transform: uppercase;
}
.hero-subtitle {
    font-family: 'Share Tech Mono', monospace;
    color: var(--text-dim);
    font-size: 0.85rem;
    margin-top: 0.3rem;
    letter-spacing: 2px;
}
.hero-badge {
    display: inline-block;
    background: var(--amber-glow);
    border: 1px solid var(--amber);
    color: var(--amber);
    font-family: 'Share Tech Mono', monospace;
    font-size: 0.7rem;
    padding: 0.2rem 0.7rem;
    border-radius: 4px;
    letter-spacing: 1px;
    margin-top: 0.8rem;
}

/* ── Cartes KPI ── */
.kpi-card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 1.2rem 1.5rem;
    position: relative;
    overflow: hidden;
    transition: border-color 0.3s;
}
.kpi-card:hover { border-color: var(--amber); }
.kpi-card::after {
    content: '';
    position: absolute;
    bottom: 0; left: 0; right: 0;
    height: 2px;
    background: linear-gradient(90deg, transparent, var(--amber), transparent);
    opacity: 0.4;
}
.kpi-label {
    font-family: 'Share Tech Mono', monospace;
    font-size: 0.7rem;
    color: var(--text-dim);
    letter-spacing: 2px;
    text-transform: uppercase;
}
.kpi-value {
    font-family: 'Rajdhani', sans-serif;
    font-size: 2.4rem;
    font-weight: 700;
    color: var(--amber);
    line-height: 1;
    margin: 0.3rem 0;
}
.kpi-value.rouge  { color: var(--rouge); }
.kpi-value.vert   { color: var(--vert); }
.kpi-value.bleu   { color: var(--bleu); }

/* ── Section ── */
.section-title {
    font-family: 'Rajdhani', sans-serif;
    font-size: 1.2rem;
    font-weight: 600;
    color: var(--amber);
    letter-spacing: 2px;
    text-transform: uppercase;
    border-left: 3px solid var(--amber);
    padding-left: 0.8rem;
    margin-bottom: 1rem;
}

/* ── Alerte ── */
.alerte-critique {
    background: rgba(239,68,68,0.1);
    border: 1px solid rgba(239,68,68,0.4);
    border-left: 4px solid var(--rouge);
    border-radius: 8px;
    padding: 0.8rem 1rem;
    margin-bottom: 0.5rem;
    font-family: 'Share Tech Mono', monospace;
    font-size: 0.78rem;
    color: #FCA5A5;
}
.alerte-avertissement {
    background: rgba(245,158,11,0.08);
    border: 1px solid rgba(245,158,11,0.3);
    border-left: 4px solid var(--amber);
    border-radius: 8px;
    padding: 0.8rem 1rem;
    margin-bottom: 0.5rem;
    font-family: 'Share Tech Mono', monospace;
    font-size: 0.78rem;
    color: #FCD34D;
}

/* ── Sidebar ── */
section[data-testid="stSidebar"] {
    background: var(--bg-panel) !important;
    border-right: 1px solid var(--border) !important;
}
section[data-testid="stSidebar"] .block-container {
    padding-top: 1.5rem;
}

/* ── Inputs Streamlit ── */
div[data-testid="stNumberInput"] input,
div[data-testid="stTextArea"] textarea,
div[data-testid="stSelectbox"] div {
    background: #1C2030 !important;
    border: 1px solid var(--border) !important;
    color: var(--text-bright) !important;
    font-family: 'Share Tech Mono', monospace !important;
    border-radius: 6px !important;
}

/* ── Bouton principal ── */
.stButton > button {
    background: linear-gradient(135deg, var(--amber-dark), var(--amber)) !important;
    color: #000 !important;
    font-family: 'Rajdhani', sans-serif !important;
    font-weight: 700 !important;
    font-size: 1rem !important;
    letter-spacing: 2px !important;
    text-transform: uppercase !important;
    border: none !important;
    border-radius: 6px !important;
    padding: 0.6rem 1.5rem !important;
    width: 100% !important;
    transition: opacity 0.2s !important;
}
.stButton > button:hover { opacity: 0.85 !important; }

/* ── DataTable ── */
div[data-testid="stDataFrame"] {
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
}

/* ── Tabs ── */
div[data-testid="stTabs"] button {
    font-family: 'Rajdhani', sans-serif !important;
    font-weight: 600 !important;
    letter-spacing: 1px !important;
    color: var(--text-dim) !important;
}
div[data-testid="stTabs"] button[aria-selected="true"] {
    color: var(--amber) !important;
    border-bottom-color: var(--amber) !important;
}

/* ── Supprimer le menu Streamlit ── */
#MainMenu, footer, header { visibility: hidden; }

/* ── Statut badge ── */
.badge-normal   { background:#065F46;color:#6EE7B7;padding:2px 8px;border-radius:4px;font-size:0.75rem;font-family:'Share Tech Mono',monospace; }
.badge-warn     { background:#78350F;color:#FCD34D;padding:2px 8px;border-radius:4px;font-size:0.75rem;font-family:'Share Tech Mono',monospace; }
.badge-crit     { background:#7F1D1D;color:#FCA5A5;padding:2px 8px;border-radius:4px;font-size:0.75rem;font-family:'Share Tech Mono',monospace; }
</style>
"""

# ─────────────────────────────────────────────
# Fonctions utilitaires d'affichage
# ─────────────────────────────────────────────
def kpi_card(label: str, valeur, couleur: str = "") -> str:
    """Génère le HTML d'une carte KPI."""
    return f"""
    <div class="kpi-card">
        <div class="kpi-label">{label}</div>
        <div class="kpi-value {couleur}">{valeur}</div>
    </div>
    """

def badge_statut(statut: str) -> str:
    """Retourne un badge HTML coloré selon le statut."""
    classes = {"Normal": "badge-normal", "Avertissement": "badge-warn", "Critique": "badge-crit"}
    icons   = {"Normal": "●", "Avertissement": "▲", "Critique": "✦"}
    cls = classes.get(statut, "badge-normal")
    ico = icons.get(statut, "●")
    return f'<span class="{cls}">{ico} {statut}</span>'


def creer_jauge(valeur: float, mini: float, maxi: float,
                seuil_warn: float, seuil_crit: float,
                titre: str, unite: str) -> go.Figure:
    """
    Crée une jauge Plotly stylisée en thème industriel sombre.
    Couleurs : vert → orange → rouge selon les seuils.
    """
    # Calcul de la couleur de l'aiguille
    if valeur >= seuil_crit:
        couleur_aig = "#EF4444"
    elif valeur >= seuil_warn:
        couleur_aig = "#F59E0B"
    else:
        couleur_aig = "#10B981"

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=valeur,
        title={"text": f"{titre}<br><span style='font-size:0.8em;color:#6B7280'>{unite}</span>",
               "font": {"family": "Rajdhani", "color": "#D1D5DB", "size": 16}},
        number={"font": {"family": "Share Tech Mono", "color": couleur_aig, "size": 28}},
        gauge={
            "axis": {
                "range": [mini, maxi],
                "tickcolor": "#374151",
                "tickfont": {"color": "#6B7280", "size": 10},
            },
            "bar": {"color": couleur_aig, "thickness": 0.25},
            "bgcolor": "#161A22",
            "bordercolor": "#374151",
            "steps": [
                {"range": [mini, seuil_warn],    "color": "rgba(16,185,129,0.15)"},
                {"range": [seuil_warn, seuil_crit], "color": "rgba(245,158,11,0.15)"},
                {"range": [seuil_crit, maxi],    "color": "rgba(239,68,68,0.15)"},
            ],
            "threshold": {
                "line": {"color": "#EF4444", "width": 2},
                "thickness": 0.75,
                "value": seuil_crit,
            },
        },
    ))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=20, r=20, t=60, b=20),
        height=200,
    )
    return fig


# ─────────────────────────────────────────────
# Onglet 1 : Saisie d'un nouveau relevé
# ─────────────────────────────────────────────
def onglet_saisie():
    """Interface de collecte des données de capteurs."""

    st.markdown('<div class="section-title">⚙ Nouveau Relevé de Capteurs</div>', unsafe_allow_html=True)

    # ── Formulaire de saisie ─────────────────────────────────
    with st.form(key="form_releve", clear_on_submit=True):

        col1, col2 = st.columns(2)

        with col1:
            turbine = st.selectbox(
                "🔩 Turbine concernée",
                options=[t.value for t in TurbineID],
                help="Identifiant de la turbine hydraulique"
            )
            tech = st.selectbox(
                "👷 Technicien responsable",
                options=[t.value for t in Technicien]
            )

        with col2:
            temperature = st.number_input(
                "🌡 Température (°C)",
                min_value=-20.0, max_value=200.0,
                value=45.0, step=0.5,
                help="Plage normale : 20°C – 80°C"
            )
            vibration = st.number_input(
                "📳 Vibration (mm/s)",
                min_value=0.0, max_value=50.0,
                value=5.0, step=0.1,
                help="Plage normale : 0 – 10 mm/s"
            )

        col3, col4 = st.columns(2)
        with col3:
            pression = st.number_input(
                "⬛ Pression (bar)",
                min_value=0.0, max_value=500.0,
                value=120.0, step=1.0,
                help="Plage normale : 0 – 200 bar"
            )
        with col4:
            debit = st.number_input(
                "💧 Débit (m³/h) — Optionnel",
                min_value=0.0, max_value=10000.0,
                value=0.0, step=10.0,
            )

        notes = st.text_area(
            "📝 Observations du technicien",
            placeholder="Ex : Vibration inhabituelle détectée au niveau du palier supérieur…",
            max_chars=500,
            height=90,
        )

        # ── Aperçu instantané du statut ──────────────────────
        statut_preview = calculer_statut(temperature, vibration, pression)
        icones = {"Normal": "🟢", "Avertissement": "🟡", "Critique": "🔴"}
        st.markdown(
            f"**Statut prévu :** {icones.get(statut_preview, '')} **{statut_preview}**",
            unsafe_allow_html=True
        )

        # ── Bouton de soumission ──────────────────────────────
        soumis = st.form_submit_button("▶ ENREGISTRER LE RELEVÉ")

    # ── Traitement après soumission ───────────────────────────
    if soumis:
        try:
            # Validation Pydantic
            releve = ReleverCapteur(
                turbine_id=TurbineID(turbine),
                technicien=Technicien(tech),
                temperature=temperature,
                vibration=vibration,
                pression=pression,
                debit=debit if debit > 0 else None,
                notes=notes if notes.strip() else None,
            )

            # Insertion en base de données
            releve_id = inserer_releve(releve)
            statut_final = calculer_statut(temperature, vibration, pression)

            # Feedback visuel selon le statut
            if statut_final == "Normal":
                st.success(f"✅ Relevé #{releve_id} enregistré avec succès — Turbine {turbine} en état NORMAL.")
            elif statut_final == "Avertissement":
                st.warning(f"⚠️ Relevé #{releve_id} enregistré — AVERTISSEMENT détecté sur {turbine}. Surveillance renforcée recommandée.")
            else:
                st.error(f"🚨 Relevé #{releve_id} enregistré — ÉTAT CRITIQUE sur {turbine} ! Inspection immédiate requise.")

        except ValidationError as e:
            # Affichage des erreurs de validation Pydantic
            st.error("❌ Données invalides — Correction requise :")
            for erreur in e.errors():
                champ = " → ".join(str(c) for c in erreur["loc"])
                st.markdown(f"• **{champ}** : {erreur['msg']}")

        except Exception as e:
            # Gestion des erreurs inattendues
            st.error(f"❌ Erreur système inattendue : {e}")
            st.info("Vérifiez les logs pour plus de détails.")

    # ── Jauges temps réel ─────────────────────────────────────
    st.markdown("---")
    st.markdown('<div class="section-title">📊 Aperçu en Temps Réel</div>', unsafe_allow_html=True)

    g1, g2, g3 = st.columns(3)
    with g1:
        st.plotly_chart(
            creer_jauge(temperature, -20, 200, 80, 120, "Température", "°C"),
            width="stretch", config={"displayModeBar": False}
        )
    with g2:
        st.plotly_chart(
            creer_jauge(vibration, 0, 50, 10, 20, "Vibration", "mm/s"),
            width="stretch", config={"displayModeBar": False}
        )
    with g3:
        st.plotly_chart(
            creer_jauge(pression, 0, 500, 200, 350, "Pression", "bar"),
            width="stretch", config={"displayModeBar": False}
        )


# ─────────────────────────────────────────────
# Onglet 2 : Tableau de bord & historique
# ─────────────────────────────────────────────
def onglet_tableau_de_bord():
    """Affiche les KPIs, graphiques et l'historique des relevés."""

    compteurs = compter_releves()
    statistiques = obtenir_statistiques()

    # ── KPI globaux ──────────────────────────────────────────
    st.markdown('<div class="section-title">📈 Indicateurs Globaux</div>', unsafe_allow_html=True)
    k1, k2, k3, k4 = st.columns(4)

    with k1:
        st.markdown(kpi_card("Total Relevés", compteurs["total"]), unsafe_allow_html=True)
    with k2:
        st.markdown(kpi_card("État Normal", compteurs["normal"], "vert"), unsafe_allow_html=True)
    with k3:
        st.markdown(kpi_card("Avertissements", compteurs["avertissement"], ""), unsafe_allow_html=True)
    with k4:
        st.markdown(kpi_card("Critiques", compteurs["critique"], "rouge"), unsafe_allow_html=True)

    st.markdown("---")

    # ── Statistiques par turbine ─────────────────────────────
    if statistiques:
        st.markdown('<div class="section-title">🔩 Performance par Turbine</div>', unsafe_allow_html=True)

        df_stats = pd.DataFrame(statistiques)

        # Graphique barres groupées — températures moyennes
        fig_bar = px.bar(
            df_stats,
            x="turbine_id", y=["temp_moy", "vib_moy", "pres_moy"],
            barmode="group",
            title="Moyennes par turbine",
            labels={"value": "Valeur", "turbine_id": "Turbine", "variable": "Capteur"},
            color_discrete_sequence=["#F59E0B", "#3B82F6", "#10B981"],
            template="plotly_dark",
        )
        fig_bar.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="#111318",
            font={"family": "Exo 2", "color": "#D1D5DB"},
            legend={"bgcolor": "rgba(0,0,0,0)"},
            title_font={"family": "Rajdhani", "size": 18},
        )
        st.plotly_chart(fig_bar, width="stretch", config={"displayModeBar": False})

    # ── Historique des relevés ────────────────────────────────
    st.markdown('<div class="section-title">📋 Historique des Relevés</div>', unsafe_allow_html=True)

    # Filtres
    fc1, fc2, fc3 = st.columns([2, 2, 1])
    with fc1:
        filtre_turbine = st.selectbox(
            "Filtrer par turbine",
            ["Toutes"] + [t.value for t in TurbineID]
        )
    with fc2:
        filtre_statut = st.selectbox(
            "Filtrer par statut",
            ["Tous", "Normal", "Avertissement", "Critique"]
        )
    with fc3:
        limite = st.number_input("Limite", min_value=10, max_value=500, value=50, step=10)

    releves = lire_releves(limite=limite, turbine_id=filtre_turbine, statut=filtre_statut)

    if releves:
        df = pd.DataFrame(releves)

        # Renommer les colonnes pour l'affichage
        df = df.rename(columns={
            "id": "ID", "turbine_id": "Turbine", "technicien": "Technicien",
            "temperature": "Temp (°C)", "vibration": "Vib (mm/s)",
            "pression": "Pres (bar)", "debit": "Débit (m³/h)",
            "notes": "Notes", "horodatage": "Horodatage",
            "statut_alerte": "Statut",
        })
        df["Horodatage"] = pd.to_datetime(df["Horodatage"]).dt.strftime("%d/%m/%Y %H:%M")

        st.dataframe(
            df[["ID", "Turbine", "Technicien", "Temp (°C)",
                "Vib (mm/s)", "Pres (bar)", "Statut", "Horodatage"]],
            width="stretch",
            hide_index=True,
        )

        # ── Graphique temporel ───────────────────────────────
        if len(df) > 1:
            st.markdown('<div class="section-title">📉 Évolution Temporelle</div>', unsafe_allow_html=True)

            df_chart = pd.DataFrame(releves).sort_values("horodatage")
            fig_line = go.Figure()
            fig_line.add_trace(go.Scatter(
                x=df_chart["horodatage"], y=df_chart["temperature"],
                name="Température (°C)", line=dict(color="#F59E0B", width=2)
            ))
            fig_line.add_trace(go.Scatter(
                x=df_chart["horodatage"], y=df_chart["vibration"],
                name="Vibration (mm/s)", line=dict(color="#3B82F6", width=2),
                yaxis="y2"
            ))
            fig_line.update_layout(
                template="plotly_dark",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="#111318",
                font={"family": "Exo 2", "color": "#D1D5DB"},
                title={"text": "Évolution des capteurs dans le temps",
                       "font": {"family": "Rajdhani", "size": 18}},
                yaxis2={"overlaying": "y", "side": "right"},
                legend={"bgcolor": "rgba(0,0,0,0)"},
                hovermode="x unified",
            )
            st.plotly_chart(fig_line, width="stretch", config={"displayModeBar": False})

    else:
        st.info("ℹ️ Aucun relevé trouvé pour les filtres sélectionnés.")


# ─────────────────────────────────────────────
# Onglet 3 : Journal d'alertes
# ─────────────────────────────────────────────
def onglet_alertes():
    """Affiche le journal des alertes industrielles."""

    st.markdown('<div class="section-title">🚨 Journal des Alertes Industrielles</div>',
                unsafe_allow_html=True)

    alertes = lire_alertes(limite=30)

    if not alertes:
        st.success("✅ Aucune alerte enregistrée. Toutes les turbines fonctionnent normalement.")
        return

    for alerte in alertes:
        horodatage = alerte.get("horodatage", "")[:19].replace("T", " ")
        niveau     = alerte.get("niveau_alerte", "Normal")
        message    = alerte.get("message", "")

        classe_css = "alerte-critique" if niveau == "Critique" else "alerte-avertissement"
        icone      = "🔴" if niveau == "Critique" else "🟡"

        st.markdown(
            f'<div class="{classe_css}">'
            f'{icone} [{horodatage}] &nbsp;|&nbsp; <strong>{niveau}</strong> &nbsp;|&nbsp; {message}'
            f'</div>',
            unsafe_allow_html=True
        )


# ─────────────────────────────────────────────
# Point d'entrée principal
# ─────────────────────────────────────────────
def main():
    """Fonction principale — orchestration de l'application."""

    # Injection du CSS global
    st.markdown(CSS_GLOBAL, unsafe_allow_html=True)

    # Initialisation de la base de données (idempotente)
    try:
        initialiser_bdd()
    except Exception as e:
        st.error(f"❌ Impossible d'initialiser la base de données : {e}")
        st.stop()

    # ── En-tête héro ──────────────────────────────────────────
    st.markdown("""
    <div class="hero-header">
        <div class="hero-title">⚙ TurboWatch</div>
        <div class="hero-subtitle">SYSTÈME DE MAINTENANCE PRÉDICTIVE — TURBINES HYDRAULIQUES INDUSTRIELLES</div>
        <div class="hero-badge">🔒 DONNÉES SÉCURISÉES · SQLITE · VERSION 1.0</div>
    </div>
    """, unsafe_allow_html=True)

    # ── Barre latérale — informations système ─────────────────
    with st.sidebar:
        st.markdown("""
        <div style="font-family:'Rajdhani',sans-serif;font-size:1.3rem;font-weight:700;
             color:#F59E0B;letter-spacing:2px;margin-bottom:0.5rem">
        ⚙ SYSTÈME
        </div>
        """, unsafe_allow_html=True)

        # Horloge en direct
        st.markdown(
            f"<div style='font-family:\"Share Tech Mono\",monospace;color:#6B7280;font-size:0.8rem'>"
            f"🕐 {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</div>",
            unsafe_allow_html=True
        )

        st.markdown("---")
        st.markdown("**Seuils de référence**")
        st.markdown("""
        | Capteur | Normal | Alerte |
        |---------|--------|--------|
        | Temp.   | < 80°C | > 120°C |
        | Vibr.   | < 10 mm/s | > 20 mm/s |
        | Pres.   | < 200 bar | > 350 bar |
        """)

        st.markdown("---")
        st.markdown("**Turbines supervisées**")
        for t in TurbineID:
            st.markdown(f"• `{t.value}`")

        st.markdown("---")
        st.caption("Développé avec Python + Streamlit\n\nMaintenance Prédictive Industrielle © 2024")

    # ── Navigation par onglets ────────────────────────────────
    tab1, tab2, tab3 = st.tabs([
        "📡 SAISIE RELEVÉ",
        "📊 TABLEAU DE BORD",
        "🚨 JOURNAL ALERTES",
    ])

    with tab1:
        onglet_saisie()

    with tab2:
        onglet_tableau_de_bord()

    with tab3:
        onglet_alertes()


# ─────────────────────────────────────────────
# Lancement
# ─────────────────────────────────────────────
if __name__ == "__main__":
    main()
