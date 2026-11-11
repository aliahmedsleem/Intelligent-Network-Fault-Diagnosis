"""Transparent link-budget calculations for virtual-network experiment design.

These are deterministic *engineering estimates*, not physical-layer packet
simulation, channel measurements, or calibrated hardware predictions.
"""
from __future__ import annotations

import math
from typing import Literal
from pydantic import BaseModel, Field, model_validator


class FiberBudget(BaseModel):
    medium: Literal["fiber"] = "fiber"
    length_km: float = Field(gt=0, le=500)
    wavelength_nm: Literal[1310, 1550] = 1550
    tx_power_dbm: float = Field(ge=-40, le=30)
    receiver_sensitivity_dbm: float = Field(ge=-50, le=10)
    connector_count: int = Field(default=2, ge=0, le=100)
    connector_loss_db: float = Field(default=0.3, ge=0, le=5)
    splice_count: int = Field(default=0, ge=0, le=1000)
    splice_loss_db: float = Field(default=0.1, ge=0, le=2)
    engineering_margin_db: float = Field(default=3, ge=0, le=30)
    attenuation_db_per_km: float | None = Field(default=None, ge=0, le=5)


class RadioBudget(BaseModel):
    medium: Literal["wifi_2_4", "wifi_5", "microwave"]
    distance_m: float = Field(gt=0, le=100000)
    frequency_ghz: float = Field(gt=0, le=100)
    tx_power_dbm: float = Field(ge=-60, le=60)
    tx_gain_dbi: float = Field(default=0, ge=-30, le=70)
    rx_gain_dbi: float = Field(default=0, ge=-30, le=70)
    rx_sensitivity_dbm: float = Field(ge=-130, le=0)
    additional_loss_db: float = Field(default=0, ge=0, le=100)
    fade_margin_db: float = Field(default=10, ge=0, le=60)

    @model_validator(mode="after")
    def frequency_matches_band(self):
        bands = {
            "wifi_2_4": (2.4, 2.5),
            "wifi_5": (5.15, 5.9),
            "microwave": (1.0, 100.0),
        }
        low, high = bands[self.medium]
        if not low <= self.frequency_ghz <= high:
            raise ValueError("Frequency does not match selected medium")
        return self


class MediumBudgetRequest(BaseModel):
    link: FiberBudget | RadioBudget = Field(discriminator="medium")


def calculate_budget(request: MediumBudgetRequest) -> dict:
    link = request.link
    if isinstance(link, FiberBudget):
        attenuation = link.attenuation_db_per_km
        if attenuation is None:
            attenuation = 0.35 if link.wavelength_nm == 1310 else 0.22
        attenuation_total = attenuation * link.length_km
        connectors = link.connector_count * link.connector_loss_db
        splices = link.splice_count * link.splice_loss_db
        path_loss = attenuation_total + connectors + splices
        received = link.tx_power_dbm - path_loss
        margin = received - link.receiver_sensitivity_dbm - link.engineering_margin_db
        propagation_ms = link.length_km / 200000 * 1000
        components = {
            "fiber_attenuation_db": round(attenuation_total, 5),
            "connector_loss_db": round(connectors, 5),
            "splice_loss_db": round(splices, 5),
            "engineering_margin_db": link.engineering_margin_db,
        }
        method = "single-mode fiber attenuation and component loss budget"
    else:
        # Friis free-space path loss with distance in km, frequency in MHz.
        distance_km = link.distance_m / 1000
        frequency_mhz = link.frequency_ghz * 1000
        fspl = 32.44 + 20 * math.log10(distance_km) + 20 * math.log10(frequency_mhz)
        path_loss = fspl + link.additional_loss_db
        received = link.tx_power_dbm + link.tx_gain_dbi + link.rx_gain_dbi - path_loss
        margin = received - link.rx_sensitivity_dbm - link.fade_margin_db
        propagation_ms = link.distance_m / 299792458 * 1000
        components = {
            "free_space_path_loss_db": round(fspl, 5),
            "additional_loss_db": link.additional_loss_db,
            "fade_margin_db": link.fade_margin_db,
        }
        method = "Friis free-space path loss; ideal line of sight with manually specified extra loss"
    return {
        "mode": "analytical_link_budget",
        "medium": link.medium,
        "method": method,
        "path_loss_db": round(path_loss, 5),
        "received_power_dbm": round(received, 5),
        "link_margin_db": round(margin, 5),
        "margin_sufficient": margin >= 0,
        "one_way_propagation_ms": round(propagation_ms, 8),
        "components": components,
        "limitations": [
            "Engineering budget only; no measured throughput, BER, PER, or packet loss.",
            "Margin threshold is not a probabilistic outage prediction.",
            "No fading distribution, obstruction geometry, interference, or MAC scheduling.",
            "Use ns-3 or calibrated field data for PHY/MAC performance validation.",
        ],
    }
