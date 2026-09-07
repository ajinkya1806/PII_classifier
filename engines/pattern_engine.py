"""
Pattern Engine — regex/format + checksum validators for every subtype
that has a detectable format pattern.

Confidence = percentage of sampled values matching the pattern.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class PatternMatch:
    """Result of pattern matching for a field."""
    subtype: str
    pattern_ref: str
    confidence: float
    matched_count: int
    total_count: int
    validator_name: str


# ──────────────────────────────────────────────────────────────
# Validator Functions
# Each returns True if the value matches the expected pattern.
# ──────────────────────────────────────────────────────────────


def _luhn_check(number: str) -> bool:
    """Luhn algorithm for credit card / IMEI validation."""
    digits = [int(d) for d in number if d.isdigit()]
    if len(digits) < 2:
        return False
    checksum = 0
    reverse_digits = digits[::-1]
    for i, d in enumerate(reverse_digits):
        if i % 2 == 1:
            d *= 2
            if d > 9:
                d -= 9
        checksum += d
    return checksum % 10 == 0


# Verhoeff algorithm tables for Aadhaar validation
_VERHOEFF_D = [
    [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
    [1, 2, 3, 4, 0, 6, 7, 8, 9, 5],
    [2, 3, 4, 0, 1, 7, 8, 9, 5, 6],
    [3, 4, 0, 1, 2, 8, 9, 5, 6, 7],
    [4, 0, 1, 2, 3, 9, 5, 6, 7, 8],
    [5, 9, 8, 7, 6, 0, 4, 3, 2, 1],
    [6, 5, 9, 8, 7, 1, 0, 4, 3, 2],
    [7, 6, 5, 9, 8, 2, 1, 0, 4, 3],
    [8, 7, 6, 5, 9, 3, 2, 1, 0, 4],
    [9, 8, 7, 6, 5, 4, 3, 2, 1, 0],
]

_VERHOEFF_P = [
    [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
    [1, 5, 7, 6, 2, 8, 3, 0, 9, 4],
    [5, 8, 0, 3, 7, 9, 6, 1, 4, 2],
    [8, 9, 1, 6, 0, 4, 3, 5, 2, 7],
    [9, 4, 5, 3, 1, 2, 6, 8, 7, 0],
    [4, 2, 8, 6, 5, 7, 3, 9, 0, 1],
    [2, 7, 9, 3, 8, 0, 6, 4, 1, 5],
    [7, 0, 4, 6, 9, 1, 3, 2, 5, 8],
]

_VERHOEFF_INV = [0, 4, 3, 2, 1, 5, 6, 7, 8, 9]


def _verhoeff_validate(number: str) -> bool:
    """Validate a number using Verhoeff checksum algorithm."""
    digits = [int(d) for d in number if d.isdigit()]
    c = 0
    for i, digit in enumerate(reversed(digits)):
        c = _VERHOEFF_D[c][_VERHOEFF_P[i % 8][digit]]
    return c == 0


def validate_aadhaar(value: str) -> bool:
    """Validate Aadhaar number: 12 digits, starts with 2-9, Verhoeff checksum."""
    clean = re.sub(r'[\s\-]', '', value.strip())
    if not re.match(r'^[2-9]\d{11}$', clean):
        return False
    return _verhoeff_validate(clean)


def validate_pan(value: str) -> bool:
    """Validate PAN: ABCPD1234E format (5 letters, 4 digits, 1 letter)."""
    clean = value.strip().upper()
    return bool(re.match(r'^[A-Z]{3}[CPHFATBLJG][A-Z]\d{4}[A-Z]$', clean))


def validate_passport(value: str) -> bool:
    """Validate Indian passport: 1 letter + 7 digits."""
    clean = value.strip().upper()
    return bool(re.match(r'^[A-Z]\d{7}$', clean))


def validate_voter_id(value: str) -> bool:
    """Validate Voter ID (EPIC): 3 letters + 7 digits."""
    clean = value.strip().upper()
    return bool(re.match(r'^[A-Z]{3}\d{7}$', clean))


def validate_driving_license(value: str) -> bool:
    """Validate Indian driving license: 2 letters + 2 digits + space? + 11 digits (approx)."""
    clean = re.sub(r'[\s\-]', '', value.strip().upper())
    return bool(re.match(r'^[A-Z]{2}\d{13}$', clean))


def validate_ifsc(value: str) -> bool:
    """Validate IFSC code: 4 letters + 0 + 6 alphanumeric."""
    clean = value.strip().upper()
    return bool(re.match(r'^[A-Z]{4}0[A-Z0-9]{6}$', clean))


def validate_credit_card(value: str) -> bool:
    """Validate credit/debit card: 13-19 digits + Luhn check."""
    clean = re.sub(r'[\s\-]', '', value.strip())
    if not re.match(r'^\d{13,19}$', clean):
        return False
    return _luhn_check(clean)


def validate_cvv(value: str) -> bool:
    """Validate CVV: 3 or 4 digits."""
    clean = value.strip()
    return bool(re.match(r'^\d{3,4}$', clean))


def validate_card_expiry(value: str) -> bool:
    """Validate card expiry: MM/YY or MM/YYYY."""
    clean = value.strip()
    return bool(re.match(r'^(0[1-9]|1[0-2])\/(\d{2}|\d{4})$', clean))


def validate_email(value: str) -> bool:
    """Validate email address (simplified RFC 5322)."""
    clean = value.strip().lower()
    return bool(re.match(
        r'^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$', clean
    ))


def validate_phone_india(value: str) -> bool:
    """Validate Indian phone/mobile number: optional +91, starts with 6-9, 10 digits."""
    clean = re.sub(r'[\s\-\(\)]', '', value.strip())
    return bool(re.match(r'^(\+91)?[6-9]\d{9}$', clean))


def validate_pincode(value: str) -> bool:
    """Validate Indian pincode: 6 digits, first digit 1-9."""
    clean = value.strip()
    return bool(re.match(r'^[1-9]\d{5}$', clean))


def validate_ip_address(value: str) -> bool:
    """Validate IPv4 or IPv6 address."""
    clean = value.strip()
    # IPv4
    if re.match(r'^(\d{1,3}\.){3}\d{1,3}$', clean):
        parts = clean.split('.')
        return all(0 <= int(p) <= 255 for p in parts)
    # IPv6 (simplified)
    if re.match(r'^([0-9a-fA-F]{0,4}:){2,7}[0-9a-fA-F]{0,4}$', clean):
        return True
    return False


def validate_mac_address(value: str) -> bool:
    """Validate MAC address: XX:XX:XX:XX:XX:XX or XX-XX-XX-XX-XX-XX."""
    clean = value.strip()
    return bool(re.match(
        r'^([0-9A-Fa-f]{2}[:\-]){5}[0-9A-Fa-f]{2}$', clean
    ))


def validate_imei(value: str) -> bool:
    """Validate IMEI: 15 digits + Luhn check."""
    clean = re.sub(r'[\s\-]', '', value.strip())
    if not re.match(r'^\d{15}$', clean):
        return False
    return _luhn_check(clean)


def validate_upi_vpa(value: str) -> bool:
    """Validate UPI VPA: user@provider format."""
    clean = value.strip().lower()
    return bool(re.match(r'^[\w.\-]+@[a-z]+$', clean))


def validate_dob(value: str) -> bool:
    """Validate date of birth in common formats: DD/MM/YYYY, DD-MM-YYYY, YYYY-MM-DD."""
    clean = value.strip()
    patterns = [
        r'^\d{2}/\d{2}/\d{4}$',       # DD/MM/YYYY
        r'^\d{2}-\d{2}-\d{4}$',       # DD-MM-YYYY
        r'^\d{4}-\d{2}-\d{2}$',       # YYYY-MM-DD
        r'^\d{2}/\d{2}/\d{2}$',       # DD/MM/YY
        r'^\d{2}\s+[A-Za-z]{3}\s+\d{4}$',  # DD Mon YYYY
    ]
    return any(re.match(p, clean) for p in patterns)


def validate_vehicle_reg(value: str) -> bool:
    """Validate Indian vehicle registration: XX00XX0000 or XX00 XX 0000."""
    clean = re.sub(r'[\s\-]', '', value.strip().upper())
    return bool(re.match(r'^[A-Z]{2}\d{2}[A-Z]{1,3}\d{4}$', clean))


def validate_bank_account(value: str) -> bool:
    """Validate bank account number: 9-18 digits (India bank account range)."""
    clean = re.sub(r'[\s\-]', '', value.strip())
    return bool(re.match(r'^\d{9,18}$', clean))


def validate_crypto_wallet(value: str) -> bool:
    """Validate crypto wallet: Bitcoin or Ethereum address."""
    clean = value.strip()
    # Bitcoin (P2PKH or P2SH)
    if re.match(r'^[13][a-km-zA-HJ-NP-Z1-9]{25,34}$', clean):
        return True
    # Bitcoin Bech32
    if re.match(r'^bc1[a-zA-HJ-NP-Z0-9]{25,39}$', clean):
        return True
    # Ethereum
    if re.match(r'^0x[0-9a-fA-F]{40}$', clean):
        return True
    return False


def validate_abha_id(value: str) -> bool:
    """Validate ABHA (Ayushman Bharat Health Account) ID: 14 digits."""
    clean = re.sub(r'[\s\-]', '', value.strip())
    return bool(re.match(r'^\d{14}$', clean))


# ──────────────────────────────────────────────────────────────
# Validator Registry
# Maps pattern_ref (from taxonomy.yaml) → validator function
# ──────────────────────────────────────────────────────────────

VALIDATORS: Dict[str, Callable[[str], bool]] = {
    "aadhaar": validate_aadhaar,
    "pan": validate_pan,
    "passport": validate_passport,
    "voter_id": validate_voter_id,
    "driving_license": validate_driving_license,
    "ifsc": validate_ifsc,
    "credit_card": validate_credit_card,
    "cvv": validate_cvv,
    "card_expiry": validate_card_expiry,
    "email": validate_email,
    "phone_india": validate_phone_india,
    "pincode": validate_pincode,
    "ip_address": validate_ip_address,
    "mac_address": validate_mac_address,
    "imei": validate_imei,
    "upi_vpa": validate_upi_vpa,
    "dob": validate_dob,
    "vehicle_reg": validate_vehicle_reg,
    "bank_account": validate_bank_account,
    "crypto_wallet": validate_crypto_wallet,
    "abha_id": validate_abha_id,
}


class PatternEngine:
    """
    Pattern-based detection engine.

    For each subtype that has a pattern_ref in taxonomy.yaml, runs the
    corresponding validator against sampled values and computes confidence
    as the ratio of matching values.
    """

    def __init__(self):
        self._validators = VALIDATORS

    def classify(
        self,
        pattern_ref: str,
        sample_values: List[str],
    ) -> Optional[PatternMatch]:
        """
        Run the pattern validator for a given pattern_ref against sample values.

        Returns PatternMatch with confidence = matched_count / total_count,
        or None if pattern_ref has no validator or no samples provided.
        """
        if not pattern_ref or pattern_ref not in self._validators:
            return None

        if not sample_values:
            return None

        validator = self._validators[pattern_ref]
        validator_name = validator.__name__

        matched = 0
        total = 0
        for value in sample_values:
            if value and value.strip():
                total += 1
                try:
                    if validator(value):
                        matched += 1
                except Exception as e:
                    logger.debug(
                        f"Validator {validator_name} error on value: {e}"
                    )

        if total == 0:
            return None

        confidence = round(matched / total, 4)

        logger.debug(
            f"Pattern engine ({pattern_ref}): {matched}/{total} matched "
            f"→ confidence={confidence:.2f}"
        )

        return PatternMatch(
            subtype="",  # Will be filled by scorer from taxonomy
            pattern_ref=pattern_ref,
            confidence=confidence,
            matched_count=matched,
            total_count=total,
            validator_name=validator_name,
        )

    def classify_all(
        self,
        sample_values: List[str],
    ) -> List[PatternMatch]:
        """
        Run ALL validators against sample values and return any that have
        non-zero matches. Useful when we don't know the pattern_ref upfront.
        """
        results = []
        for ref, validator in self._validators.items():
            match = self.classify(ref, sample_values)
            if match and match.confidence > 0:
                results.append(match)

        results.sort(key=lambda m: m.confidence, reverse=True)
        return results

    def get_available_validators(self) -> List[str]:
        """Return list of available pattern_ref keys."""
        return list(self._validators.keys())
