import bcrypt
from dataclasses import dataclass
from typing import Optional
from app.models.domain import Cliente
from app.repositories.cliente_repository import ClienteRepository


@dataclass
class AuthResult:
    exito: bool
    cliente: Optional[Cliente] = None
    mensaje: str = ""


class AuthService:
    def __init__(self):
        self.cliente_repo = ClienteRepository()

    def iniciar_sesion(self, email: str, contrasena: str):
        cliente = self.cliente_repo.get_by_email(email=email)

        if not cliente:
            return AuthResult(exito=False, mensaje="Correo o contraseña incorrectos.")

        contrasena_plana_bytes = contrasena.encode('utf-8')
        hash_guardado_bytes = cliente.password_hash.encode('utf-8')

        if bcrypt.checkpw(contrasena_plana_bytes, hash_guardado_bytes):
            return AuthResult(
                exito=True,
                cliente=cliente,
                mensaje="Inicio de sesion exitoso"
            )
        else:
            return AuthResult(exito=False, mensaje="Correo o contraseña incorrectos.")

    def registrar(self, nombre: str, apellido: str, email: str,
                   telefono: Optional[str], contrasena: str) -> AuthResult:

        if self.cliente_repo.get_by_email(email):
            return AuthResult(exito=False, mensaje="Ya existe una cuenta registrada con ese correo.")

        password_hash = bcrypt.hashpw(
            contrasena.encode("utf-8"), bcrypt.gensalt()
        ).decode("utf-8")

        nuevo_cliente = Cliente(
            nombre=nombre,
            apellido=apellido,
            email=email,
            password_hash=password_hash,
            telefono=telefono
        )

        try:
            id_cliente = self.cliente_repo.save(nuevo_cliente)
        except Exception as e:
            return AuthResult(exito=False, mensaje=f"No se pudo completar el registro: {e}")

        nuevo_cliente.id_cliente = id_cliente
        return AuthResult(exito=True, cliente=nuevo_cliente, mensaje="Registro exitoso.")