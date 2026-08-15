"""Findling ExApp backend.

Zero-config search backend for Nextcloud, deployed through AppAPI as the
external app ``findling_backend`` and driven by the PHP companion ``findling``.

The version is shared with the PHP companion on purpose: the Nextcloud App Store
ships both parts as separate entries, and users must not be able to drift them
apart.
"""

__version__ = "0.1.0"
