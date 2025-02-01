# WhatsApp Message Implementation

La librería adjunta **`whatsapp_message`** implementa los métodos esperados para `request` y `response`, utilizando modelos para construir sus respuestas y mensajes, permitiendo así su uso bajo el principio de sustitución de Liskov.

Es compatible, a la fecha de enero de 2025, con la documentación oficial: [reference/messages](https://developers.facebook.com/docs/whatsapp/cloud-api/reference/messages).

El siguiente artículo explica cómo generar y obtener el identificador de número de teléfono, el `access_token`, y agregar los números para los casos de prueba. **Articulo no definido**

## Ejemplos de construcción y envío de mensajes

Explicaremos las propiedades para la construcción de `WhatsAppResponse`, siendo las básicas los datos proporcionados por `meta`.

    from yeeko_abc_message_models.whatsapp_message.response import WhatsAppResponse

    whatsapp_response = WhatsAppResponse(
        sender_uid="525512345678",
        account_pid="102141987654321",
        account_token="EAAS...."
    )

- **sender_uid**: Número telefónico destino.
- **account_pid**: Identificador del número de teléfono de la cuenta de negocio.
- **account_token**: Token de acceso con permisos autorizados o de prueba para el envío de mensajes por WhatsApp Business.

### Otras propiedades ajustables o consultables

- **message_list**: Lista de mensajes en orden de entrada, en formato de diccionario con la estructura esperada por `meta`. Puede contener datos de seguimiento adicionales.
- **errors**: Lista de errores ocurridos durante la ejecución.
- **debug**: Si se establece en `True`, en lugar de enviar los errores a la lista, se generará una excepción. Los servicios basados en webhook esperan una respuesta `200 OK`, por lo que debe considerarse una gestión adecuada de errores. Valor por defecto: `False`.
- **clean_list_after_send**: La política de la librería es almacenar todos los mensajes calculados y enviarlos al final con `send_messages()`. Esta propiedad limpia las listas después de ser enviadas. Valor por defecto: `True`.
- **response_send_messages**: Lista de seguimiento compuesta por el diccionario de respuesta y el diccionario del mensaje procesado por `_send_message()`. Se reinicia con `clean_list_after_send` al usar `send_messages()`.
- **base_url**: URL del endpoint de `meta` para el envío de mensajes.

### Envío de texto simple y multimedia

Para el envío de texto simple y multimedia se han simplificado los accesos. Para texto simple, se utiliza:

    whatsapp_response.message_text("Hello, world!")

Para multimedia, debes conocer los [tipos soportados por `meta`](https://developers.facebook.com/docs/whatsapp/cloud-api/reference/messages#media-object) y contar con una URL pública del contenido:

    whatsapp_response.message_multimedia(
        media_type="image",
        url_media="<https://server/public.jpg>"
    )

También es posible enviar un `media_id`, pero deberás gestionarlo y obtenerlo a través del [endpoint media de `meta`](https://developers.facebook.com/docs/whatsapp/cloud-api/reference/media):

    whatsapp_response.message_multimedia(
        media_type="image",
        media_id="KHHoa78"
    )

No olvides ejecutar:

    whatsapp_response.send_messages()
    whatsapp_response.response_send_messages  # Ver resultados

### Mensajes con botones

Se contemplan 2 opciones para el envio de mensajes con botones, pocos botones y muchos botones, la mayoría de los sistemas contemplan un layer de 3 botones o mas y algún otro método para muchos botones

WhatsApp ofrece dos opciones principales para este propósito: botones y secciones.

- **Botones:** Máximo de 3 botones siempre visibles.
- **Secciones:** Formato desplegable con un máximo de 10 secciones y 10 botones.

Ambas opciones se construyen de forma similar pero tienen resultados diferentes.

#### Construcción de botones

    from yeeko_abc_message_models.response.models import ReplyMessage, Button

    list_buttons = [
        Button(title="Button 1", payload="button_1"),
        Button(title="Button 2", payload="button_2"),
        Button(title="Button 3", payload="button_3"),
        Button(title="Button 4", payload="button_4"),
        Button(title="Button 5", payload="button_5")
    ]

    reply_test = ReplyMessage(
        body="Hello, buttons!",
        buttons=list_buttons  # type: ignore
    )

#### `message_few_buttons`

Pensado para construir mensajes con un máximo de 3 botones. En este ejemplo, se descartan los botones 4 y 5.

    whatsapp_response.message_few_buttons(reply_test)

#### `message_many_buttons`

Amplía el número de botones pero cambia el formato de presentación. WhatsApp no tiene soporte directo para esto, por lo que se representa mediante secciones con un máximo de 10 botones, descartando los excedentes.

    whatsapp_response.message_many_buttons(reply_test)

### Mensajes con secciones

Los servicios de mensajería suelen ofrecer opciones para enviar interacciones divididas o seccionadas. WhatsApp proporciona mensajes seccionados con la siguiente estructura:

    SectionsMessage
        Sections
            Buttons

La construcción de mensajes con secciones también utiliza una lista de botones. En los ejemplos, usaremos `list_buttons` del ejemplo anterior:

    from yeeko_abc_message_models.response.models import Section, SectionsMessage

    section_test = Section(
        title="Hello, section 2!",
        buttons=list_buttons[:3]
    )

    whatsapp_response.message_sections(
        SectionsMessage(
            body="Hello, sections!",
            sections=[section_test] * 6,  # Máximo de 6 secciones en este ejemplo
            button_text="Select"
        )
    )

Similar a `message_many_buttons`, el total de botones se limita a 10 entre todas las secciones, con un máximo de 10 secciones.
