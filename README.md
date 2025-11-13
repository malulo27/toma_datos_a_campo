# Toma de datos a campo

Aplicación web progresiva (PWA) pensada para registrar datos en campo sin conexión y sincronizarlos automáticamente cuando el dispositivo vuelva a tener internet. Incluye un backend mínimo en Node.js (sin dependencias externas) para recibir los registros y almacenarlos en un archivo JSON.

## Características

- **Modo offline**: guarda los registros en `localStorage` y mantiene la interfaz disponible gracias a un _service worker_.
- **Sincronización automática**: al recuperar la conexión, envía los registros pendientes al backend.
- **Backend liviano**: API REST para consultar y recibir registros, con persistencia en `data/records.json`.
- **Interfaz adaptable**: formulario simple de captura y listado de registros pendientes/sincronizados.

## Requisitos

- [Node.js](https://nodejs.org/) 18 o superior.

## Instalación y uso

```bash
npm start
```

- No es necesario ejecutar `npm install` porque el servidor solo usa dependencias nativas de Node.js.
- La aplicación quedará disponible en [http://localhost:3000](http://localhost:3000).
- Completa el formulario y guarda registros aun sin conexión. Cuando el navegador recupere internet se sincronizarán solos o puedes forzar la sincronización con el botón "Sincronizar".

## Estructura del proyecto

```
.
├── data
│   └── records.json          # Persistencia simple del backend
├── public                    # Frontend (PWA)
│   ├── index.html
│   ├── js
│   │   ├── app.js            # Lógica de UI y sincronización
│   │   └── storage.js        # Utilidades de almacenamiento local
│   ├── manifest.json         # Configuración PWA
│   ├── styles.css            # Estilos de la interfaz
│   └── sw.js                 # Service worker para funcionamiento offline
├── server.js                 # Servidor HTTP nativo + API REST
├── package.json
└── README.md
```

## Personalización

- **Estructura de datos**: ajusta los campos guardados en `public/js/app.js` según las necesidades del trabajo de campo.
- **Destino de sincronización**: modifica `SYNC_ENDPOINT` (en `public/js/app.js`) para apuntar a tu API o servicio real.
- **Persistencia**: reemplaza la persistencia basada en archivo (`data/records.json`) por una base de datos como PostgreSQL, MongoDB o un servicio en la nube.

## Próximos pasos sugeridos

1. Autenticación básica para identificar a cada operario.
2. Manejo de conflictos o duplicados cuando varios dispositivos reporten el mismo registro.
3. Encriptar la información sensible almacenada localmente.
4. Implementar sincronización incremental (p.ej. usando colas o _change feeds_).
5. Añadir pruebas automáticas (unitarias y de integración) para garantizar la calidad del código.

## Preguntas frecuentes

### ¿Qué significa el botón "Copy git apply" que aparece en GitHub?

Cuando revisas un _pull request_ en GitHub, cada bloque de cambios ("diff") suele incluir una opción llamada **"Copy git apply"**.
Al pulsarla, GitHub copia en tu portapapeles un parche en formato `git apply` que contiene exactamente las modificaciones de ese bloque.

Puedes pegar ese parche en tu terminal y ejecutarlo con `git apply` para replicar localmente esos cambios sin necesidad de descargarlos manualmente.
Es útil para probar o revisar una propuesta específica antes de que se fusione.

## Licencia

MIT
