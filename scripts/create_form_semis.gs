/**
 * Cria o Google Form dos palpites das SEMIFINAIS do Bolão da Copa 2026.
 *
 * Como usar (uma vez só):
 *   1. Abra https://script.google.com → Novo projeto.
 *   2. Apague o conteúdo, cole este arquivo inteiro e clique em ▶ Executar
 *      (função criarFormSemis). Autorize quando pedir.
 *   3. Abra "Registro de execução": lá estão o link pra mandar no grupo
 *      (publishedUrl), o link de edição (editUrl) e a planilha de respostas.
 *
 * A ordem das perguntas espelha a ordem dos confrontos em secondstage/data.js
 * (stage SEMI) — não mude a ordem, o importador de respostas depende dela.
 */
function criarFormSemis() {
  const APOSTADORES = [
    "Diego", "Miguel", "Gabriel", "Leandro", "Lucas Volcov", "Junior",
    "Alisson", "Thiago", "Douglas", "Guilherme B.", "Osmar", "Andrew",
    "Pedro", "Manuel", "Murilo",
  ];
  // mesma ordem de secondstage/data.js (stage SEMI) — vencedores das quartas
  const JOGOS = [
    ["França", "Espanha"],
    ["Inglaterra", "Argentina"],
  ];

  const form = FormApp.create("⚽ Bolão da Copa — Semifinais");
  form.setDescription(
    "Palpites das SEMIFINAIS — cada acerto vale +5 pontos!\n\n" +
    "⏰ Prazo: antes do primeiro jogo das semis.\n" +
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
      .setTitle("Jogo " + (i + 1) + ": " + j[0] + " × " + j[1] + " — quem avança?")
      .setChoiceValues(j)
      .setRequired(true);
  });

  // respostas numa planilha, pra exportar fácil depois
  const ss = SpreadsheetApp.create("Bolão Semifinais — respostas");
  form.setDestination(FormApp.DestinationType.SPREADSHEET, ss.getId());

  Logger.log("Link pro grupo:  " + form.shortenFormUrl(form.getPublishedUrl()));
  Logger.log("Link de edição:  " + form.getEditUrl());
  Logger.log("Planilha de respostas: " + ss.getUrl());
}
