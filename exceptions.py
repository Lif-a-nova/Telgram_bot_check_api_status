class HTTPException(Exception):
    """Exception while getting HTTP response."""


#     if response.status_code != HTTPStatus.OK:
#         code = response.status_code
#         text =  response.text
#       details = f'Кода ответа: {code}, сообщение об ошибке: {text}'
#         
#         if code == HTTPStatus.BAD_REQUEST:
#             raise HTTPException(f'Ошибка запроса. {details}')
#         
#         if code == HTTPStatus.UNAUTHORIZED:
#             raise HTTPException(f'Ошибка аутентификации. {details}')
#         
#         if code == HTTPStatus.FORBIDDEN:
#             raise HTTPException(f'Доступ к API запрещен. {details}')
#         
#         if code == HTTPStatus.NOT_FOUND:
#             raise HTTPException(f'Ресурс не найден. {details}')
        
# pytest не пропускает
