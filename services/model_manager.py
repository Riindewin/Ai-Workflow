import os


class ModelManager:

    def __init__(self, root="models"):
        self.root = root
        os.makedirs(root, exist_ok=True)

    def list_models(self):
        return [f for f in os.listdir(self.root) if os.path.isfile(os.path.join(self.root, f))]

    def get_model_path(self, name):
        candidate = os.path.join(self.root, name)
        return candidate if os.path.exists(candidate) else None

    def register_model(self, name, source_path):
        destination = os.path.join(self.root, name)
        if os.path.exists(source_path):
            with open(source_path, "rb") as src, open(destination, "wb") as dst:
                dst.write(src.read())
            return destination
        return None

    def download_model(self, name, url):
        raise NotImplementedError("Model download is not implemented yet.")
