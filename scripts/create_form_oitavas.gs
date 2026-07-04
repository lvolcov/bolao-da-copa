/**
 * Cria o Google Form dos palpites das OITAVAS do Bolão da Copa 2026.
 *
 * Como usar (uma vez só):
 *   1. Abra https://script.google.com → Novo projeto.
 *   2. Apague o conteúdo, cole este arquivo inteiro e clique em ▶ Executar
 *      (função criarFormOitavas). Autorize quando pedir.
 *   3. Abra "Registro de execução": lá estão o link pra mandar no grupo
 *      (publishedUrl) e o link de edição (editUrl).
 *
 * A ordem das perguntas espelha a ordem dos confrontos em secondstage/data.js —
 * não mude a ordem, o importador de respostas depende dela.
 * Obs.: Jogo 7 assume a Colômbia classificada (Suíça × Colômbia). Se Gana
 * passar, edite as opções dessa pergunta no formulário.
 */
function criarFormOitavas() {
  const APOSTADORES = [
    "Diego", "Miguel", "Gabriel", "Leandro", "Lucas Volcov", "Junior",
    "Alisson", "Thiago", "Douglas", "Guilherme B.", "Osmar", "Andrew",
    "Pedro", "Manuel", "Murilo",
  ];
  // mesma ordem de secondstage/data.js (stages.r16.matches)
  const JOGOS = [
    ["Canadá", "Marrocos"],
    ["Paraguai", "França"],
    ["Estados Unidos", "Bélgica"],
    ["Espanha", "Portugal"],
    ["Brasil", "Noruega"],
    ["México", "Inglaterra"],
    ["Suíça", "Colômbia"],
    ["Egito", "Argentina"],
  ];

  const form = FormApp.create("⚽ Bolão da Copa — Oitavas de Final");
  form.setDescription(
    "Palpites das OITAVAS — cada acerto vale +3 pontos!\n\n" +
    "⏰ Prazo: antes do primeiro jogo — 04/07 às 18:00 (horário do UK).\n" +
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
  const ss = SpreadsheetApp.create("Bolão Oitavas — respostas");
  form.setDestination(FormApp.DestinationType.SPREADSHEET, ss.getId());

  Logger.log("Link pro grupo:  " + form.shortenFormUrl(form.getPublishedUrl()));
  Logger.log("Link de edição:  " + form.getEditUrl());
  Logger.log("Planilha de respostas: " + ss.getUrl());
}
