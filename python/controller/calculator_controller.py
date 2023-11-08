from service.calculator_service import CalculatorService


class CalculatorController:
    def __init__(self):
        self.service = CalculatorService()

    def add(self, a, b):
        return self.service.add(a, b)

    def multiply(self, a, b):
        return self.service.multiply(a, b)
