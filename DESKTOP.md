# Claus para Windows

Abra **Claus.exe**, na pasta superior. A janela é nativa; não precisa do navegador. O executável inicia o Python portátil instalado em `transcritor-local`, portanto mantenha ambos juntos.

## Procedimento de ditado

1. **Preparar:** escolher o microfone, idioma e motor. Manter **Ativação por voz** ligada.
2. **Posicionar:** clicar no campo de texto do aplicativo de destino, deixando o cursor de escrita ativo.
3. **Chamar:** dizer a chamada salva (por padrão **“computador”**) e aguardar o indicador mudar para **Estou ouvindo**. Fazer a chamada separada do conteúdo evita incluir ou perder palavras na abertura do microfone.
4. **Ditar:** falar normalmente e fazer uma pausa. O aplicativo conclui automaticamente após a pausa configurada (1,8 segundo por padrão), reconhece com a GPU e insere o texto. Não é preciso apertar uma tecla para parar.
5. **Conferir:** o texto é colado no destino se a janela original continuar ativa. Se você mudar de janela, ele é copiado para colagem manual. O Claus nunca pressiona Enter nem envia mensagens.

O atalho funciona com a janela do Claus oculta. Fechar a janela mantém o ícone na bandeja. Use **Sair** no menu do ícone para encerrar. **Testar ditado aqui** mostra o resultado na janela, sem inserção externa.

**Ctrl + Alt + Espaço** continua funcionando como alternativa manual. Em **Concluir após**, escolha uma pausa maior se o aplicativo terminar antes de você concluir a frase. Ao terminar um ditado, ele volta a aguardar outra chamada. Sem fala após uma chamada, a sessão encerra em dez segundos.

## Ativação e indicador animado

### Escolher a chamada

Em **Chamada por voz**, escreva uma palavra ou uma frase de até quatro palavras e acione **Salvar chamada**. O aplicativo valida se as palavras existem no modelo de português e salva a escolha para as próximas aberturas. Exemplos de vocabulário disponível incluem “computador” e “ok escuta”. Somente a chamada escolhida fica ativa; não há aliases ocultos. Uma chamada de uma palavra exige confiança maior. Prefira palavras incomuns no seu ambiente para reduzir acionamentos involuntários.

Palavras inexistentes no vocabulário deste modelo não são treinadas automaticamente: o app apresenta uma mensagem e mantém a chamada anterior. Para nomes inventados ou em outros idiomas seria necessário outro detector/modelo.

A chamada usa Vosk Small PT, offline. Enquanto **Ativação por voz** estiver ligada, o microfone permanece aberto para reconhecer a chamada. O áudio de espera não é escrito em disco nem enviado à rede; a fila em memória é curta e descartável. Desative a opção na janela ou no menu da bandeja para pausar essa escuta.

Durante o ditado e o processamento, o indicador mostra somente a animação fornecida na pasta `wave`, sem títulos, mensagens nem contador: 23 cruzes, geometria original e 98 quadros de movimento, junto com o fundo GIF. A onda clara sobre preto reage à voz.

Na espera, aparece somente um personagem vetorial baseado na imagem fornecida: corpo preto com seis lóbulos e olhos brancos, sem faixa ou texto. Somente os olhos acompanham o cursor. Eles piscam em intervalos variados, com algumas piscadas duplas e expressões semicerradas ocasionais. O corpo permanece na posição escolhida.

Para mover: mantenha o botão esquerdo pressionado sobre o personagem e arraste. Os olhos ficam semicerrados, com a borda superior reta, e reabrem suavemente após soltar. A posição é salva entre aberturas e limitada à área disponível do monitor.

Para abrir o menu: clique no personagem. Escolha **Iniciar ditado**, **Abrir Claus** ou **Ocultar na bandeja**. Para restaurar: clique no ícone da bandeja ou marque **Mostrar personagem** no menu desse ícone. Ocultar o personagem mantém o aplicativo em segundo plano e preserva a ativação por voz. A animação Wave continua aparecendo durante o ditado.

Para ajustar o visual: abra **Aparência** no canto superior da janela. O tamanho do personagem varia de 50% a 250%; o tamanho da transcrição, de 50% a 200%, limitado à área disponível do monitor. Em **Altura na tela**, 0% posiciona a animação no topo e 100% na base. A animação permanece centralizada horizontalmente e mantém o monitor escolhido ao iniciar o ditado.

Marque **Fundo transparente** para remover o painel preto e sua borda, mantendo a onda e a geometria animada. Os pixels pretos do GIF ficam transparentes; os traços geométricos continuam visíveis. **Visualizar na tela** mostra uma prévia sem usar o microfone. Os controles aplicam as mudanças imediatamente e salvam as preferências automaticamente; **Concluir** fecha a prévia.

Ao arrastar bastante o personagem em pouco tempo, sobretudo de um lado para outro, ele fica zonzo: os olhos se transformam em espirais que giram em sentidos opostos. Após parar de movimentá-lo, a expressão permanece por alguns segundos e volta gradualmente aos olhos normais. Arrastes curtos mantêm a expressão semicerrada.

