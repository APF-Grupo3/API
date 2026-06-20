// Lógica del formulario de login y registro.
// Habla con los endpoints /api/v1/login y /api/v1/registro definidos en auth.py

const loginTab = document.querySelector('[data-target="login-form"]');
const registroTab = document.querySelector('[data-target="registro-form"]');
const loginForm = document.getElementById("login-form");
const registroForm = document.getElementById("registro-form");
const mensajeBox = document.getElementById("auth-mensaje");

function mostrarMensaje(texto, tipo) {
  mensajeBox.textContent = texto;
  mensajeBox.className = `auth-mensaje ${tipo}`;
  mensajeBox.hidden = false;
}

function ocultarMensaje() {
  mensajeBox.hidden = true;
}

function activarPestana(tab, form, otroTab, otroForm) {
  tab.classList.add("active");
  otroTab.classList.remove("active");
  form.hidden = false;
  otroForm.hidden = true;
  ocultarMensaje();
}

loginTab.addEventListener("click", () => {
  activarPestana(loginTab, loginForm, registroTab, registroForm);
});

registroTab.addEventListener("click", () => {
  activarPestana(registroTab, registroForm, loginTab, loginForm);
});

async function enviarJSON(url, payload) {
  const respuesta = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "include", // necesario para que la cookie de sesión se guarde
    body: JSON.stringify(payload),
  });
  const datos = await respuesta.json().catch(() => ({}));
  return { ok: respuesta.ok, datos };
}

loginForm.addEventListener("submit", async (evento) => {
  evento.preventDefault();
  ocultarMensaje();

  const boton = loginForm.querySelector(".auth-submit");
  boton.disabled = true;

  const payload = {
    email: document.getElementById("login-email").value.trim(),
    password: document.getElementById("login-password").value,
  };

  try {
    const { ok, datos } = await enviarJSON("/api/v1/login", payload);
    if (!ok) {
      mostrarMensaje(datos.error || "No se pudo iniciar sesión", "error");
      return;
    }
    mostrarMensaje(`Bienvenido, ${datos.cliente.nombre}`, "success");
    // Sesión creada en el servidor: ya podemos pasar al dashboard.
    window.location.href = "/dashboard";
  } catch (error) {
    mostrarMensaje("Error de conexión con el servidor", "error");
  } finally {
    boton.disabled = false;
  }
});

registroForm.addEventListener("submit", async (evento) => {
  evento.preventDefault();
  ocultarMensaje();

  const boton = registroForm.querySelector(".auth-submit");
  boton.disabled = true;

  const payload = {
    nombre: document.getElementById("reg-nombre").value.trim(),
    apellido: document.getElementById("reg-apellido").value.trim(),
    email: document.getElementById("reg-email").value.trim(),
    pais: document.getElementById("reg-pais").value.trim(),
    telefono: document.getElementById("reg-telefono").value.trim(),
    password: document.getElementById("reg-password").value,
  };

  try {
    const { ok, datos } = await enviarJSON("/api/v1/registro", payload);
    if (!ok) {
      mostrarMensaje(datos.error || "No se pudo crear la cuenta", "error");
      return;
    }
    mostrarMensaje("Cuenta creada correctamente. Ya puedes iniciar sesión.", "success");
    registroForm.reset();
    activarPestana(loginTab, loginForm, registroTab, registroForm);
  } catch (error) {
    mostrarMensaje("Error de conexión con el servidor", "error");
  } finally {
    boton.disabled = false;
  }
});
