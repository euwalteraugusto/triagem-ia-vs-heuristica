# -*- coding: utf-8 -*-
"""
Gera massa de teste com diversidade lexical REAL (cada instância é um texto
distinto, não uma repetição do mesmo corpo com número de ticket trocado).
Corrige a pseudo-replicação identificada na v1 (gerar_massa.py).
"""
import json
import random

random.seed(42)

# Cada categoria tem N variações de ASSUNTO+CORPO genuinamente diferentes
# (vocabulário, estrutura de frase e contexto diferentes), não apenas o
# mesmo texto com um número trocado.

SIMPLES = {
    "Dívidas e Cobranças": [
        ("Segunda via de fatura", "Por favor, me enviem o boleto atualizado deste mês. O antigo venceu."),
        ("Boleto não chegou por e-mail", "Não recebi o boleto de setembro na minha caixa de entrada, podem reenviar?"),
        ("Preciso da fatura do cartão", "Onde consigo baixar a fatura do meu cartão de crédito referente ao mês passado?"),
        ("Valor da parcela errado", "A parcela que apareceu no aplicativo está diferente do combinado no contrato."),
    ],
    "Documentos e Protocolos": [
        ("Informe de Rendimentos 2025", "Segue o informe para declaração do imposto de renda."),
        ("Preciso do comprovante de residência", "Vocês podem emitir um comprovante de vínculo para eu levar ao banco?"),
        ("Cópia do contrato assinado", "Solicito uma via digital do contrato de prestação de serviços que assinei em março."),
        ("Certidão negativa de débitos", "Como faço para solicitar a certidão negativa junto à empresa?"),
    ],
    "Alertas de Segurança": [
        ("Novo acesso detectado", "Identificamos um login em um novo dispositivo (iPhone 13). Se não foi você, troque sua senha."),
        ("Tentativa de login suspeita", "Alguém tentou acessar sua conta de um local incomum. Confirme se foi você."),
        ("Código de verificação solicitado", "Um código de segurança foi solicitado para sua conta às 03h da manhã."),
        ("Dispositivo desconhecido conectado", "Detectamos que um computador novo acessou seus dados ontem à noite."),
    ],
    "Trabalho e Projetos": [
        ("Entrevista técnica - Desenvolvedor Python", "Confirmo minha presença na entrevista de amanhã às 14h."),
        ("Reunião de alinhamento do sprint", "Podemos remarcar a reunião de planejamento para quinta-feira?"),
        ("Feedback sobre a proposta técnica", "Segue meu retorno sobre o documento de arquitetura que vocês enviaram."),
        ("Disponibilidade para o projeto novo", "Gostaria de saber se ainda há vaga na equipe do projeto de automação."),
    ],
    "Suporte Técnico": [
        ("Reset de senha do painel", "Clique no link abaixo para cadastrar sua nova senha de acesso ao sistema interno."),
        ("Sistema não abre no navegador", "A tela fica carregando infinitamente quando tento acessar o painel pelo Chrome."),
        ("Botão de exportar não funciona", "Ao clicar em exportar relatório, nada acontece e não aparece nenhum erro."),
        ("Erro 404 ao acessar o link", "O link que vocês mandaram por e-mail está retornando página não encontrada."),
    ],
    "Promoções e Propaganda": [
        ("Aproveite seu limite pré-aprovado", "Você tem R$ 10.000 disponíveis para empréstimo com taxas reduzidas."),
        ("Cashback em dobro este final de semana", "Compre com o cartão da sua conta e ganhe o dobro de pontos até domingo."),
        ("Última chance: desconto de 30%", "Assine o plano anual hoje e garanta 30% de desconto por tempo limitado."),
        ("Convite exclusivo para novos produtos", "Conheça a nova linha de investimentos disponível só para clientes VIP."),
    ],
    "Assinaturas e Serviços": [
        ("Cancelamento de conta premium", "Gostaria de cancelar minha assinatura mensal do plano Pro."),
        ("Upgrade de plano solicitado", "Quero migrar do plano básico para o plano empresarial ainda este mês."),
        ("Renovação automática ativada", "Percebi que minha assinatura renovou sozinha, isso está certo?"),
        ("Dúvida sobre benefícios do plano", "O plano atual inclui suporte prioritário ou preciso contratar à parte?"),
    ],
    "Newsletters e Notícias": [
        ("Fechamento do Ibovespa", "Confira as principais altas e baixas do mercado financeiro nesta semana."),
        ("Resumo econômico da semana", "Veja como o dólar e a taxa Selic se comportaram nos últimos dias."),
        ("Panorama do mercado de tecnologia", "As principais notícias do setor de fintechs publicadas nesta edição."),
        ("Boletim semanal de investimentos", "Confira a análise dos especialistas sobre o cenário macroeconômico atual."),
    ],
    "Eventos e Convites": [
        ("Ingresso - Summit de Inovação", "Seu QR Code para entrada no evento está anexado."),
        ("Convite para webinar gratuito", "Participe da live sobre tendências de mercado nesta quinta às 19h."),
        ("Confirmação de inscrição no workshop", "Sua vaga na oficina de capacitação foi confirmada para o dia 20."),
        ("Save the date: conferência anual", "Reserve a data do nosso maior evento do ano na agenda."),
    ],
    "Viagens e Reservas": [
        ("Confirmação de voo - SP/RJ", "Seu bilhete aéreo para a reunião de diretoria foi emitido."),
        ("Reserva de hotel confirmada", "Sua estadia em Curitiba de 10 a 12 de outubro está garantida."),
        ("Check-in disponível para seu voo", "Faça o check-in online até 2 horas antes do embarque."),
        ("Alteração no horário do embarque", "Seu voo teve o horário de partida adiantado em 40 minutos."),
    ],
}

