"""
Email validation and formatting utilities for appointment booking.
"""

import re
from typing import Tuple


def validate_email(email: str) -> Tuple[bool, str]:
    """
    Validate email format and normalize it.

    Args:
        email: Email address to validate

    Returns:
        Tuple of (is_valid, normalized_email)
        - is_valid: True if email matches standard format
        - normalized_email: Lowercase, stripped version of email

    Example:
        >>> validate_email("John.Doe@Example.COM")
        (True, "john.doe@example.com")
        >>> validate_email("invalid-email")
        (False, "invalid-email")
    """
    # Remove spaces, convert to lowercase
    email = email.strip().lower()

    # Basic email regex pattern
    # Matches: username@domain.tld
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

    if re.match(pattern, email):
        return True, email
    return False, email


def spell_out_email(email: str) -> str:
    """
    Convert email to spelled-out format for voice confirmation.

    This function helps verify emails character-by-character in voice conversations
    where STT may mishear characters.

    Args:
        email: Email address to spell out

    Returns:
        Spelled-out version with characters separated by hyphens,
        '@' replaced with 'at', and '.' replaced with 'dot'

    Example:
        >>> spell_out_email("john@example.com")
        'j-o-h-n at example dot com'
        >>> spell_out_email("user.name@company.co.uk")
        'u-s-e-r dot n-a-m-e at company dot co dot uk'
    """
    if '@' not in email:
        # If no @ symbol, just spell out the whole thing
        return '-'.join(list(email))

    # Split at @ symbol
    local, domain = email.split('@', 1)

    # Spell out local part character by character, including dots
    local_parts = []
    current_word = []

    for char in local:
        if char == '.':
            if current_word:
                local_parts.append('-'.join(current_word))
                current_word = []
            local_parts.append('dot')
        else:
            current_word.append(char)

    if current_word:
        local_parts.append('-'.join(current_word))

    local_spelled = ' '.join(local_parts)

    # Handle domain - replace dots with 'dot'
    domain_spelled = domain.replace('.', ' dot ')

    return f"{local_spelled} at {domain_spelled}"
