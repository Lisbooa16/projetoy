document.addEventListener("DOMContentLoaded", function () {
  const lojaSelect = document.querySelector("#id_loja_responsavel");
  if (!lojaSelect) return;

  lojaSelect.addEventListener("change", async function () {
    const lojaId = this.value;
    if (!lojaId) return;

    // Django Admin usa dois <select>s para o filter_horizontal
    const selectFrom = document.querySelector("#id_user_from");
    const selectTo = document.querySelector("#id_user_to");
    if (!selectFrom || !selectTo) return;

    // Mantém o que já está selecionado (lado direito)
    const selectedIds = Array.from(selectTo.options).map((opt) => opt.value);

    // Busca os novos vendedores
    const response = await fetch(`/api/vendedores/?loja=${lojaId}`);
    const data = await response.json();

    // Limpa o box da esquerda corretamente via API do Django Admin
    SelectBox.cache["id_user_from"] = [];
    SelectBox.cache["id_user_to"] = [];

    // Recria a lista da esquerda
    selectFrom.innerHTML = "";
    data.forEach((v) => {
      const opt = new Option(v.nome, v.id);
      if (!selectedIds.includes(String(v.id))) {
        selectFrom.add(opt);
      }
    });

    // Recarrega os caches internos do Django Admin
    SelectBox.init("id_user_from");
    SelectBox.init("id_user_to");
  });
});
