seguridad-chat-documentos
Disena, implementa, audita y asegura sistemas de chat con cifrado de extremo a extremo (E2EE) y flujos de encriptado de documentos. Usalo cuando el usuario pregunte sobre arquitectura de mensajeria segura, protocolo Signal, X3DH, Double Ratchet, MLS, cifrado de archivos o documentos del lado del cliente, envelope encryption, gestion de claves (KMS), seguridad en WebSockets o auditoria de codigo criptografico para aplicaciones de chat e intercambio de archivos.

Instructions
Seguridad de Chat y Documentos
Proporciona guia arquitectonica, implementaciones criptograficas y auditorias de seguridad para plataformas de chat en tiempo real y sistemas de encriptado de documentos utilizando primitivas criptograficas modernas y autenticadas.

Cuando Usar
Disenar o implementar mensajeria con cifrado de extremo a extremo (E2EE) para chats individuales (1-a-1) o grupales.
Cifrar documentos, archivos adjuntos o archivos pesados en reposo o en transito (cifrado del lado del cliente o cifrado por sobre en el servidor).
Implementar mecanismos de derivacion, intercambio, rotacion o almacenamiento seguro de claves.
Auditar codigo existente de chat o manejo de archivos en busca de vulnerabilidades criptograficas, fugas de metadatos o fallos de control de acceso.
Asegurar canales de transporte en tiempo real (WebSockets, gRPC, WebRTC) y flujos de autenticacion.
Pasos
1. Definir el Modelo de Amenazas y el Limite de Confianza
Determina donde comienza y termina la confianza antes de escribir codigo o elegir algoritmos:

Zero-Knowledge / E2EE (Servidor No Confiable): El servidor solo enruta texto cifrado y almacena blobs encriptados. Las claves se generan, intercambian y almacenan estrictamente en los dispositivos cliente.
Servidor Confiable (Cifrado en Servidor / KMS): El servidor gestiona el cifrado en reposo mediante un Servicio de Gestion de Claves (AWS KMS, HashiCorp Vault, Google Cloud KMS) y TLS 1.3 en transito. Usa este enfoque solo cuando sea estrictamente necesario realizar busquedas en el servidor, procesamiento con IA o indexacion por cumplimiento normativo.
2. Seleccionar Primitivas Criptograficas Modernas
Exige cifrado autenticado (AEAD) en todas las capas. Nunca utilices modos no autenticados (como CBC sin MAC o ECB) ni algoritmos obsoletos.

Cifrado Simetrico (Mensajes y Documentos): Usa AES-256-GCM (cuando exista aceleracion por hardware AES-NI) o XChaCha20-Poly1305 (preferido en entornos puramente de software y por usar nonces aleatorios de 192 bits que evitan colisiones).
Intercambio de Claves: Usa X25519 (ECDH sobre Curve25519).
Firmas Digitales: Usa Ed25519 para verificacion de identidad y pre-claves firmadas.
Derivacion de Claves (KDF):
Entradas de alta entropia (secretos compartidos): Usa HKDF-SHA256.
Entradas de baja entropia (contrasenas de usuario): Usa Argon2id (minimo 64 MB de memoria, 3 iteraciones, 4 hilos).
3. Arquitecturar la Seguridad del Chat
Para sistemas de chat E2EE, garantiza Secreto Hacia Adelante (Forward Secrecy - FS) y Seguridad Post-Compromiso (Post-Compromise Security - PCS):

Configuracion de Sesion Asincrona (X3DH):
Cada cliente publica en el servidor una Clave de Identidad (IK), una Pre-Clave Firmada (SPK) y un lote de Pre-Claves de Un Solo Uso (OPK).
Verifica siempre la firma de la SPK antes de calcular el secreto compartido mediante intercambios Diffie-Hellman X25519.
Rotacion por Mensaje (Double Ratchet / MLS):
Deriva una clave efimera unica para cada mensaje de chat utilizando una cadena KDF simetrica y un trinquete (ratchet) Diffie-Hellman.
Elimina de inmediato las claves de mensajes antiguos tras descifrarlos para garantizar el secreto hacia adelante.
Para chats grupales grandes, prefiere el estandar MLS (Messaging Layer Security - RFC 9420) en lugar de claves de remitente por pares para escalar las actualizaciones de claves de forma logaritmica.
Seguridad de Transporte y Sesion:
Exige TLS 1.3 y wss:// para todas las conexiones WebSocket.
Autentica el handshake del WebSocket mediante tokens de corta duracion (ej. JWT con expiracion de 5 a 15 minutos) y revalida periodicamente el estado de la sesion en los sockets activos.
Vincula el ID del remitente, el ID del destinatario y el numero de secuencia del mensaje dentro de los Datos Autenticados Adicionales (AAD) del esquema AEAD para prevenir ataques de repeticion (replay), reordenamiento y confusion de contexto.
4. Arquitecturar el Cifrado de Documentos y Archivos
Nunca cargues documentos completos en memoria de una sola vez, y nunca cifres archivos directamente con la contrasena de un usuario o una clave maestra estatica.

