# ml/utils/mitre.py

from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class MITRETechnique:
    technique_id: str
    technique_name: str
    tactic: str
    description: str
    indicators: List[str]
    reference_url: str


# MITRE ATT&CK Ransomware-Relevant Techniques
MITRE_TECHNIQUES: Dict[str, MITRETechnique] = {
    "T1486": MITRETechnique(
        technique_id="T1486",
        technique_name="Data Encrypted for Impact",
        tactic="Impact",
        description=(
            "Adversaries may encrypt data on target systems or on large numbers of systems "
            "in a network to interrupt availability to system and network resources."
        ),
        indicators=[
            "high_entropy",
            "high_encryption_ratio",
            "mass_file_modification",
        ],
        reference_url="https://attack.mitre.org/techniques/T1486/",
    ),
    "T1490": MITRETechnique(
        technique_id="T1490",
        technique_name="Inhibit System Recovery",
        tactic="Impact",
        description=(
            "Adversaries may delete or remove built-in data and turn off services designed "
            "to aid in the recovery and restore of a victim's system."
        ),
        indicators=["high_delete_rate", "shadow_copy_deletion"],
        reference_url="https://attack.mitre.org/techniques/T1490/",
    ),
    "T1083": MITRETechnique(
        technique_id="T1083",
        technique_name="File and Directory Discovery",
        tactic="Discovery",
        description=(
            "Adversaries may enumerate files and directories or may search in specific "
            "locations of a host or network share for certain information within a file system."
        ),
        indicators=["high_directory_access", "high_read_operations"],
        reference_url="https://attack.mitre.org/techniques/T1083/",
    ),
    "T1222": MITRETechnique(
        technique_id="T1222",
        technique_name="File and Directory Permissions Modification",
        tactic="Defense Evasion",
        description=(
            "Adversaries may modify file or directory permissions/attributes to evade "
            "access control lists (ACLs) and access protected files."
        ),
        indicators=["permission_changes", "high_rename_operations"],
        reference_url="https://attack.mitre.org/techniques/T1222/",
    ),
    "T1560": MITRETechnique(
        technique_id="T1560",
        technique_name="Archive Collected Data",
        tactic="Collection",
        description=(
            "An adversary may compress and/or encrypt data that is collected prior to exfiltration."
        ),
        indicators=["high_entropy", "high_write_operations"],
        reference_url="https://attack.mitre.org/techniques/T1560/",
    ),
    "T1489": MITRETechnique(
        technique_id="T1489",
        technique_name="Service Stop",
        tactic="Impact",
        description=(
            "Adversaries may stop or disable services on a system to render those services "
            "unavailable to legitimate users."
        ),
        indicators=["high_cpu_usage", "process_termination"],
        reference_url="https://attack.mitre.org/techniques/T1489/",
    ),
    "T1078": MITRETechnique(
        technique_id="T1078",
        technique_name="Valid Accounts",
        tactic="Defense Evasion",
        description=(
            "Adversaries may obtain and abuse credentials of existing accounts as a means "
            "of gaining initial access, persistence, privilege escalation, or defense evasion."
        ),
        indicators=["unusual_process_behavior", "high_memory_usage"],
        reference_url="https://attack.mitre.org/techniques/T1078/",
    ),
}


class MITREMapper:
    """Maps detected behavioral indicators to MITRE ATT&CK techniques."""

    def __init__(self):
        self.techniques = MITRE_TECHNIQUES

    def map_features_to_techniques(
        self,
        features: Dict[str, float],
        prediction: int,
        probability: float,
        thresholds: Optional[Dict[str, float]] = None,
    ) -> List[MITRETechnique]:
        """
        Map feature values to relevant MITRE ATT&CK techniques.

        Args:
            features: Feature dictionary with values
            prediction: Model prediction (0=benign, 1=ransomware)
            probability: Prediction probability
            thresholds: Custom thresholds for feature analysis

        Returns:
            List of matched MITRE techniques
        """
        if prediction == 0 and probability < 0.5:
            return []

        thresholds = thresholds or {
            "entropy": 7.0,
            "encryption_ratio": 0.5,
            "files_modified_per_sec": 50,
            "files_deleted": 100,
            "rename_operations": 50,
            "directories_accessed": 100,
            "read_operations": 500,
            "write_operations": 200,
            "cpu_usage": 80,
            "memory_usage": 80,
        }

        active_indicators = self._extract_indicators(features, thresholds)
        matched_techniques = []

        for tech_id, technique in self.techniques.items():
            if any(ind in active_indicators for ind in technique.indicators):
                matched_techniques.append(technique)

        return matched_techniques

    def _extract_indicators(
        self, features: Dict[str, float], thresholds: Dict[str, float]
    ) -> List[str]:
        """Extract active behavioral indicators from features."""
        indicators = []

        if features.get("entropy", 0) >= thresholds.get("entropy", 7.0):
            indicators.append("high_entropy")

        if features.get("encryption_ratio", 0) >= thresholds.get("encryption_ratio", 0.5):
            indicators.append("high_encryption_ratio")

        if features.get("files_modified_per_sec", 0) >= thresholds.get("files_modified_per_sec", 50):
            indicators.append("mass_file_modification")

        if features.get("files_deleted", 0) >= thresholds.get("files_deleted", 100):
            indicators.append("high_delete_rate")

        if features.get("rename_operations", 0) >= thresholds.get("rename_operations", 50):
            indicators.append("high_rename_operations")

        if features.get("directories_accessed", 0) >= thresholds.get("directories_accessed", 100):
            indicators.append("high_directory_access")

        if features.get("read_operations", 0) >= thresholds.get("read_operations", 500):
            indicators.append("high_read_operations")

        if features.get("write_operations", 0) >= thresholds.get("write_operations", 200):
            indicators.append("high_write_operations")

        if features.get("cpu_usage", 0) >= thresholds.get("cpu_usage", 80):
            indicators.append("high_cpu_usage")

        if features.get("memory_usage", 0) >= thresholds.get("memory_usage", 80):
            indicators.append("high_memory_usage")

        return indicators

    def get_technique_by_id(self, technique_id: str) -> Optional[MITRETechnique]:
        """Retrieve a technique by its MITRE ID."""
        return self.techniques.get(technique_id)

    def format_report(self, techniques: List[MITRETechnique]) -> str:
        """Format matched techniques into a human-readable report."""
        if not techniques:
            return "No MITRE ATT&CK techniques matched."

        lines = ["=== MITRE ATT&CK Technique Mapping ===\n"]
        for technique in techniques:
            lines.append(f"[{technique.technique_id}] {technique.technique_name}")
            lines.append(f"  Tactic     : {technique.tactic}")
            lines.append(f"  Description: {technique.description[:120]}...")
            lines.append(f"  Reference  : {technique.reference_url}")
            lines.append("")

        return "\n".join(lines)