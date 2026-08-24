import asyncio
import edge_tts
from pathlib import Path

TEXT = """
Pessoal, vamos começar nosso projeto. Ok. E o ponto de partida a partir deste momento, depois de todo o trabalho de configuração, é um documento de requisitos do produto. O que é isso? Bem, isso basicamente vai delinear nosso pensamento de sistemas.

O que estamos construindo? Qual é nossa pilha de tecnologia? Qual é parte da funcionalidade? Que só precisa ser breve porque podemos construir iterativamente esse conjunto de funcionalidades como faríamos. Você sempre adiciona recursos mais tarde.

Você precisa lançar a primeira versão. Então o PRD é para a v1 do seu aplicativo. Quem são seus usuários, etc. Agora, eu me adiantei e preparei isso hoje de manhã. Eu não usei o ChatGPT, que eu costumava usar em 2024.

Eu acho que documentos PRD são melhores se forem breves. A pilha de tecnologia é provavelmente uma das coisas mais importantes, assim como o que o aplicativo faz. Agora, eu mantenho breve porque, do ponto de vista técnico, o Claude Code é melhor do que eu e é melhor do que você em alguns desses desafios que precisamos resolver. Ok. Então eu não quero alimentá-lo com muita informação porque eu acho que o Claude Code é um desenvolvedor muito mais técnico e proficiente do que eu.

Eu acredito que é o melhor do mundo. Por que eu o orquestraria demais e diria para fazer as coisas de uma certa maneira? Eu posso, em vez disso, dar uma ideia geral do que eu quero construir. Esta é uma pilha de tecnologia que eu gostaria de usar. Agora eu quero que você, Claude Code, eu quero que você descubra como construí-la.

Essa é a melhor, melhor abordagem. Então vamos abrir o Claude Code. Ok? Agora o que eu vou fazer, eu vou apenas dizer compactar muito rapidamente. Ok?

E compactar, o que ele faz é apenas pegar o chat, compactá-lo em um pequeno resumo em segundo plano. Nós não vamos vê-lo, só para manter esse contexto fluindo, mas libera o contexto porque você está começando com algo novo aqui. Então, após cada marco ou implementação de recurso, estaremos compactando, começando novamente do zero. Ok. Ótimo.

No lado esquerdo, eu quero que você clique com o botão direito na pasta Orbit e clique em novo arquivo. Eu então quero que você digite PRD ponto MD. MD é markdown. PRD é documento de requisitos do produto porque vamos colar o PRD que você pode encontrar abaixo deste vídeo. Ok.

Super, super curto. Se você está fazendo codificação AR há um tempo, pode pensar, Greg, isso é tão pequeno. E, novamente, eu acho que este é um ótimo lugar para começar. É contexto suficiente. Claro.

Podemos dizer ao Claude Code, preencha um pouco mais o PRD. Eu estou intencionalmente mantendo-o curto porque eu não sei como cada recurso neste aplicativo vai parecer. Vamos ver como nos saímos. Eu sei que quero construir uma versão do Linear para mim. Vamos ver como progredimos.

Eu vou ler para você, e nós vamos discutir. Estamos construindo um aplicativo de gerenciamento de projetos semelhante ao Linear. O aplicativo permite que equipes criem, colaborem em tarefas. Agora, se você não sabe o que é Linear, vá para linear.app. Dê uma olhada.

Eu o uso no meu trabalho diário. Eu trabalho em uma startup com a Radian, e é lá que lidamos com rastreamento de problemas e gerenciamento de projetos e direcionamento do tempo da equipe. Ok? Aplicativo fantástico. Mas no final das contas, é meio que um quadro Kanban glorificado ou Kanban dependendo de onde você está no mundo.

Eu chamo de Kanban. Então é só mover, criar tarefas que estão associadas a projetos e mover essas tarefas através de diferentes status. Não iniciado, iniciado, concluído, revisado, revisão, triagem, todos os status diferentes. Então funcionalidade, eu quero integração de usuário, criação de equipe. Então isso é importante de um ponto de vista hierárquico.

Temos uma equipe e então membros que pertencem a uma equipe. Esta é uma plataforma para as equipes se inscreverem, então elas precisam pertencer à sua própria equipe e ver apenas os dados de sua própria equipe. Temos espaços de trabalho e quadros. Então espaços de trabalho são um espaço de trabalho e quadros são apenas uma maneira de adicionar uma estrutura de pastas às suas tarefas para sua equipe. Layout Kanban com arrastar e soltar, gerenciamento de equipe e usuário.

Eu vou adicionar tudo aqui. Claude Code provavelmente vai praticamente saber toda a funcionalidade que eu preciso. Provavelmente vai me pedir para preencher isso. Então a pilha de tecnologia, eu preciso adicionar. Ele só precisa saber o que nós escolhemos.

E nós escolhemos Next. 16. Agora eu coloquei use proxy dot t s aqui só porque na lição anterior, eu falei sobre versionamento. Com Next. Js 15, houve uma grande mudança de quebra para chegar ao Next.

Js 16, e alguns desses modelos ainda voltam para a versão 15 para este conceito chamado middleware, que agora foi atualizado para proxy.ts. Deixei lá apenas como um lembrete, e Claude Code pode buscar os documentos através de uma chamada de ferramenta de pesquisa na web para entender proxy dot t s. Nós estamos usando superbase. Agora eu disse local primeiro. Ok?

Eu não quero usar superbase cloud porque eu tenho que pagar por ele imediatamente. Então eu quero usar local primeiro, e esta é apenas uma boa habilidade para se ter. Sempre que eu crio ideias, em vez de criar projetos superbase, eu tenho cerca de mais de 40 agora. Eu apenas o executo localmente. Ok?

Então isso economiza dinheiro. Stripe for payments, resend for email, AI SDK, e então look and feel. Eu estou dizendo use Shad CN UI. Se você não sabe o que é Shad CN UI, vá para ui.shadcn.com. É basicamente como um sistema de componentes de nível muito baixo, quase para você criar para construir em cima e para você criar seu próprio look and feel.

Isso apenas ajuda a criar estrutura para interação do usuário, o que você vê na página. Estrutura de componentes. Use modo escuro por padrão e com uma alternância de modo claro. Shad CN permite isso. E então processo.

Como eu gostaria de gerenciar isso? Você poderia criar um aplicativo linear no Claude Code? Eu já fiz isso antes. Ele codificou por cerca de 3 horas. Ele fez coisas que eu realmente não queria que ele fizesse porque eu não estava participando.

Então eu não quero fazer isso. Eu quero participar. Então vamos dizer para dividir em marcos. Então eu estou apenas dizendo, olhe. Use MCP para integrações.

MCP significa protocolo de contexto de modelo. Nós vamos entrar nisso em breve, mas é uma maneira para o Claude Co. realmente entrar na sua conta Stripe, ir na sua conta Supabase, olhar as tabelas, olhar os dados, olhar os assessores de segurança, olhar o armazenamento. Incrível. Então essa é uma maneira para o Claude Co.

ter acesso às suas ferramentas e serviços. E é isso. Ok? Então no lado direito, vamos, escreva o seguinte. Eu quero que você faça o mesmo para que possamos começar aqui.

Eu vou dizer, eu adicionei prd.md revise e elabore um plano. Eu vou apenas lemá-lo mais uma vez, dividido em marcos. Além disso, atualize claude.md. E, pessoal, na parte inferior aqui, diz aceitar edições em. Eu quero que você apenas digite shift tab.

Eu quero que você vá para o modo plano. Isso apenas muda o modo. Agora claudecode provavelmente teria feito isso automaticamente, mas só porque isso é tão crucial no início, eu só pensei que faria isso manualmente. Para voltar ao modo anterior, eu apenas clico em shift tab novamente, aceitar edição em. Ok.

Eu vou apertar enter. Então diz que Claude elaborou um plano e está pronto para executar. Eu gostaria de prosseguir? Eu vou apenas rolar para cima, e eu vou ler este plano. Então marco 7, recursos de IA.

Marco 6, pagamentos. Ótimo. Então eu vou rolar para baixo até 0.4. Digite aqui para dizer ao Claude o que mudar. Eu vou dizer, gere um arquivo plan dot m d.

K? Plano é um pouco diferente do PRD. O plano foi criado a partir do PRD, mas o plano tem todos os marcos disso. Ok. Agora eu vou apertar o número 1.

Sim. Limpar contexto. 15% do contexto foi usado e aceitar edições automaticamente está ligado. Eu vou dizer sim. Agora lembre-se que eu pedi para ele atualizar claude.md, e é isso que ele fez.

Se eu tivesse que clicar em claude.md, você pode ver que nós agora temos uma pilha de tecnologia. Ok? Eu já posso ver que ele ignorou o meu pedido proxy dot t s, então nós vamos lidar com isso. Talvez o seu tenha acertado em termos de proxy. Não importa.

Nós vamos fazer isso juntos em um segundo. Vamos dar uma olhada no nosso plano. Eu vou clicar com o botão direito e abrir a visualização. Para construir o plano, marco 1, instalar e configurar SHAD CN, modo escuro, Superbase e NET. Ótimo.

Vai apenas lidar com o marco 1 por enquanto. Ok. Então aqui está o que foi criado, atualizado, plano, Claude code, Claude MD atualizado, e está falando sobre middleware. Agora lembre-se que eu falei sobre codificação de IA e não-determinística ou probabilística. Sua saída será ligeiramente diferente da minha.

Tudo bem, pessoal. Por favor, abracem isso. Estamos falando sobre processo, pensamento de sistemas, gosto. Isso é o que é importante aqui. Não muito desse detalhe.

Seu aplicativo vai parecer diferente do meu, comportamento ligeiramente diferente. Eu vou encontrar áreas que você não vai encontrar. Você vai encontrar áreas que eu não vai encontrar. Juntos, vamos aprender sobre o processo. Então antes de começarmos o marco 1, e se eu pudesse apertar se eu apertar tab, você pode ver que agora eu aceitei o que ele está prevendo.

Em vez disso, eu vou dizer o que vamos fazer é isso. Abra um navegador para mim. Ok. Eu vou deixar o link abaixo. Renomeie o seu middleware para proxy para que você possa apenas copiar e colar este link.

Eu vou dizer middleware.ts é agora proxy.ts. Eu vou colar aquele link e apertar enter. Tudo bem. Isso é apenas algo que você ganha com experiência. Quando Next.

Js 17 sair, a primeira coisa que eu vou fazer é ir olhar todas as mudanças de quebra apenas para ver o que mudou. Mas, obviamente, meus projetos anteriores não são afetados. Quando eu falo sobre mudanças de quebra, eu falo sobre se você fosse atualizar um projeto existente para uma nova versão, o que eu realmente não faço. Eu tenho alguns projetos rodando no Next. Js 15.

Eles estão perfeitos. Então diz boa pegada. Ele intercepta blá blá blá. Não é um proxy reverso. Ótimo.

Oh, espere. Eu disse que não é proxy. Eu vou apertar para cima. É agora proxy dot t s. Desculpa.

Erro de digitação ali. Você pode ver que claud co pode às vezes alucinar. Ok. Isso é o que eu queria. Correto.

Ok. Então essa é a única peculiaridade ou caso limite para pensar. Certifique-se de que se ele falar sobre middleware, nós estamos agora usando proxy dot t s. Então apenas coloque isso em um post-it por enquanto para o futuro. Eu suspeito que LLMs começarão a se adaptar a isso.

Essa é a única peculiaridade. Pessoal, nós terminamos com esta lição, e eu vejo vocês na próxima.
"""

VOICE = "pt-BR-AntonioNeural"
OUTPUT_FILE = Path(__file__).parent.resolve() / "02-audio" / "orbit_lesson.mp3"

async def generate_audio():
    communicate = edge_tts.Communicate(TEXT, VOICE)
    await communicate.save(OUTPUT_FILE)
    print(f"Áudio gerado com sucesso: {OUTPUT_FILE}")

if __name__ == "__main__":
    asyncio.run(generate_audio())
