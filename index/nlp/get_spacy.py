import subprocess
import sys
import spacy


def download_model(name: str) -> None:
    """
    Automates the spaCy model download.
    """
    try:
        subprocess.run(
            [sys.executable, "-m", "spacy", "download", name],
            check=True
        )
        print(f"spaCy model '{name}' downloaded successfully.")
    except subprocess.CalledProcessError as error:
        print(f"Error downloading spaCy model {name}:", error)
        

def get_spacy(model_name: str) -> spacy.Language:
    """
    A special class for managing the spaCy model download.
    """
    try:
        return spacy.load(model_name)
    except OSError:
        download_model(model_name)
        return spacy.load(model_name)
    