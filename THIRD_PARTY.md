# Dependências e recursos

O projeto usa bibliotecas e modelos externos, sujeitos às respectivas licenças:

- [faster-whisper](https://github.com/SYSTRAN/faster-whisper) e modelos Whisper distribuídos separadamente.
- [whisper.cpp](https://github.com/ggml-org/whisper.cpp) / [runtime Vulkan Lemonade](https://github.com/lemonade-sdk/whisper.cpp-rocm), opcionais e não incluídos.
- [Vosk](https://github.com/alphacep/vosk-api) e [modelo PT Small](https://alphacephei.com/vosk/models), baixado durante a instalação.
- [PySide6 / Qt for Python](https://doc.qt.io/qtforpython-6/), [sounddevice](https://python-sounddevice.readthedocs.io/), [PyWinRT](https://pywinrt.readthedocs.io/), FastAPI, Uvicorn, PyAV e demais dependências declaradas nos arquivos de requisitos.

Os recursos `assets/wave/background.gif` e `assets/wave/motion.json` vieram de uma referência fornecida para este projeto. Não foi confirmada uma licença pública de redistribuição desses recursos. As imagens de referência do personagem não são incluídas; o desenho é feito por código em Qt.

Este repositório não inclui uma licença geral de distribuição do código ou dos recursos gráficos. Antes de publicar ou redistribuir o projeto, defina a licença desejada e confirme os direitos dos recursos de referência.
