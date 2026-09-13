async function generateMap() {
  const link = document.getElementById("link").value;
  const lang = document.getElementById("lang").value;
  const resultDiv = document.getElementById("result");
  resultDiv.textContent = "...";

  const response = await fetch("/generate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ link, lang, fmt: "svg" }),
  });

  if (!response.ok) {
    const error = await response.json();
    resultDiv.textContent = error.detail;
    return;
  }

  const blob = await response.blob();
  const url = URL.createObjectURL(blob);
  resultDiv.innerHTML = `<img src="${url}" alt="map"><br><a href="${url}" download="cartocrisp.svg">Download</a>`;
}