Patron de Cifrado por Sobre (Envelope Encryption):
Genera una Clave de Cifrado de Datos (DEK) unica y criptograficamente aleatoria de 256 bits para cada documento.
Cifra el documento utilizando la DEK.
Cifra (envuelve) la DEK utilizando una Clave de Cifrado de Claves (KEK) (derivada de la clave publica del destinatario en E2EE, o gestionada por un KMS).
Almacena la DEK envuelta junto con los metadatos del documento cifrado.
Cifrado AEAD por Flujo en Fragmentos (Chunked Streaming AEAD):
Divide los documentos en fragmentos de tamano fijo (ej. de 64 KB a 1 MB) y cifra cada fragmento de forma independiente como un flujo (usando age, libsodium crypto_secretstream o Google Tink Streaming AEAD).
Deriva el nonce de cada fragmento de forma determinista a partir de un nonce base mas el contador del fragmento (big-endian), e incluye un indicador de fragmento final en la etiqueta o AAD para evitar ataques de truncamiento o reordenamiento de bloques.
Proteccion de Metadatos y Subida de Archivos:
Cifra el nombre original del archivo, el tipo MIME y las etiquetas personalizadas dentro de un manifiesto cifrado en lugar de exponerlos en texto plano en la base de datos o en las rutas de almacenamiento.
Almacena los blobs cifrados bajo UUIDs aleatorios en el almacenamiento de objetos (ej. S3).
Elimina los metadatos EXIF y propiedades del documento en el cliente antes de cifrar cuando la privacidad sea critica.
Valida los limites de tamano de archivo antes de aceptar flujos para prevenir ataques de denegacion de servicio (DoS).
5. Verificar y Auditar la Implementacion
Revisa esta lista de verificacion siempre que generes o audites codigo de seguridad:

[ ] Uso exclusivo de CSPRNG: ¿Se generan todas las claves, nonces y sales mediante un Generador de Numeros Pseudoaleatorios Criptograficamente Seguro (crypto.getRandomValues, os.urandom, secrets, crypto/rand)?
[ ] Cero reutilizacion de Nonces: ¿Se garantiza que cada par clave/nonce sea unico? (Prefiere XChaCha20-Poly1305 o DEKs unicas por documento para eliminar el riesgo de colision).
[ ] Comparaciones en Tiempo Constante: ¿Se comparan los MAC, hashes y tokens utilizando funciones de tiempo constante (hmac.compare_digest, crypto.timingSafeEqual)?
[ ] Vinculacion en AAD: ¿Cada llamada de cifrado AEAD vincula los metadatos contextuales (ID del documento, ID del remitente, indice del fragmento) en el parametro AAD?
[ ] Limpieza de Claves en Memoria: ¿Se sobrescriben o limpian de la memoria las claves sensibles en texto plano despues de su uso cuando el entorno de ejecucion lo permite?
Errores Comunes (Gotchas)
Cifrar archivos grandes en un unico buffer AEAD: Llamar a AES-GCM estandar sobre un archivo de 500 MB de una sola vez obliga al cliente o al servidor a almacenar en memoria o disco texto plano no verificado antes de comprobar la etiqueta de autenticacion al final. Usa siempre AEAD por flujo en fragmentos (crypto_secretstream o Tink).
Compartir documentos directamente por el canal de chat: Nunca envies un documento de varios megabytes directamente dentro del payload del ratchet del chat. En su lugar, cifra el archivo localmente con una DEK efimera nueva, sube el blob cifrado al almacenamiento de objetos y envia unicamente la DEK + URL del texto cifrado + hash de integridad SHA-256 dentro del mensaje de chat E2EE.
Colisiones de Nonce de 96 bits en AES-GCM: Generar nonces aleatorios de 96 bits con la misma clave presenta riesgo de colision tras $2^{32}$ cifrados (limite del cumpleanos). Rota las claves frecuentemente (mediante ratcheting o DEKs por archivo) o utiliza XChaCha20-Poly1305 (nonce de 192 bits).
Desfase de Autorizacion en WebSockets: Autenticar solo durante la solicitud inicial HTTP Upgrade permite que usuarios revocados permanezcan conectados indefinidamente. Implementa verificaciones periodicas de permisos en los heartbeats y desconecta forzosamente los sockets al revocar tokens o rotar claves.
Trampas en la Busqueda sobre Texto Cifrado: No implementes cifrado determinista ingenuo (como AES-ECB) para habilitar busquedas en el servidor sobre el historial de chat o documentos, ya que filtra patrones de frecuencia. Utiliza indexacion local en el cliente (ej. SQLite cifrado con SQLCipher).