COMPLEXOS = {
    "Suporte Técnico": [
        ("App travou e cobrou juros", "Tentei pagar a fatura ontem, mas a tela de PIX do aplicativo de vocês deu erro 500 o dia todo. Agora estão me cobrando multa por atraso. Quero o estorno da multa."),
        ("Erro de token e bloqueio judicial", "Estou tentando sacar meus dividendos, mas o SMS do token não chega e o app diz que minha conta tem restrição judicial. O que está acontecendo?"),
        ("Alerta de indisponibilidade nos servidores AWS", "As instâncias de banco de dados estão batendo 100% de CPU. Precisamos de aprovação imediata de orçamento para escalar o cluster antes que o app caia."),
        ("Falha na sincronização entre app e site", "O saldo que aparece no aplicativo é diferente do que vejo no site, e isso está me impedindo de fazer uma transferência importante hoje."),
    ],
    "Alertas de Segurança": [
        ("Fui roubado - Cancelem os cartões", "Levaram meu celular desbloqueado. O 0800 de suporte não atende, preciso que bloqueiem qualquer tentativa de empréstimo ou pix imediatamente!"),
        ("Suspeita de clonagem de cartão", "Notei três compras que não reconheço no exterior, mas o cartão físico nunca saiu da minha carteira."),
        ("Conta acessada de outro país", "Recebi um alerta de login na Rússia enquanto estava dormindo no Brasil, e agora não consigo mais entrar na minha conta."),
        ("Golpe de phishing recebido", "Recebi um e-mail em nome de vocês pedindo meus dados bancários, mas o domínio do remetente parecia falso."),
    ],
    "Documentos e Protocolos": [
        ("Divergência contratual na API de pagamentos", "O contrato NDA que vocês enviaram cita retenção de dados por 5 anos, mas a documentação da API de vocês diz 2 anos. Precisamos alinhar isso antes do deploy."),
        ("Notificação extrajudicial - Regularização de licenças", "Identificamos o uso de softwares sem licenciamento ativo nas máquinas da equipe de engenharia. Regularizem o pagamento ou enfrentaremos multas."),
        ("Cláusula de rescisão ambígua no contrato", "O item 4.2 do contrato de prestação de serviço permite rescisão a qualquer momento, mas o anexo financeiro cobra multa de 6 meses. Qual prevalece?"),
        ("Pendência de assinatura em contrato internacional", "O jurídico da matriz nos EUA pede aditivo bilíngue, mas nosso modelo padrão só existe em português. Como seguimos com o protocolo?"),
    ],
    "Finanças Pessoais": [
        ("Reembolso de hospedagem vs Adiantamento", "O hotel do evento em Miami cobrou no meu cartão pessoal, mas eu já havia solicitado adiantamento corporativo. Como conciliar isso no fechamento do mês?"),
        ("Divergência entre extrato pessoal e reembolso corporativo", "Recebi o reembolso da viagem, mas o valor não bate com o que gastei do meu próprio bolso durante a conferência."),
        ("Imposto retido indevidamente no salário", "Meu contracheque veio com uma retenção de IR maior do que o esperado, e isso afetou meu planejamento financeiro pessoal do mês."),
        ("Conciliação de despesas mistas do cartão", "Usei o cartão corporativo para uma despesa pessoal por engano durante a viagem e preciso entender como devolver o valor."),
    ],
    "Assinaturas e Serviços": [
        ("Cobrança dupla cancelando meu limite", "Cancelei a assinatura premium mês passado pelo site parceiro, mas a parcela veio na fatura de hoje e estourou meu limite, bloqueando minhas compras."),
        ("Plano cancelado mas serviço continua ativo", "Pedi o cancelamento há duas semanas e recebi confirmação por e-mail, porém meu acesso ao aplicativo premium continua liberado e sendo cobrado."),
        ("Downgrade automático sem aviso", "Meu plano empresarial foi rebaixado para o básico sem eu solicitar, e perdi acesso a integrações que a equipe usa todos os dias."),
        ("Renovação cobrada em moeda diferente", "A renovação anual veio cobrada em dólar mesmo eu tendo contratado o plano em reais no ano passado."),
    ],
    "Trabalho e Projetos": [
        ("Nova feature de investimentos liberada", "A funcionalidade de CDB foi para produção. Segue o material de propaganda para dispararmos aos clientes e a documentação técnica para o FAQ."),
        ("Conflito de prioridades entre squads", "O time de dados pediu urgência num relatório enquanto o time de produto pediu urgência numa integração, e ambos têm o mesmo prazo."),
        ("Revisão de arquitetura antes do deploy", "Precisamos que alguém do time sênior valide o desenho da nova esteira de dados antes de liberarmos para produção na sexta."),
        ("Atraso na entrega por dependência externa", "Nosso módulo está pronto, mas depende de uma API de um parceiro que ainda não entregou o ambiente de homologação."),
    ],
    "Dívidas e Cobranças": [
        ("Comprei, devolvi, mas a cobrança continua", "Fiz uma compra na loja parceira usando o cartão de vocês. Já devolvi o produto e tenho o comprovante dos correios, mas a segunda parcela veio cobrando."),
        ("Cobrança de serviço que nunca contratei", "Apareceu uma cobrança recorrente de um serviço que não reconheço, e isso já aconteceu duas vezes seguidas."),
        ("Negociação de dívida com desconto prometido", "Um atendente me ofereceu 40% de desconto para quitar a dívida à vista, mas o valor no boleto veio sem o desconto."),
        ("Parcelamento não refletido na fatura", "Parcelei uma compra em 6 vezes pelo aplicativo, mas a fatura deste mês cobrou o valor integral de uma vez."),
    ],
    "Newsletters e Notícias": [
        ("Análise semanal: juros e câmbio", "Nosso time de economistas comenta os principais movimentos do dólar e da taxa de juros nesta semana."),
        ("Fintechs em alta: o que mudou no setor", "Reportagem especial sobre fusões e aquisições que movimentaram o mercado de pagamentos digitais."),
        ("Editorial: o futuro do crédito no Brasil", "Coluna de opinião discutindo tendências regulatórias para o mercado de crédito nos próximos anos."),
        ("Radar de mercado: criptomoedas e renda fixa", "Panorama comparativo entre a volatilidade de cripto e a segurança da renda fixa neste trimestre."),
    ],
    "Eventos e Convites": [
        ("Convite para painel sobre open finance", "Você foi selecionado para participar como palestrante no painel sobre open finance no próximo mês."),
        ("Confirmação de patrocínio para o hackathon", "Precisamos da confirmação da cota de patrocínio até sexta para garantir o logo no material do evento."),
        ("Agenda da conferência internacional", "Segue a grade completa de palestras e workshops para os três dias do evento em São Paulo."),
        ("Convite para comitê de inovação", "Você foi convidado a integrar o comitê que vai decidir os investimentos em inovação do próximo ano."),
    ],
    "Viagens e Reservas": [
        ("Remarcação de voo por reunião cancelada", "A reunião com o investidor em Londres foi cancelada, preciso remarcar o voo e o hotel já reservados."),
        ("Reembolso de viagem corporativa negado", "Solicitei reembolso de uma viagem cancelada por motivos de saúde, mas o financeiro negou alegando prazo expirado."),
        ("Conflito de datas entre duas viagens a trabalho", "Fui escalado para dois eventos em cidades diferentes na mesma semana e preciso decidir qual reserva manter."),
        ("Upgrade de classe não aplicado na reserva", "Paguei pelo upgrade para classe executiva, mas o bilhete emitido ainda mostra classe econômica."),
    ],
}