Passe o mouse várias vezes sobre o personagem, sem pressionar o botão, para fazer carinho. Ele fica com olhos felizes e bochechas rosas. Ao terminar o gesto, mostra um sorriso por oito segundos. Se uma chamada ficar dez segundos sem fala detectada, a onda encerra e ele mostra olhos assimétricos e uma interrogação por cinco segundos. O áudio sem fala é descartado.

O personagem permanece na posição escolhida durante a gravação e o reconhecimento. A onda aparece em uma janela separada, com os tamanhos, altura e transparência definidos em **Aparência**. A opção **Ocultar na bandeja** continua escondendo o personagem quando solicitada.

### Sono, curiosidade e música

Em repouso, ele pode dormir depois de 60–90 segundos, por 12–22 segundos. Fecha os olhos e respira lentamente. Ao acordar, passa quatro segundos com olhos sonolentos e um pequeno bocejo; depois espera pelo menos um minuto antes de poder dormir de novo. Cliques, carinho, arraste, ditado e música acordam o personagem. Ele não dorme durante gravação, processamento ou reprodução musical.

Entre períodos de repouso, olha para os dois lados com curiosidade por cerca de quatro segundos. Apenas os olhos se deslocam nessa variação.

Quando um player informa música em reprodução aos controles de mídia do Windows, o personagem dança, com balanço, pequenos pulos e sorriso. Ao pausar, a dança termina suavemente. A coreografia tem cadência própria; não mede o ritmo do áudio. Ditado e interações têm prioridade sobre a dança.

A detecção consulta somente o estado e o tipo da sessão de mídia, sem capturar som nem ler os nomes das faixas. Players que não publicam uma sessão de mídia compatível podem não acionar a dança. Integração: [API de sessões de mídia do Windows](https://learn.microsoft.com/en-us/uwp/api/windows.media.control.globalsystemmediatransportcontrolssessionplaybackinfo), via [PyWinRT](https://pywinrt.readthedocs.io/en/latest/).

O personagem recebe cliques somente em sua silhueta, sem tomar o foco ao arrastar. A animação de ditado permite que os cliques atravessem a janela. Os recursos Wave ficam em `assets/wave`, preservando a pasta original; o personagem é desenhado em Qt para animar os olhos sem imagens rasterizadas. A interface desktop e seus menus usam preto e tons de cinza.

A conclusão automática usa Silero VAD, não apenas volume. Ruído, áudio de outras pessoas ou uma pausa longa podem afetar a chamada e a segmentação. O detector não reconhece a identidade do locutor. A janela original precisa continuar ativa; se o foco mudar, o texto é copiado para colagem manual, evitando inserir em outro aplicativo inadvertidamente.

Para esta versão desktop, a inserção acontece ao concluir cada gravação, com limite de cinco minutos por ditado. A interface web continua disponível separadamente para transcrição ao vivo por trechos e arquivos longos.

## Motores locais

- **GPU AMD:** whisper.cpp com Vulkan, modelo Large v3 Turbo q5_0. Driver e runtime detectaram a RX 580 2048SP. Não usa CUDA nem exige GPU NVIDIA.
- **CPU Small:** menor consumo e conclusão mais rápida, com menor capacidade do modelo.
- **CPU Turbo:** motor faster-whisper já instalado.

Falhas da GPU são mostradas; não há troca silenciosa de motor. Aplicativos elevados como administrador e alguns campos protegidos podem bloquear a colagem. Nesse caso, use o texto copiado manualmente.

O resultado também fica em **Último ditado**, sem histórico persistente. O áudio é temporário e excluído ao terminar. Preferências de microfone, motor e vocabulário ficam em `desktop-settings.ini`. A área de transferência recebe o texto quando a inserção é usada.

## Origem e verificação da GPU

Runtime: [Lemonade whisper.cpp-rocm v1.8.4](https://github.com/lemonade-sdk/whisper.cpp-rocm/releases/tag/v1.8.4), pacote `whisper-v1.8.4-windows-vulkan-x64.zip`, SHA256 `e0d20a0f92e31b98adc0faf71172efc810b701e6391a9d858ca045bff26f77cd`, validado antes de extrair.

Modelo: [ggerganov/whisper.cpp](https://huggingface.co/ggerganov/whisper.cpp), `ggml-large-v3-turbo-q5_0.bin`.

O teste do mesmo modelo q5_0 com whisper.cpp levou 11,84 s na GPU no primeiro teste e 27,07 s com GPU desativada, para 10,13 s de voz sintética. Kernels/cache quentes reduziram o tempo na execução do motor desktop. `desktop-benchmark.json` mede os motores efetivamente disponíveis no aplicativo; formatos de modelo e implementações diferem, portanto não é uma comparação isolada apenas de hardware. O ganho depende do áudio, modelo e cache.

No teste do motor desktop com o cache Vulkan aquecido, os tempos foram **5,16 s na RX 580/Vulkan q5_0** e **20,89 s no faster-whisper/CPU Turbo int8**, com a mesma frase reconhecida corretamente por ambos. A primeira execução pode demorar mais para preparar shaders.

## Manutenção

Dependências adicionais: `desktop-requirements.txt`. O executável é um iniciador da instalação portátil; não distribua apenas ele sem a pasta `transcritor-local`. Não há inicialização automática com o Windows nem serviço externo.

Teste: `.venv\Scripts\python.exe -m unittest -v`.
