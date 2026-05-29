# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec for Forge Core CLI.
Compiles the Python engine into a single standalone binary.

Build:
  pip install pyinstaller
  pyinstaller forge-core.spec

Output: dist/forge-core (single binary, ~50-80MB)
"""

import sys
from pathlib import Path

block_cipher = None

# Collect all forge_core modules
a = Analysis(
    ['forge_core/cli.py'],
    pathex=[],
    binaries=[],
    datas=[
        # Include prompt templates if bundled
        ('../.github/prompts', 'prompts'),
        ('../knowledge-packs', 'knowledge-packs'),
    ],
    hiddenimports=[
        'forge_core',
        'forge_core.orchestrator',
        'forge_core.config',
        'forge_core.auth',
        'forge_core.ai.provider',
        'forge_core.ai.prompts',
        'forge_core.ai.structured',
        'forge_core.phases.detect_stack',
        'forge_core.phases.exclusion_scan',
        'forge_core.phases.analyze_project',
        'forge_core.phases.journey_mapping',
        'forge_core.phases.audit_tests',
        'forge_core.phases.fix_broken',
        'forge_core.phases.generate_tests',
        'forge_core.phases.compile_fix',
        'forge_core.phases.coverage_report',
        'forge_core.phases.self_learn',
        'forge_core.core.file_manager',
        'forge_core.core.coverage',
        'forge_core.core.agent_manager',
        'forge_core.models.config',
        'forge_core.models.project',
        'forge_core.models.dto',
        'forge_core.models.test_result',
        'forge_core.utils.logger',
        'forge_core.utils.shell',
        'forge_core.utils.tokens',
        'forge_core.utils.reporter',
        # Dependencies
        'litellm',
        'instructor',
        'typer',
        'rich',
        'yaml',
        'tiktoken',
        'httpx',
        'pydantic',
        'tiktoken_ext',
        'tiktoken_ext.openai_public',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'matplotlib',
        'scipy',
        'numpy',
        'pandas',
        'pytest',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='forge-core',
    debug=False,
    bootloader_ignore_signals=False,
    strip=True,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
