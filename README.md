# cadess (CAdES Service) 
Сервис предоставляет функционал подписывания документов электронной подписью и отправку документов в Diadoc

[Инструкция по сборке и установке](INSTALL.md)

Описание методов API можно посмотреть по ссылке: 
[https://cadess-host/docs](https://cadess-host/docs)

Логирование: 

При запуске создаётся файл `cades.log`. В директории с exe файлом в случае с win-service. 


В случае с docker вариантом логирование происходит в docker logs.
Логируются основные события сервиса: обнаружение ключа для подписи, попытки открыть ключ (если не удалось сделать это с первого раза)
, а также успех (или не успех) подписания и отправки документа.

