"""
NexusCommerce AI - Channel3 Retail Search Provider
Integrates Channel3 Retail Search API for automated supplier & product discovery.
Supports Live API mode and Zero-Key Demo Mode.
"""

from typing import List, Dict, Any, Optional
import os
import httpx
import logging

logger = logging.getLogger("nexus.channel3_provider")


# Built-in High Quality Enterprise Catalog for Zero-Key Mode
DEFAULT_B2B_CATALOG: List[Dict[str, Any]] = [
    {
        "item_id": "CH3-ROUTER-100G",
        "vendor_id": "VEND-NEXIQ-410",
        "vendor_name": "NexIQ Enterprise Networks Ltd",
        "vendor_rating": 4.95,
        "title": "NexusEdge Pro 100G Modular Edge Router",
        "category": "Networking Hardware",
        "specifications": {
            "throughput": "100 Gbps wire-speed",
            "redundancy": "Dual Hot-Swap AC Power",
            "latency": "< 1.2 microseconds",
            "certifications": ["NEBS Level 3", "FIPS 140-3", "CE/FCC"],
        },
        "inventory_available": 340,
        "catalog_ask_price": 1250.0,
        "min_bulk_price": 1050.0,
        "lead_time_days": 5,
        "warranty_months": 36,
        "location": "San Jose, CA, USA",
    },
    {
        "item_id": "CH3-SWITCH-48P",
        "vendor_id": "VEND-OPTIX-882",
        "vendor_name": "Optix Core Infrastructure Systems",
        "vendor_rating": 4.88,
        "title": "OptixFabric 48-Port L3 Managed Spine Switch",
        "category": "Networking Hardware",
        "specifications": {
            "ports": "48x 25GbE SFP28 + 8x 100GbE QSFP28",
            "switching_capacity": "4.0 Tbps",
            "airflow": "Front-to-Back redundant fans",
        },
        "inventory_available": 180,
        "catalog_ask_price": 2850.0,
        "min_bulk_price": 2450.0,
        "lead_time_days": 7,
        "warranty_months": 24,
        "location": "Austin, TX, USA",
    },
    {
        "item_id": "CH3-NVME-ARRAY",
        "vendor_id": "VEND-SYNAPSE-109",
        "vendor_name": "Synapse Ultra Storage Corp",
        "vendor_rating": 4.92,
        "title": "Synapse 30TB Enterprise U.3 NVMe All-Flash Enclosure",
        "category": "Data Center Equipment",
        "specifications": {
            "read_iops": "1,400,000 IOPS",
            "endurance": "3 DWPD / 5 Years",
            "encryption": "Self-Encrypting TCG Opal",
        },
        "inventory_available": 75,
        "catalog_ask_price": 3400.0,
        "min_bulk_price": 2980.0,
        "lead_time_days": 6,
        "warranty_months": 60,
        "location": "Fremont, CA, USA",
    },
    {
        "item_id": "CH3-IOT-SENSE-5G",
        "vendor_id": "VEND-AURA-773",
        "vendor_name": "Aura Industrial Sensing Technologies",
        "vendor_rating": 4.79,
        "title": "AuraMesh Ruggedized 5G IoT Gateway Node",
        "category": "Edge Infrastructure",
        "specifications": {
            "connectivity": "5G Sub-6 + Wi-Fi 6E + LoRaWAN",
            "temp_range": "-40C to +85C IP67 Enclosure",
            "power": "PoE+ 802.3at / 12-24V DC",
        },
        "inventory_available": 600,
        "catalog_ask_price": 420.0,
        "min_bulk_price": 340.0,
        "lead_time_days": 4,
        "warranty_months": 24,
        "location": "Boulder, CO, USA",
    },
    {
        "item_id": "CH3-GPU-H100",
        "vendor_id": "VEND-LAMBDA-901",
        "vendor_name": "Lambda Cloud & Compute Systems",
        "vendor_rating": 4.98,
        "title": "NVIDIA H100 SXM5 80GB Server Node",
        "category": "AI Compute Hardware",
        "specifications": {
            "architecture": "Hopper 4nm SXM5",
            "memory": "80GB HBM3 (3.35 TB/s)",
            "interconnect": "NVLink 900 GB/s bidirectional",
            "certifications": ["Enterprise Tier-1", "RoHS"],
        },
        "inventory_available": 120,
        "catalog_ask_price": 33500.0,
        "min_bulk_price": 29800.0,
        "lead_time_days": 12,
        "warranty_months": 36,
        "location": "San Jose, CA, USA",
    },
    {
        "item_id": "CH3-DEFENSE-GW",
        "vendor_id": "VEND-TACTICAL-302",
        "vendor_name": "Titan Defense & Secure Communications",
        "vendor_rating": 4.94,
        "title": "Ruggedized Quantum-Resistant Tactical Gateway",
        "category": "Edge Infrastructure & Defense",
        "specifications": {
            "security": "FIPS 140-3 Level 4 Quantum-Resistant Kyber/Dilithium",
            "chassis": "MIL-STD-810H IP68 Submersible",
            "ports": "10GbE Ruggedized M12 Connectors",
        },
        "inventory_available": 85,
        "catalog_ask_price": 4850.0,
        "min_bulk_price": 4150.0,
        "lead_time_days": 5,
        "warranty_months": 36,
        "location": "Huntsville, AL, USA",
    },
    {
        "item_id": "CH3-DISP-5K",
        "vendor_id": "VEND-OPTIX-882",
        "vendor_name": "Optix Core Infrastructure Systems",
        "vendor_rating": 4.85,
        "title": "Nexus UltraWide 5K Thunderbolt Professional Displays",
        "category": "Enterprise Hardware",
        "specifications": {
            "panel": "5120x2160 Nano IPS 98% DCI-P3",
            "connectivity": "Thunderbolt 4 (96W PD Daisy Chain)",
            "warranty": "Advance Exchange 3-Year",
        },
        "inventory_available": 450,
        "catalog_ask_price": 890.0,
        "min_bulk_price": 790.0,
        "lead_time_days": 4,
        "warranty_months": 24,
        "location": "Austin, TX, USA",
    },
]


