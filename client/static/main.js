document.addEventListener("DOMContentLoaded", () => {
    const profileSelect = document.getElementById("profile-select");
    const fileInput = document.getElementById("file-input");
    const uploadBtn = document.getElementById("upload-btn");
    const tabsContainer = document.getElementById("tabs-container");
    const contentsContainer = document.getElementById("tab-contents");

    const savedTaskIds = JSON.parse(localStorage.getItem("task_ids") || "[]");
    savedTaskIds.forEach(taskId => {
        createTab(taskId);
        pollStatus(taskId);
    });

    uploadBtn.addEventListener("click", async () => {
        const files = fileInput.files;
        const profileId = profileSelect.value;

        if (!profileId || files.length === 0) {
            alert("Выберите профиль и хотя бы один файл");
            return;
        }

        const formData = new FormData();
        formData.append("profile_id", profileId);
        for (const file of files) {
            formData.append("files", file);
        }

        try {
            console.log("[UPLOAD] Отправка запроса на /upload...");
            const resp = await fetch("/upload", {
                method: "POST",
                body: formData
            });

            if (!resp.ok) {
                const text = await resp.text();
                throw new Error(text);
            }

            const data = await resp.json();
            const taskId = data.task_id;
            console.log("[UPLOAD] Получен task_id:", taskId);

            createTab(taskId);
            pollStatus(taskId);

            const updatedIds = [...new Set([...savedTaskIds, taskId])];
            localStorage.setItem("task_ids", JSON.stringify(updatedIds));
        } catch (err) {
            console.error("[UPLOAD] Ошибка:", err.message);
            alert("Ошибка отправки: " + err.message);
        }
    });

    function createTab(taskId) {
        if (document.getElementById("tab-" + taskId)) return;

        const tab = document.createElement("div");
        tab.className = "tab";
        tab.id = "tab-" + taskId;
        tab.textContent = `Задача #${taskId}`;
        tab.dataset.taskId = taskId;

        const closeBtn = document.createElement("span");
        closeBtn.textContent = "×";
        closeBtn.className = "close";
        closeBtn.onclick = () => {
            tabsContainer.removeChild(tab);
            contentsContainer.removeChild(document.getElementById("content-" + taskId));

            const newList = JSON.parse(localStorage.getItem("task_ids") || "[]").filter(id => id !== taskId);
            localStorage.setItem("task_ids", JSON.stringify(newList));
        };
        tab.appendChild(closeBtn);

        tab.onclick = () => {
            document.querySelectorAll(".tab").forEach(t => t.classList.remove("active"));
            document.querySelectorAll(".tab-content").forEach(c => c.style.display = "none");

            tab.classList.add("active");
            document.getElementById("content-" + taskId).style.display = "block";
        };

        tabsContainer.appendChild(tab);

        const content = document.createElement("div");
        content.className = "tab-content";
        content.id = "content-" + taskId;

        content.innerHTML = `
            <section class="task-header">
                <span><strong>📂 Задача #${taskId}</strong></span>
                <span class="status">Статус: <span class="task-status">Ожидание...</span></span>

                <label>Формат:</label>
                <select class="download-format">
                    <option value="txt">TXT</option>
                    <option value="pdf">PDF</option>
                    <option value="docx">DOCX</option>
                </select>

                <button class="download-zip" data-task-id="${taskId}">Скачать ZIP</button>
                <button class="download-single">Скачать файл</button>
            </section>
            <section class="main-content">
                <div class="text-column">
                    <h2>Оригинал</h2>
                    <textarea class="original-text" readonly>Загрузка...</textarea>
                </div>
                <div class="text-column">
                    <h2>Редактировано</h2>
                    <textarea class="redacted-text">Загрузка...</textarea>
                </div>
            </section>
            <section class="report">
                <h2>Отчёт</h2>
                <pre class="report-content">Ожидание результата...</pre>
            </section>
        `;

        content.style.display = "none";
        contentsContainer.appendChild(content);
        tab.click();
    }

    function pollStatus(taskId) {
        const statusText = () => document.querySelector(`#content-${taskId} .task-status`);

        const interval = setInterval(async () => {
            try {
                const resp = await fetch(`/status/${taskId}`);
                const data = await resp.json();

                console.log(`[STATUS] Задача ${taskId}:`, data.status);
                statusText().textContent = data.status;

                if (data.status === "completed") {
                    clearInterval(interval);
                    loadResults(taskId);
                }
            } catch (error) {
                console.error("[STATUS] Ошибка получения статуса:", error);
            }
        }, 3000);
    }

    async function loadResults(taskId) {
        console.log(`[LOAD] Загружаем результат для ${taskId}`);
        const content = document.getElementById("content-" + taskId);

        try {
            const resp = await fetch(`/results/${taskId}`);
            const text = await resp.text();
            console.log(`[LOAD] Ответ от /results/${taskId}:`, text);

            let data;
            try {
                data = JSON.parse(text);
            } catch (parseError) {
                console.error("[LOAD] Ошибка парсинга JSON:", parseError);
                content.querySelector(".original-text").textContent = "Ошибка разбора ответа";
                return;
            }

            const report = data.reports?.[0];
            if (!report || !report.report) {
                console.warn(`[LOAD] Пустой или некорректный отчёт для ${taskId}`);
                content.querySelector(".original-text").textContent = "Ошибка: пустой отчёт";
                content.querySelector(".redacted-text").value = "Ошибка загрузки";
                content.querySelector(".report-content").textContent = "Пустой результат";
                return;
            }

            const filename = report.file || `Задача #${taskId}`;
            const tabElem = document.getElementById("tab-" + taskId);
            if (tabElem) tabElem.firstChild.textContent = filename + " ";

            content.querySelector(".original-text").textContent = report.report.original_text || "—";
            content.querySelector(".redacted-text").value = report.report.reduced_text || "—";

            const replacements = report.report.replacements || [];
            const reportBlock = content.querySelector(".report-content");
            if (replacements.length > 0) {
                reportBlock.textContent = replacements
                    .map(r => `${r.entity_type}: ${r.original} → ${r.replacement}`)
                    .join("\n");
            } else {
                reportBlock.textContent = "Нет замен";
            }

            content.querySelector(".download-zip").onclick = () => {
                window.location.href = `/download/${taskId}`;
            };

            content.querySelector(".download-single").onclick = () => {
                const redactedText = content.querySelector(".redacted-text").value;
                const formatSelector = content.querySelector(".download-format");
                if (!formatSelector) {
                    alert("Не выбран формат для скачивания.");
                    return;
                }

                const format = formatSelector.value;
                const filenameBase = filename.replace(/\.[^/.]+$/, "");

                if (format === "txt") {
                    const blob = new Blob([redactedText], { type: "text/plain;charset=utf-8" });
                    triggerDownload(blob, `${filenameBase}.txt`);
                } else if (format === "pdf") {
                    const pdf = new window.jspdf.jsPDF();
                    pdf.setFont("Courier");
                    pdf.setFontSize(12);
                    const lines = pdf.splitTextToSize(redactedText, 180);
                    pdf.text(lines, 10, 10);
                    pdf.save(`${filenameBase}.pdf`);
                } else if (format === "docx") {
                    const doc = new window.docx.Document({
                        sections: [{
                            children: [new window.docx.Paragraph(redactedText)],
                        }],
                    });
                    window.docx.Packer.toBlob(doc).then(blob => {
                        triggerDownload(blob, `${filenameBase}.docx`);
                    });
                }
            };

            function triggerDownload(blob, filename) {
                const link = document.createElement("a");
                link.href = URL.createObjectURL(blob);
                link.download = filename;
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
            }

        } catch (error) {
            console.error("[LOAD] Ошибка при обработке результатов:", error);
            content.querySelector(".original-text").textContent = "Ошибка загрузки";
            content.querySelector(".redacted-text").value = "Ошибка загрузки";
            content.querySelector(".report-content").textContent = "Ошибка загрузки отчёта";
        }
    }
});
