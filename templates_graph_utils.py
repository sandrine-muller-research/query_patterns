#!/usr/bin/env python3
"""
templates_graph utils
"""
import hashlib

def generate_template_id(subject, predicate, object_):
    """Create a reproducible template ID using SHA1"""
    raw = f"{subject}|{predicate}|{object_}".encode()
    return hashlib.sha1(raw).hexdigest()[:16]