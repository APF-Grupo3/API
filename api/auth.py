"""Endpoints de registro y login.

Este módulo define un Blueprint de Flask con dos rutas:
  - POST /api/v1/registro  -> crea un cliente nuevo
  - POST /api/v1/login     -> comprueba email + contraseña y abre sesión

Se importa y registra desde app.py con:
    from auth import auth_bp
    app.register_blueprint(auth_bp)
"""

from __future__ import annotations

import re

from flask import Blueprint, jsonify, request, session

from models import Cliente, db

auth_bp = Blueprint("auth", __name__)

EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def validar_email(email: str) -> bool:
    return bool(EMAIL_REGEX.match(email or ""))


@auth_bp.route("/api/v1/registro", methods=["POST"])
def registro() -> object:
    payload = request.get_json(silent=True) or {}

    campos_obligatorios = ("email", "nombre", "apellido", "pais", "password")
    faltantes = [c for c in campos_obligatorios if not payload.get(c)]
    if faltantes:
        return (
            jsonify({"error": "Faltan campos obligatorios", "campos": faltantes}),
            400,
        )

    email = payload["email"].strip().lower()
    if not validar_email(email):
        return jsonify({"error": "El email no tiene un formato válido"}), 400

    if len(payload["password"]) < 6:
        return (
            jsonify({"error": "La contraseña debe tener al menos 6 caracteres"}),
            400,
        )

    if Cliente.query.filter_by(email=email).first() is not None:
        return jsonify({"error": "Ya existe un cliente registrado con ese email"}), 409

    cliente = Cliente(
        email=email,
        nombre=payload["nombre"].strip(),
        apellido=payload["apellido"].strip(),
        pais=payload["pais"].strip(),
        telefono=payload.get("telefono", "").strip() or None,
    )
    cliente.set_password(payload["password"])

    db.session.add(cliente)
    db.session.commit()

    return jsonify({"status": "created", "cliente": cliente.to_dict()}), 201


@auth_bp.route("/api/v1/login", methods=["POST"])
def login() -> object:
    payload = request.get_json(silent=True) or {}

    email = (payload.get("email") or "").strip().lower()
    password = payload.get("password") or ""

    if not email or not password:
        return jsonify({"error": "Debes indicar email y contraseña"}), 400

    cliente = Cliente.query.filter_by(email=email).first()

    # Mensaje genérico a propósito: no revelamos si el problema es el email
    # o la contraseña, para no dar pistas a quien intente adivinar cuentas.
    credenciales_invalidas = (
        cliente is None or not cliente.check_password(password)
    )
    if credenciales_invalidas:
        return jsonify({"error": "Email o contraseña incorrectos"}), 401

    if not cliente.activo:
        return jsonify({"error": "Esta cuenta está desactivada"}), 403

    # Guardamos el id del cliente en la sesión (cookie firmada por Flask).
    # Esto es lo que permite que /dashboard sepa que ya hay alguien logueado.
    session["cliente_id"] = cliente.id

    return jsonify({"status": "ok", "cliente": cliente.to_dict()}), 200


@auth_bp.route("/api/v1/logout", methods=["POST"])
def logout() -> object:
    session.pop("cliente_id", None)
    return jsonify({"status": "ok"}), 200


@auth_bp.route("/api/v1/sesion", methods=["GET"])
def sesion_actual() -> object:
    """Permite al frontend comprobar si hay alguien logueado."""
    cliente_id = session.get("cliente_id")
    if not cliente_id:
        return jsonify({"autenticado": False}), 200

    cliente = Cliente.query.get(cliente_id)
    if cliente is None:
        session.pop("cliente_id", None)
        return jsonify({"autenticado": False}), 200

    return jsonify({"autenticado": True, "cliente": cliente.to_dict()}), 200
