from src.infrastructure.trello.trello import TrelloOperaciones


class TrelloOperacion:
    def __init__(self):
        self.repository = TrelloOperaciones()

    def execute(
        self,
        data_frontend: dict,
        id_op: str,
        trello_archivos: list,
        url_drive: str,
        cavali_resultados: dict,
    ) -> dict | None:
        title = self.repository.trello_title(data_frontend, id_op)

        descripcion = self.repository.trello_descripcion(
            data_frontend=data_frontend,
            id_op=id_op,
            drive_folder_urlstr=url_drive,
            cavali_resultados=cavali_resultados,
        )

        card_id = self.repository.trello_card(title, descripcion)

        attachments_result = None
        if card_id and trello_archivos:
            attachments_result = self.repository.attach_files_to_card(
                card_id, trello_archivos
            )

        return {
            "success": True,
            "card_id": card_id,
            "title": title,
            "attachments": attachments_result,
        }
