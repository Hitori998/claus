<div align="center">
  <img src="assets/brand/claus.png" alt="Personagem e logo do Claus" width="112">
  <h1>Claus</h1>
  <p><strong>Sua voz vira texto. O Claus faz companhia.</strong></p>
  <p>Ditado local para Windows, com chamada por voz e um personagem animado.</p>
  <p><a href="https://github.com/Hitori998/claus/releases/latest"><strong>BAIXAR PARA WINDOWS</strong></a> · <a href="#como-usar">Como usar</a> · <a href="#requisitos">Requisitos</a> · <a href="https://github.com/Hitori998/claus/issues">Relatar problema</a></p>
</div>

---

## Instalar

1. **BAIXAR:** abra [a versão mais recente](https://github.com/Hitori998/claus/releases/latest) e, em **Assets**, selecione `Claus-Setup-0.2.0-win-x64.exe`.
2. **EXECUTAR:** abra o instalador e siga as instruções. Não é necessário instalar Python nem baixar modelos separadamente.
3. **INICIAR:** abra **Claus** pelo menu Iniciar ou pelo atalho na área de trabalho.

[**Download direto do instalador 0.2.0**](https://github.com/Hitori998/claus/releases/download/v0.2.0/Claus-Setup-0.2.0-win-x64.exe)

O pacote tem aproximadamente **1,2 GB**, pois inclui Python, bibliotecas e os modelos de reconhecimento para uso offline. O instalador ainda **não possui assinatura digital de editor**. O botão **Code → Download ZIP** baixa o código-fonte; para instalar o aplicativo pronto, use **Releases**.

## Como usar

1. **PREPARAR:** selecione a entrada do microfone nas configurações e mantenha a ativação por voz ligada.
2. **CONFIGURAR:** escolha a palavra ou frase de chamada em português e salve. O padrão de novas instalações é **computador**.
3. **POSICIONAR:** clique no campo de texto em que deseja escrever.
4. **DITAR:** diga a chamada, aguarde a animação de escuta e fale.
5. **CONCLUIR:** faça uma pausa. O Claus reconhece a gravação e insere o texto no campo original.
6. **CONFERIR:** revise o resultado antes de enviar ou salvar.

O atalho **Ctrl + Alt + Espaço** também inicia o ditado. Se o foco mudar, o resultado fica na área de transferência para colagem manual. O Claus não pressiona Enter nem envia mensagens automaticamente.

> A transcrição é concluída após cada pausa; o texto não é inserido palavra por palavra enquanto você fala.

## O que o Claus faz

| Recurso | Como funciona |
| --- | --- |
| **Ditado em outros aplicativos** | Insere o texto no campo que estava selecionado ao iniciar. |
| **Chamada por voz** | Permite configurar a frase de ativação e o microfone. |
| **Reconhecimento local** | Usa Whisper Small na CPU ou Whisper Turbo em GPU com Vulkan compatível. |
| **Sem API de transcrição** | Não exige assinatura, chave de API ou tokens faturados para reconhecer o áudio. |
| **Personagem na tela** | Pode ser arrastado, acompanha o cursor com os olhos e permanece visível durante o ditado. |
| **Expressões animadas** | Piscadas, carinho, sorriso, dúvida, tontura, sono, despertar e curiosidade. |
| **Dança com música** | Reage ao estado de reprodução informado por players compatíveis com os controles de mídia do Windows. |
| **Aparência configurável** | Ajusta tamanho do personagem, tamanho e altura da animação de escuta e fundo transparente. |
| **Execução em segundo plano** | Fechar a janela mantém o aplicativo na bandeja. Use **Sair** para encerrar. |

<p align="center"><img src="docs/personagem.png" alt="Expressões e interface do personagem Claus" width="720"></p>

## Requisitos

- **Sistema:** Windows 10 versão 1809 ou posterior / Windows 11, de 64 bits.
- **Entrada:** um microfone disponível no Windows.
- **CPU:** funcionamento incluído no instalador, sem necessidade de GPU dedicada.
- **GPU opcional:** placa e driver compatíveis com Vulkan; selecione o motor GPU no aplicativo. A compatibilidade e a velocidade dependem do hardware e do driver.
- **Internet:** necessária para baixar o instalador. Os modelos incluídos funcionam offline após a instalação.

O pacote inclui **Whisper Small**, **Whisper Turbo q5_0** e o modelo de chamada **Vosk em português**. Novas instalações começam em CPU. O tamanho do download não corresponde ao consumo de memória durante o uso.

## Privacidade e limites

A detecção da chamada e o reconhecimento acontecem no computador. **Nenhum áudio é enviado a uma API de transcrição.** Com a ativação por voz ligada, o microfone permanece aberto para detectar a chamada. O áudio de espera não é salvo; o áudio de ditado é temporário.

Ruído e conversas próximas podem causar erros ou ativações indevidas. A chamada não identifica quem está falando. Campos protegidos e aplicativos executados como administrador podem bloquear a inserção de texto. Revise transcrições que exijam precisão.

## Atualizar, verificar ou remover

- **Atualizar:** baixe o instalador de uma versão nova e execute. Preferências existentes são preservadas.
- **Verificar o download:** compare o SHA-256 do instalador com o arquivo `.sha256` publicado na mesma versão.
- **Desinstalar:** abra **Configurações do Windows → Aplicativos → Aplicativos instalados → Claus → Desinstalar**.

```powershell
Get-FileHash .\Claus-Setup-0.2.0-win-x64.exe -Algorithm SHA256
```

## Código e suporte

Para desenvolver ou instalar a partir do código, consulte [o guia de desenvolvimento](docs/DESENVOLVIMENTO.md). Essa alternativa exige Python 3.12 e downloads iniciais dos modelos; o procedimento ainda não foi validado em um Windows limpo.

Encontrou um problema? [Abra uma issue](https://github.com/Hitori998/claus/issues) com sua versão do Windows, versão do Claus, motor selecionado e uma descrição dos passos para reproduzir. Não publique gravações pessoais, senhas ou dados sensíveis.

[Notas das versões](https://github.com/Hitori998/claus/releases) · [Dependências e recursos de terceiros](THIRD_PARTY.md) · [Referências técnicas](PESQUISA-TRANSCRITORES.md)
