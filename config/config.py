import yaml

class Config:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
            cls._instance.load_config()
        return cls._instance

    def load_config(self):
        with open('config/config.yaml', 'r') as file:
            self.config = yaml.safe_load(file)
    
    def get(self, key, default=None):
        return self.config.get(key, default)