"""
database.py — Couche d'accès aux données (SQLite)
Gestion sécurisée et robuste du stockage des relevés de capteurs.
Auteur : Ingénieur Logiciel Senior
"""

import sqlite3
import logging
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Generator, List, Optional

from models import ReleverCapteur, calculer_statut

# ─────────────────────────────────────────────
# Configuration du journal d'événements
# ─────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# Chemin vers le fichier de base de données
CHEMIN_BDD = Path("data/maintenance_predictive.db")


# ─────────────────────────────────────────────
# Gestionnaire de connexion (context manager)
# ─────────────────────────────────────────────
@contextmanager
def obtenir_connexion() -> Generator[sqlite3.Connection, None, None]:
    """
    Ouvre une connexion SQLite de façon sécurisée.
    Garantit la fermeture de la connexion même en cas d'erreur.
    Utilise row_factory pour obtenir des résultats sous forme de dictionnaires.
    """
    CHEMIN_BDD.parent.mkdir(parents=True, exist_ok=True)
    connexion = None
    try:
        connexion = sqlite3.connect(str(CHEMIN_BDD), check_same_thread=False)
        connexion.row_factory = sqlite3.Row   # accès par nom de colonne
        connexion.execute("PRAGMA journal_mode=WAL")   # écriture sécurisée
        connexion.execute("PRAGMA foreign_keys=ON")    # intégrité référentielle
        yield connexion
    except sqlite3.Error as e:
        logger.error(f"Erreur de connexion à la base de données : {e}")
        raise
    finally:
        if connexion:
            connexion.close()


# ─────────────────────────────────────────────
# Initialisation du schéma de base de données
# ─────────────────────────────────────────────
def initialiser_bdd() -> None:
    """
    Crée les tables de la base de données si elles n'existent pas encore.
    Structure :
      - releves_capteurs : données brutes des capteurs
      - journal_alertes  : historique des événements critiques
    """
    schema_releves = """
        CREATE TABLE IF NOT EXISTS releves_capteurs (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            turbine_id     TEXT    NOT NULL,
            technicien     TEXT    NOT NULL,
            temperature    REAL    NOT NULL,
            vibration      REAL    NOT NULL,
            pression       REAL    NOT NULL,
            debit          REAL,
            notes          TEXT,
            horodatage     TEXT    NOT NULL,
            statut_alerte  TEXT    NOT NULL DEFAULT 'Normal'
        )
    """

    schema_alertes = """
        CREATE TABLE IF NOT EXISTS journal_alertes (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            releve_id      INTEGER REFERENCES releves_capteurs(id),
            turbine_id     TEXT    NOT NULL,
            niveau_alerte  TEXT    NOT NULL,
            message        TEXT    NOT NULL,
            horodatage     TEXT    NOT NULL
        )
    """

    # Index pour accélérer les requêtes par turbine et par date
    index_turbine = """
        CREATE INDEX IF NOT EXISTS idx_turbine_id
        ON releves_capteurs(turbine_id)
    """
    index_date = """
        CREATE INDEX IF NOT EXISTS idx_horodatage
        ON releves_capteurs(horodatage)
    """

    try:
        with obtenir_connexion() as conn:
            conn.execute(schema_releves)
            conn.execute(schema_alertes)
            conn.execute(index_turbine)
            conn.execute(index_date)
            conn.commit()
        logger.info("✅ Base de données initialisée avec succès.")
    except sqlite3.Error as e:
        logger.error(f"❌ Échec de l'initialisation de la BDD : {e}")
        raise


# ─────────────────────────────────────────────
# Insertion d'un nouveau relevé
# ─────────────────────────────────────────────
def inserer_releve(releve: ReleverCapteur) -> int:
    """
    Insère un relevé validé dans la base de données.
    Crée automatiquement une alerte si le statut est anormal.

    Retourne l'ID du relevé inséré.
    """
    statut = calculer_statut(releve.temperature, releve.vibration, releve.pression)

    requete_insertion = """
        INSERT INTO releves_capteurs
            (turbine_id, technicien, temperature, vibration,
             pression, debit, notes, horodatage, statut_alerte)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """

    valeurs = (
        releve.turbine_id.value,
        releve.technicien.value,
        releve.temperature,
        releve.vibration,
        releve.pression,
        releve.debit,
        releve.notes,
        releve.horodatage.isoformat(),
        statut,
    )

    try:
        with obtenir_connexion() as conn:
            curseur = conn.execute(requete_insertion, valeurs)
            releve_id = curseur.lastrowid

            # ── Enregistrer une alerte si statut anormal ──────────
            if statut in ("Avertissement", "Critique"):
                message = (
                    f"Turbine {releve.turbine_id.value} : "
                    f"T={releve.temperature}°C | V={releve.vibration}mm/s | "
                    f"P={releve.pression}bar — Statut : {statut}"
                )
                conn.execute(
                    """INSERT INTO journal_alertes
                       (releve_id, turbine_id, niveau_alerte, message, horodatage)
                       VALUES (?, ?, ?, ?, ?)""",
                    (releve_id, releve.turbine_id.value, statut,
                     message, datetime.now().isoformat()),
                )

            conn.commit()
            logger.info(f"✅ Relevé #{releve_id} inséré — Statut : {statut}")
            return releve_id

    except sqlite3.Error as e:
        logger.error(f"❌ Erreur lors de l'insertion du relevé : {e}")
        raise


