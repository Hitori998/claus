# Referências de código aberto e decisão técnica

Consulta em 5 de novembro de 2026. Não há um “melhor” universal: precisão em português brasileiro, latência e compatibilidade precisam ser medidos no equipamento e áudio reais.

| Projeto | O que oferece | Aplicação neste computador |
| --- | --- | --- |
| [WhisperLiveKit](https://github.com/QuentinFuxa/WhisperLiveKit) | Streaming local, estratégias SimulStreaming/LocalAgreement, VAD, vários motores | Referência para separar prévia de texto estável e preservar contexto; não foi instalado inteiro |
| [Whisper-Streaming](https://github.com/ufal/whisper_streaming) | Código e artigo da política LocalAgreement; o próprio projeto aponta SimulStreaming como sucessor | Referência conceitual. Nossa implementação usa sobreposição e revisão final; não afirma implementar LocalAgreement |
| [Buzz](https://github.com/chidiwilliams/buzz) | Aplicativo desktop offline, microfone ao vivo, exportação, vários motores e Vulkan | Alternativa pronta ao aplicativo próprio; não instalado |
| [whisper.cpp](https://github.com/ggml-org/whisper.cpp) | Runtime C/C++, quantização, CPU e Vulkan | Candidato a aproveitar a RX 580; requer confirmar driver e desempenho. Não foi ativada aceleração Vulkan nesta versão |
| [Qwen3-ASR](https://github.com/QwenLM/Qwen3-ASR) | Modelos abertos 0.6B/1.7B de reconhecimento de fala, multilíngue, demonstração de streaming | Candidato baseado em modelo de linguagem com áudio. Stack nova e desempenho no Windows/CPU ainda não medido; não instalado |
| [Parakeet TDT v3](https://huggingface.co/nvidia/parakeet-tdt-0.6b-v3) | Reconhecimento em 25 idiomas, incluindo português | A ficha informa dados de português europeu e ressalva diferenças com avaliações brasileiras. Não instalado nem declarado superior para esta voz |

## Alteração aplicada

- Small e Large v3 Turbo em [faster-whisper](https://github.com/SYSTRAN/faster-whisper), com CPU int8 e arquivos locais.
- Prévia Small com tempos por palavra; janela crescente de até 18 segundos, mantendo até 12 segundos de contexto anterior a cada atualização. A hipótese na região sobreposta é substituída. Um teste de janela curta de 1,5 segundo ainda cortava palavras no início da janela e foi descartado.
- Revisão final opcional, ativada por padrão: reconstruir o áudio completo em memória e reconhecê-lo com Turbo. Isso permite reavaliar palavras cortadas usando o áudio original, em vez de tentar adivinhá-las a partir de texto.
- Campo de nomes/termos esperados enviado como hotwords, sem mandar o áudio a um serviço remoto.
- Modelo ao vivo selecionável; a revisão final e arquivos usam Turbo. O Base permanece disponível como opção leve, sem fallback oculto.
- Sem LLM genérica de reescrita nesta versão: ela não recupera informação acústica ausente e pode mudar o sentido. Qwen3-ASR é uma alternativa de ASR, diferente de revisar o texto com um chatbot.

## Hardware verificado

Intel Xeon E5-2630 v4, dez núcleos, 15,9 GB de RAM, AMD Radeon RX 580 2048SP. Cerca de 19 GB livres antes dos novos downloads. Este runtime usa CPU; não presumimos suporte CUDA em placa AMD.

## Validação

`quality-benchmark.json` registra uma comparação reproduzível de Base, Small e Turbo sobre a mesma voz sintética em português, limpa e com ruído determinístico de 12 dB. WER normaliza pontuação, caixa e acentos. Um único áudio sintético não prova melhoria para o microfone real do usuário. Não usamos rankings entre bases ou equipamentos diferentes como garantia de precisão.