class Channel3Provider:
    def __init__(self, api_key: Optional[str] = None, demo_mode: bool = True):
        self.api_key = api_key or os.getenv("CHANNEL3_API_KEY", "")
        self.demo_mode = demo_mode or (not self.api_key)
        self.base_url = "https://api.channel3.ai/v1"
        self.catalog = list(DEFAULT_B2B_CATALOG)

    def is_demo_mode(self) -> bool:
        return self.demo_mode

    def set_demo_mode(self, enabled: bool):
        self.demo_mode = enabled

    async def search_catalog(
        self,
        query: str = "",
        category: Optional[str] = None,
        max_price: Optional[float] = None,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Search suppliers and products matching procurement criteria.
        """
        if self.demo_mode:
            results = []
            q_tokens = [t for t in query.lower().replace("-", " ").replace(":", " ").split() if len(t) > 2]
            
            for item in self.catalog:
                item_text = f"{item['title']} {item['category']} {item['vendor_name']}".lower()
                token_matches = sum(1 for t in q_tokens if t in item_text) if q_tokens else 1
                matches_cat = not category or category.lower() in item["category"].lower()
                matches_price = not max_price or item["min_bulk_price"] <= max_price * 1.35

                if token_matches > 0 or matches_cat:
                    score = token_matches * 10
                    if matches_cat:
                        score += 5
                    if matches_price:
                        score += 5
                    results.append((score, item))

            results.sort(key=lambda x: x[0], reverse=True)
            sorted_items = [r[1] for r in results]

            if not sorted_items:
                # If price is specified, select catalog item closest to requested price
                if max_price:
                    sorted_items = sorted(self.catalog, key=lambda x: abs(x["catalog_ask_price"] - max_price))
                else:
                    sorted_items = [self.catalog[0]]

            return sorted_items[:limit]

        # LIVE MODE
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        params = {"query": query, "limit": limit}
        if category:
            params["category"] = category
        if max_price:
            params["max_price"] = max_price

        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{self.base_url}/search", headers=headers, params=params, timeout=10.0)
            resp.raise_for_status()
            data = resp.json()
            return data.get("products", [])

    def get_item_by_id(self, item_id: str) -> Optional[Dict[str, Any]]:
        for item in self.catalog:
            if item["item_id"] == item_id:
                return item
        return None
