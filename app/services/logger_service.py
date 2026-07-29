class SesionActual:
    def __init__(self):
        self.usuario = None

    def iniciar(self, cliente):
        self.usuario = cliente

    def cerrar(self):
        self.usuario = None

    def esta_activo(self):
        return self.usuario is not None

sesion = SesionActual()