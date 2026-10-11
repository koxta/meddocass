const upload = document.querySelector("#upload")
const status = document.querySelector("#status")
const documents = document.querySelector("#documents")
const form = document.querySelector("#ask")
const button = form.querySelector("button")
const answer = document.querySelector("#answer")

async function api(path, options) {
  const response = await fetch(path, options)
  const body = await response.json().catch(() => ({}))
  if (!response.ok) {
    throw new Error(typeof body.detail === "string" ? body.detail : response.statusText)
  }
  return body
}

function el(tag, text) {
  const node = document.createElement(tag)
  node.textContent = text
  return node
}

async function loadDocuments() {
  const docs = await api("/documents")
  documents.replaceChildren(...docs.map((doc) => el("li", doc.filename)))
}

upload.addEventListener("change", async () => {
  const data = new FormData()
  data.append("file", upload.files[0])
  upload.value = ""
  status.textContent = "Uploading..."
  try {
    const doc = await api("/documents", { method: "POST", body: data })
    status.textContent = `Indexed ${doc.filename}`
    await loadDocuments()
  } catch (error) {
    status.textContent = error.message
  }
})

form.addEventListener("submit", async (event) => {
  event.preventDefault()
  button.disabled = true
  answer.textContent = "Thinking..."
  try {
    const result = await api("/ask", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question: form.question.value }),
    })
    const references = el("ul", "")
    for (const ref of result.references) {
      const page = ref.page ? `, p. ${ref.page}` : ""
      references.append(el("li", `[${ref.source_id}] ${ref.filename}${page}: ${ref.snippet}`))
    }
    answer.replaceChildren(el("p", result.answer), references)
  } catch (error) {
    answer.textContent = error.message
  } finally {
    button.disabled = false
  }
})

loadDocuments().catch((error) => (status.textContent = error.message))
