/**
 * Cria o Google Form dos palpites da FINAL do Bolão da Copa 2026.
 *
 * Como usar (uma vez só):
 *   1. Abra https://script.google.com → Novo projeto.
 *   2. Apague o conteúdo, cole este arquivo inteiro e clique em ▶ Executar
 *      (função criarFormFinal). Autorize quando pedir.
 *   3. Abra "Registro de execução": lá estão o link pra mandar no grupo
 *      (publishedUrl), o link de edição (editUrl) e a planilha de respostas.
 *
 * A ordem das perguntas espelha a ordem dos confrontos em secondstage/data.js
 * (stage FINAL) — não mude a ordem, o importador de respostas depende dela.
 */
function criarFormFinal() {
  const APOSTADORES = [
    "Diego", "Miguel", "Gabriel", "Leandro", "Lucas Volcov", "Junior",
    "Alisson", "Thiago", "Douglas", "Guilherme B.", "Osmar", "Andrew",
    "Pedro", "Manuel", "Murilo",
  ];
  // mesma ordem de secondstage/data.js (stage FINAL) — vencedores das semis
  const JOGOS = [
    ["Espanha", "Argentina"],
  ];
  // disputa de 3º lugar — perdedores das semis. NÃO vale pontos, só por diversão.
  const TERCEIRO = ["França", "Inglaterra"];

  const form = FormApp.create("⚽ Bolão da Copa — Final");
  form.setDescription(
    "Palpite da FINAL — acertar o campeão vale +10 pontos!\n\n" +
    "🥉 Tem também a disputa de 3º lugar (só por curiosidade, NÃO vale pontos).\n\n" +
    "⏰ Prazo: antes do apito inicial da final.\n" +
    "Palpite enviado depois do prazo não vale. Boa sorte! 🍀"
  );
  form.setLimitOneResponsePerUser(false); // sem exigir login Google
  form.setAllowResponseEdits(true);

  form.addListItem()
    .setTitle("Quem é você?")
    .setChoiceValues(APOSTADORES)
    .setRequired(true);

  JOGOS.forEach(function (j, i) {
    form.addMultipleChoiceItem()
      .setTitle("Jogo " + (i + 1) + ": " + j[0] + " × " + j[1] + " — quem é o campeão?")
      .setChoiceValues(j)
      .setRequired(true);
  });

  // disputa de 3º lugar — fica por último, não vale pontos
  form.addMultipleChoiceItem()
    .setTitle(
      "🥉 3º lugar: " + TERCEIRO[0] + " × " + TERCEIRO[1] +
      " — quem fica com o bronze? (não vale pontos)"
    )
    .setChoiceValues(TERCEIRO)
    .setRequired(true);

  // respostas numa planilha, pra exportar fácil depois
  const ss = SpreadsheetApp.create("Bolão Final — respostas");
  form.setDestination(FormApp.DestinationType.SPREADSHEET, ss.getId());

  Logger.log("Link pro grupo:  " + form.shortenFormUrl(form.getPublishedUrl()));
  Logger.log("Link de edição:  " + form.getEditUrl());
  Logger.log("Planilha de respostas: " + ss.getUrl());
}
