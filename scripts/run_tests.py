#!/usr/bin/env python3
"""
Test runner script for Nebraska Medicaid PDL Redline Skill.
Executes pytest test suite and reports test results.
"""

import os
import sys
import pytest

if __name__ == "__main__":
    # Prevent bytecode compilation from writing .pyc files
    sys.dont_write_bytecode = True
    os.environ["PYTHONDONTWRITEBYTECODE"] = "1"

    # Ensure sample PDF exists before testing
    sample_pdf = "examples/sample_pdl.pdf"
    if not os.path.exists(sample_pdf):
        print(f"Generating {sample_pdf} ...")
        from scripts.generate_sample_pdf import create_sample_pdl
        create_sample_pdl(sample_pdf)

    # Run pytest with cache disabled
    print("Running PDL Extractor Test Suite...\n" + "=" * 50)
    args = ["-v", "-p", "no:cacheprovider", "tests/test_pdl_extractor.py"] + sys.argv[1:]
    exit_code = pytest.main(args)
    sys.exit(exit_code)