# ─────────────────────────────────────────────
# Lecture des relevés récents
# ─────────────────────────────────────────────
def lire_releves(
    limite: int = 100,
    turbine_id: Optional[str] = None,
    statut: Optional[str] = None,
) -> List[dict]:
    """
    Récupère les derniers relevés depuis la BDD.
    Filtres optionnels : turbine_id, statut d'alerte.
    """
    requete = "SELECT * FROM releves_capteurs WHERE 1=1"
    parametres: list = []

    if turbine_id and turbine_id != "Toutes":
        requete += " AND turbine_id = ?"
        parametres.append(turbine_id)

    if statut and statut != "Tous":
        requete += " AND statut_alerte = ?"
        parametres.append(statut)

    requete += " ORDER BY horodatage DESC LIMIT ?"
    parametres.append(limite)

    try:
        with obtenir_connexion() as conn:
            curseur = conn.execute(requete, parametres)
            resultats = [dict(row) for row in curseur.fetchall()]
        return resultats
    except sqlite3.Error as e:
        logger.error(f"❌ Erreur lors de la lecture des relevés : {e}")
        return []


# ─────────────────────────────────────────────
# Statistiques agrégées par turbine
# ─────────────────────────────────────────────
def obtenir_statistiques() -> List[dict]:
    """
    Calcule les statistiques min/max/moyenne par turbine
    pour le tableau de bord.
    """
    requete = """
        SELECT
            turbine_id,
            COUNT(*)            AS nb_releves,
            ROUND(AVG(temperature), 2)  AS temp_moy,
            ROUND(MAX(temperature), 2)  AS temp_max,
            ROUND(AVG(vibration), 2)    AS vib_moy,
            ROUND(MAX(vibration), 2)    AS vib_max,
            ROUND(AVG(pression), 2)     AS pres_moy,
            ROUND(MAX(pression), 2)     AS pres_max,
            SUM(CASE WHEN statut_alerte = 'Critique'      THEN 1 ELSE 0 END) AS nb_critiques,
            SUM(CASE WHEN statut_alerte = 'Avertissement' THEN 1 ELSE 0 END) AS nb_avertissements
        FROM releves_capteurs
        GROUP BY turbine_id
        ORDER BY turbine_id
    """
    try:
        with obtenir_connexion() as conn:
            curseur = conn.execute(requete)
            return [dict(row) for row in curseur.fetchall()]
    except sqlite3.Error as e:
        logger.error(f"❌ Erreur lors du calcul des statistiques : {e}")
        return []


# ─────────────────────────────────────────────
# Lecture du journal d'alertes
# ─────────────────────────────────────────────
def lire_alertes(limite: int = 20) -> List[dict]:
    """Retourne les dernières alertes enregistrées."""
    requete = """
        SELECT * FROM journal_alertes
        ORDER BY horodatage DESC LIMIT ?
    """
    try:
        with obtenir_connexion() as conn:
            curseur = conn.execute(requete, (limite,))
            return [dict(row) for row in curseur.fetchall()]
    except sqlite3.Error as e:
        logger.error(f"❌ Erreur lecture alertes : {e}")
        return []


# ─────────────────────────────────────────────
# Compteur global (pour les métriques KPI)
# ─────────────────────────────────────────────
def compter_releves() -> dict:
    """Retourne les compteurs globaux pour les indicateurs KPI."""
    requete = """
        SELECT
            COUNT(*) AS total,
            SUM(CASE WHEN statut_alerte = 'Normal'        THEN 1 ELSE 0 END) AS normal,
            SUM(CASE WHEN statut_alerte = 'Avertissement' THEN 1 ELSE 0 END) AS avertissement,
            SUM(CASE WHEN statut_alerte = 'Critique'      THEN 1 ELSE 0 END) AS critique
        FROM releves_capteurs
    """
    try:
        with obtenir_connexion() as conn:
            row = conn.execute(requete).fetchone()
            return dict(row) if row else {"total": 0, "normal": 0,
                                          "avertissement": 0, "critique": 0}
    except sqlite3.Error as e:
        logger.error(f"❌ Erreur comptage : {e}")
        return {"total": 0, "normal": 0, "avertissement": 0, "critique": 0}
