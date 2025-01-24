
# Modelos y Clases Genéricas para Mensajería

La siguiente librería está diseñada como base para la implementación de otras librerías de mensajería instantánea, permitiendo aplicar el principio de sustitución de Liskov en sistemas conversacionales o de mensajería instantánea.

## Request

Enfocada en la recepción de mensajes, esta librería ofrece una clase abstracta `RequestAbc` con la declaración de métodos para ser implementados. Su inicialización da como resultado clases representativas organizadas en tres niveles: página, usuario y mensajes.

    InputAccount:
        raw_data: dict
        pid: str
        members: List[InputSender]
            uid: str
            sender_data: dict
            messages: List[MessageBase]
                TextMessage | InteractiveMessage | EventMessage | MediaMessage

        statuses: List[]
            EventMessage

Normalmente, se espera que llegue una página con un usuario y un mensaje. Sin embargo, también es necesario contemplar escenarios en los que se reciban varias páginas, con múltiples usuarios, y cada usuario con varios mensajes.

Además, es posible recibir referencias a mensajes sin usuarios (comúnmente estados, como vistos o leídos).

## Response

Para la construcción de mensajes, se diseñaron modelos capaces de representar la mayoría de las opciones ofrecidas por distintos servicios de mensajería:

- **Message**: Para texto simple (`body`) o compuesto por `header`, `body` y `footer`.
- **ReplyMessage**: Mensaje base que incluye botones.
- **SectionsMessage**: Mensajes seccionados, útiles para opciones como carruseles.
- **MediaMessage**: Para imágenes o archivos.

Además, se ofrece la clase `ResponseAbc`, que declara métodos que simplifican el envío de mensajes. Aunque los límites son sugerencias para estandarizar, están atados a las capacidades y restricciones de cada servicio de mensajería.

- `message_text(str)`: Envío de texto simple.
- `message_multimedia(url)`: Envío de contenido multimedia.
- `message_few_buttons(ReplyMessage)`: Envío con un máximo de 3 botones.
- `message_many_buttons(ReplyMessage)`: Envío con un máximo de 10 botones.
- `message_sections(SectionsMessage)`: Envío con un máximo de 10 secciones, con un total de hasta 10 botones.

La política de envío sugerida consiste en declarar cada clase por sesión de usuario, acumulando los mensajes esperados para enviarlos en un solo paso. Esto permite calcular errores de redundancia o retrasos en el envío de mensajes.

## Utils

`replace_parameter` es un método que reemplaza variables en textos con el formato `{variable}`. Este método se apoya en `ResponseAbc._get_parameters()`, que permite declarar una forma de obtener las variables de cada usuario. Así, es posible enviar mensajes más personalizados utilizando textos genéricos.

## WhatsApp

Se incluye un ejemplo de implementación de las clases `request.py` y `response.py`, con envío de mensajes reales si se tienen las configuraciones correctas y un token con permisos autorizados.

Puedes encontrar ejemplos de su uso en la [wiki correspondiente](https://github.com/yeeko-org/abc_message_models/wiki/WhatsApp-Message-Response).

## Instalación

Para instalar la librería, se recomienda utilizar la herramienta `pip` para agregarla a los recursos de Python o a un entorno virtual:

    pip install git+https://github.com/yeeko-org/abc_message_models

Recuerda que, si utilizas `pip freeze`, el paquete se establecerá en un hash específico del repositorio. Si no necesitas una versión exacta, basta con eliminar el hash y guardar el requerimiento.

Para actualizar la librería, puedes usar el parámetro `--upgrade`:

    pip install --upgrade git+https://github.com/yeeko-org/abc_message_models

También puedes descargar el repositorio y utilizar las aplicaciones que necesites. Ten en cuenta que `whatsapp_message` es una implementación que requiere las dependencias `request`, `response` y `utils`.
