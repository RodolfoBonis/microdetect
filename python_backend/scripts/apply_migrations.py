#!/usr/bin/env python
"""
Script para aplicar migrações existentes do Alembic.
Uso: python scripts/apply_migrations.py
"""

import sys
import os
import subprocess
from pathlib import Path

def apply_migrations():
    """Aplica as migrações pendentes do Alembic."""
    # Obter o diretório raiz do projeto
    root_dir = Path(__file__).parent.parent
    
    print("Aplicando migrações pendentes...")
    
    # Executar o comando do Alembic para aplicar as migrações
    cmd = [sys.executable, "-m", "alembic", "upgrade", "head"]
    
    try:
        result = subprocess.run(
            cmd, 
            cwd=root_dir, 
            capture_output=True, 
            text=True, 
            check=True
        )
        
        # Exibir saída do comando
        if result.stdout:
            print("Saída:")
            print(result.stdout)
            
        # Exibir erros, se houver
        if result.stderr:
            print("Erros:")
            print(result.stderr)
            
        print("Migrações aplicadas com sucesso!")
        
    except subprocess.CalledProcessError as e:
        print(f"Erro ao aplicar migrações: {e}")
        if e.stdout:
            print("Saída:")
            print(e.stdout)
        if e.stderr:
            print("Erros:")
            print(e.stderr)
        return False
    
    return True

if __name__ == "__main__":
    # Aplicar as migrações
    success = apply_migrations()
    
    # Sair com o código apropriado
    sys.exit(0 if success else 1) 