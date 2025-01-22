# Modelos y clases Genéricos para mensajería

La siguiente librería esta pensada como base para la implementación otras librerías de mensajería instantánea y poder aplicar el principio de sustitución de liskov en sistemas de conversacionales o mensajería instantáneas

## Request

Centrado en la recepción de mensajes, ofrece una clase abstracta RequestAbc con la declaración de métodos para ser implementados, donde su inicialización de como resultado clases representativas organizadas a 3 niveles: pagina, usuario y mensajes

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

Lo normal será que llegue una pagina, con un usuario y un mensaje, pero se debe contemplar que de los datos pueden llegar varias paginas, con varios usuarios y cada usuario con varios mensajes

Además de que tambien pueden llegar referencias a mensajes sin usuarios, comúnmente estados, como vistos o leídos

## Response

Para la construcción de mensajes, se diseñaron modelos que puedan representar la mayoría de las opciones ofrecidas por los distintos servicios.

- Message: para texto simple(body) o compuesto por header, body y footer
- ReplyMessage: Message base que incluyen botones
- SectionsMessage: Mensajes seccionados para opciones como carruseles
- MediaMessage: imágenes o archivos

Tambien se ofrece una clase ResponseAbc, con la declaración de métodos que simplifiquen el envio de mensajes, aunque los limites son sugerencias para estandarizar, están atados a las capacidades y limitaciones de cada servicio de mensajería.

- message_text(str): envio de texto simple
- message_multimedia(url): envio de multimedia
- message_few_buttons(ReplyMessage): envio máximo de 3 botones
- message_many_buttons(ReplyMessage): envio máximo de 10 botones
- message_sections(SectionsMessage): envio máximo de 10 secciones con 10 botones máximo en total

La política de envio sugerida es declara cada clase por sesión de usuario y acumular los mensajes esperados para poder mandarlos en un solo paso, de esta forma se pueden calcular errores de redundancia o envio de mensajes con retrasos de tiempo

## Utils

replace_parameter es un método que remplaza variables en textos con el formato {variable}, apoyado de ResponseAbc._get_parameters() donde podremos declarar una forma de obtener las variables de cada usuario, y asi poder mandarle mensajes mas personalizados utilizando textos genéricos.

## Whastapp

Ejemplo de implementación de las clases request.py y response.py, con envio de mensajes reales si se tienen las configuraciones correctas y un token con permisos autorizados.

ejemplos de su utilización en la siguiente wiki.
