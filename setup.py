"""
Configuração de instalação para o pacote MicroDetect.
"""

from setuptools import setup, find_packages
import os
import re
import glob


def get_version():
    """Extrair versão do módulo __init__.py."""
    init_path = os.path.join(os.path.dirname(__file__), 'microdetect', '__init__.py')
    with open(init_path, 'r') as f:
        version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]", f.read(), re.M)
        if version_match:
            return version_match.group(1)
        raise RuntimeError("Versão não encontrada!")


def read_requirements():
    """Ler requisitos de dependências do arquivo requirements.txt."""
    with open('requirements.txt', 'r') as f:
        return [line.strip() for line in f if line.strip() and not line.startswith('#')]


# Collect all documentation files
doc_files = glob.glob('docs/**/*.md', recursive=True)
doc_files += glob.glob('docs/**/*.html', recursive=True)
doc_files += glob.glob('docs/**/*.css', recursive=True)
doc_files += glob.glob('docs/**/*.js', recursive=True)
doc_files += glob.glob('docs/**/*.png', recursive=True)
doc_files += glob.glob('docs/**/*.jpg', recursive=True)
doc_files += glob.glob('docs/**/*.svg', recursive=True)

# Organize doc files by directory structure
doc_dirs = {}
for doc_file in doc_files:
    # Extrair diretório relativo
    rel_dir = os.path.dirname(doc_file)
    if rel_dir not in doc_dirs:
        doc_dirs[rel_dir] = []
    doc_dirs[rel_dir].append(doc_file)

# Create data_files entries for each directory
doc_data_files = []
for rel_dir, files in doc_dirs.items():
    install_dir = os.path.join('share/microdetect', rel_dir)
    doc_data_files.append((install_dir, files))

setup(
    name="microdetect",
    version=get_version(),
    description="Detecção e classificação de microorganismos com visão computacional",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="MicroDetect Team",
    author_email="dev@rodolfodebonis.com.br",
    url="https://github.com/RodolfoBonis/microdetect",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "License :: OSI Approved :: MIT License",
        "Topic :: Scientific/Engineering :: Image Recognition",
    ],
    python_requires=">=3.9",
    install_requires=read_requirements(),
    entry_points={
        "console_scripts": [
            "microdetect=microdetect.cli:main",
        ],
    },
    include_package_data=True,
    package_data={
        'microdetect': ['default_config.yaml'],
    },
    data_files=doc_data_files,
    zip_safe=False,
)