#!/usr/bin/env python3
"""
Helpers for deterministic UUIDs.
"""

import uuid
NS_DRUG      = uuid.uuid5(uuid.NAMESPACE_URL,  "fdadata/drug")
NS_MOLECULE  = uuid.uuid5(uuid.NAMESPACE_URL,  "fdadata/molecule")
NS_INDIC     = uuid.uuid5(uuid.NAMESPACE_URL,  "fdadata/indication")
NS_MOA       = uuid.uuid5(uuid.NAMESPACE_URL,  "fdadata/moa")
NS_ENDPOINT  = uuid.uuid5(uuid.NAMESPACE_URL,  "fdadata/endpoint")
NS_ADVERSE   = uuid.uuid5(uuid.NAMESPACE_URL,  "fdadata/adverse")

def make_uuid(ns, value: str) -> str:
    return str(uuid.uuid5(ns, value.lower().strip()))
