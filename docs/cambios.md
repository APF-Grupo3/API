Cambios:

icono de persona con capacidad para cerrar sesión
si la persona no ha vinculado su movil aparece icono vincular telegram
si ha vinculado telegram aparece icono enviar resumen por telegram
botón favoritos para incluir en la base de datos
que se puedan seleccionar más de 3 activos
corrección para que las alertas se guarden en la base de datos y no se pierdan al reiniciar el servidor 

- cambios pendientes que  me gustaría implementar:

creo que podríamos hacer otras tabs (ventanas como en el html del profesor)
por ejemplo una de gráficas o algo para que no aparezca únicmante una página

me falta crear el flujo de las alertas:
- primero revisar que la alerta se guarda por usuario
- que alertas se puede crear más de 1 (pasa lo mismo que con tickers, en cuanto añades otra alerta sobreescribe la anterior) Por lo menos dejar crear 5 alertas con diversos periodos..
- 1 cada cuanto tiempo vamos a calcular las métricas en el back para enviar las alertas. (para empezar 1 vez al día?)
- por qué medio se va a enviar la notificación: mail o telegram o las dos?
- se va a realizar por n8n? o mediante webhooks por código
- faltaria añadir a la alerta el periodo con el que se compara

