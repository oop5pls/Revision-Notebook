const CONFIG = {
    queryRoute: "/query",
    fileUploadRoute: "/file/upload",
    fileDeleteRoute: "/file/delete",
};

const queryInput = document.getElementById("query-input");
const queryForm = document.querySelector(".query-form");
const resultsBox = document.getElementById("query-results");
const fileInput = document.getElementById("file-input");
const categoryInput = document.getElementById("category-input");
const subjectInput = document.getElementById("subject-input");
const fileList = document.getElementById("file-list");
const submitUploadBtn = document.getElementById("submit-upload-btn");
const selectedFileNameDisplay = document.getElementById("selected-file-name");

queryForm?.addEventListener("submit", async (event) => {
    event.preventDefault();
    const query = queryInput?.value.trim();
    if (!query || !resultsBox) return;

    resultsBox.innerHTML = '<p class="placeholder-text">Searching knowledge base...</p>';

    try {
        const response = await fetch(CONFIG.queryRoute, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ query }),
        });
        if (!response.ok) throw new Error(`Query failed: ${response.status}`);

        const data = await response.json();
        resultsBox.textContent = data.result;
    } catch (error) {
        resultsBox.textContent = `Error: ${error instanceof Error ? error.message : "Unknown error"}`;
    }
});

fileInput?.addEventListener("change", () => {
    const file = fileInput.files?.[0];
    if (selectedFileNameDisplay) {
        selectedFileNameDisplay.textContent = file
            ? `Selected: ${file.name}`
            : "No file selected";
    }
});

submitUploadBtn?.addEventListener("click", async () => {
    const file = fileInput?.files?.[0];
    if (!file || !categoryInput || !subjectInput) return;

    const allowedExtensions = ["csv", "xlsx", "xls"];
    const fileExtension = file.name.split(".").pop()?.toLowerCase();
    if (!fileExtension || !allowedExtensions.includes(fileExtension)) {
        alert("Invalid file type. Please upload a CSV or Excel file.");
        return;
    }

    const category = categoryInput.value.trim();
    const subject = subjectInput.value.trim();
    if (!category || !subject) {
        alert("Both Category and Subject are required before uploading.");
        return;
    }

    const formData = new FormData();
    formData.append("file", file);
    formData.append("category", category);
    formData.append("subject", subject);

    try {
        const response = await fetch(CONFIG.fileUploadRoute, {
            method: "POST",
            body: formData,
        });
        if (!response.ok) throw new Error(`Upload failed: ${response.status}`);

        const data = await response.json();
        addFileToList(file.name, data.id ?? file.name);
    } catch (error) {
        alert(`Upload error: ${error instanceof Error ? error.message : "Unknown error"}`);
    }
});

function addFileToList(filename, id) {
    if (!fileList) return;
    fileList.querySelector(".placeholder")?.remove();

    const item = document.createElement("li");
    item.className = "file-item";

    const name = document.createElement("span");
    name.textContent = filename;
    item.appendChild(name);

    fileList.appendChild(item);
}
