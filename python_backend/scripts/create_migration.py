#!/usr/bin/env python
"""
Script para criar novas migrações do Alembic.
Uso: python scripts/create_migration.py "Descrição da migração"
"""

import sys
import os
import subprocess
from pathlib import Path

def create_migration(description=None):
    """Cria uma nova migração do Alembic."""
    # Obter o diretório raiz do projeto
    root_dir = Path(__file__).parent.parent
    
    # Verificar se foi fornecida uma descrição
    if not description:
        description = "Auto generated migration"
    
    print(f"Criando migração: '{description}'")
    
    # Executar o comando do Alembic para gerar a migração
    cmd = [
        sys.executable, 
        "-m", 
        "alembic", 
        "revision", 
        "--autogenerate", 
        "-m", 
        description
    ]
    
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
            
        print("Migração criada com sucesso!")
        
    except subprocess.CalledProcessError as e:
        print(f"Erro ao criar migração: {e}")
        if e.stdout:
            print("Saída:")
            print(e.stdout)
        if e.stderr:
            print("Erros:")
            print(e.stderr)
        return False
    
    return True

if __name__ == "__main__":
    # Obter a descrição da migração da linha de comando
    description = None
    if len(sys.argv) > 1:
        description = sys.argv[1]
    
    # Criar a migração
    success = create_migration(description)
    
    # Sair com o código apropriado
    sys.exit(0 if success else 1) 