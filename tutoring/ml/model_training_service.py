class ModelTrainingService:
    def __init__(self, dataset_builder, model_registry):
        self.dataset_builder = dataset_builder
        self.model_registry = model_registry

    def train(self):
        pass

    def evaluate(self, model, x_valid, y_valid):
        pass

    def save_model(self, model, metadata):
        pass