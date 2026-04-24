"""
models.py — Modèles de validation des données avec Pydantic
Secteur : Turbines Hydrauliques (centrales hydroélectriques)
Auteur  : Ingénieur Logiciel Senior
"""

from pydantic import BaseModel, Field, field_validator, model_validator
from datetime import datetime
from enum import Enum
from typing import Optional


# ─────────────────────────────────────────────
# Énumération des turbines disponibles en usine
# ─────────────────────────────────────────────
class TurbineID(str, Enum):
    TURBINE_A = "TH-001-A"
    TURBINE_B = "TH-002-B"
    TURBINE_C = "TH-003-C"
    TURBINE_D = "TH-004-D"


# ─────────────────────────────────────────────
# Énumération des techniciens accrédités
# ─────────────────────────────────────────────
class Technicien(str, Enum):
    ALPHA  = "Mbarga Jean"
    BETA   = "Nkolo Sophie"
    GAMMA  = "Etoa Paul"
    DELTA  = "Fouda Alice"


# ─────────────────────────────────────────────
# Modèle principal : relevé de capteurs
# ─────────────────────────────────────────────
class ReleverCapteur(BaseModel):
    """
    Représente un relevé de données issues des capteurs
    d'une turbine hydraulique industrielle.
    """

    turbine_id    : TurbineID
    technicien    : Technicien
    temperature   : float = Field(..., ge=-20.0, le=200.0,
                                  description="Température en °C (plage : -20 à 200°C)")
    vibration     : float = Field(..., ge=0.0,  le=50.0,
                                  description="Vibration en mm/s (plage : 0 à 50 mm/s)")
    pression      : float = Field(..., ge=0.0,  le=500.0,
                                  description="Pression en bar (plage : 0 à 500 bar)")
    debit         : Optional[float] = Field(None, ge=0.0, le=10000.0,
                                  description="Débit en m³/h (optionnel)")
    notes         : Optional[str]  = Field(None, max_length=500,
                                  description="Observations du technicien (max 500 car.)")
    horodatage    : datetime       = Field(default_factory=datetime.now)

    # ── Validation : température anormalement haute ──────────────
    @field_validator("temperature")
    @classmethod
    def verifier_temperature(cls, v: float) -> float:
        if v > 150:
            raise ValueError(
                f"⚠ Température critique détectée : {v}°C — Arrêt d'urgence requis !"
            )
        return round(v, 2)

    # ── Validation : vibration critique ─────────────────────────
    @field_validator("vibration")
    @classmethod
    def verifier_vibration(cls, v: float) -> float:
        if v > 30:
            raise ValueError(
                f"⚠ Vibration excessive : {v} mm/s — Risque de dommage mécanique !"
            )
        return round(v, 2)

    # ── Validation : pression dangereuse ────────────────────────
    @field_validator("pression")
    @classmethod
    def verifier_pression(cls, v: float) -> float:
        if v > 400:
            raise ValueError(
                f"⚠ Surpression dangereuse : {v} bar — Vérifier les soupapes de sécurité !"
            )
        return round(v, 2)

    # ── Validation croisée : cohérence globale ───────────────────
    @model_validator(mode="after")
    def verifier_coherence(self) -> "ReleverCapteur":
        """
        Règle métier : si la pression est > 300 bar ET la température > 100°C
        en même temps, il s'agit d'une combinaison anormale.
        """
        if self.pression > 300 and self.temperature > 100:
            raise ValueError(
                "⚠ Combinaison anormale : pression > 300 bar ET température > 100°C "
                "simultanément. Inspection immédiate requise."
            )
        return self


# ─────────────────────────────────────────────
# Modèle de sortie (lecture depuis la BDD)
# ─────────────────────────────────────────────
class ReleverCapteurBDD(ReleverCapteur):
    """Modèle étendu incluant l'identifiant de base de données."""
    id            : int
    statut_alerte : str   # "Normal", "Avertissement", "Critique"

    class Config:
        from_attributes = True


# ─────────────────────────────────────────────
# Utilitaire : calculer le statut d'alerte
# ─────────────────────────────────────────────
def calculer_statut(temperature: float, vibration: float, pression: float) -> str:
    """
    Détermine le niveau d'alerte en fonction des seuils industriels.
    Retourne : "Normal", "Avertissement" ou "Critique"
    """
    critique     = temperature > 120 or vibration > 20 or pression > 350
    avertissement = temperature > 80  or vibration > 10 or pression > 200

    if critique:
        return "Critique"
    elif avertissement:
        return "Avertissement"
    return "Normal"