def montar_massa():
    massa = []
    id_counter = 1
    for cat, itens in SIMPLES.items():
        for assunto, corpo in itens:
            massa.append({
                "id": str(id_counter),
                "remetente": f"contato{id_counter}@teste.com",
                "assunto": assunto,
                "corpo": corpo,
                "categoria_esperada": cat,
                "complexidade": "Simples",
            })
            id_counter += 1
    for cat, itens in COMPLEXOS.items():
        for assunto, corpo in itens:
            massa.append({
                "id": str(id_counter),
                "remetente": f"contato{id_counter}@teste.com",
                "assunto": assunto,
                "corpo": corpo,
                "categoria_esperada": cat,
                "complexidade": "Complexo",
            })
            id_counter += 1
    random.shuffle(massa)
    return massa


if __name__ == "__main__":
    massa = montar_massa()
    with open("mock_emails.json", "w", encoding="utf-8") as f:
        json.dump(massa, f, ensure_ascii=False, indent=2)

    # Checagem de diversidade lexical: nenhum corpo deve se repetir
    corpos = [m["corpo"] for m in massa]
    unicos = len(set(corpos))
    print(f"Total de e-mails: {len(massa)}")
    print(f"Textos únicos (corpo): {unicos} / {len(massa)}  -> {'OK, sem pseudo-replicação' if unicos == len(massa) else 'ATENÇÃO: ainda há repetição'}")
