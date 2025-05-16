document.addEventListener("DOMContentLoaded", () => {
    const profileSelect     = document.getElementById("profile-select");
    const fileInput         = document.getElementById("file-input");
    const uploadBtn         = document.getElementById("upload-btn");
    const tabsContainer     = document.getElementById("tabs-container");
    const contentsContainer = document.getElementById("tab-contents");
  
    const docxLib = window.docx || window.Docx;
    if (!docxLib || !docxLib.Packer) {
      console.error("Docx.js не найден! Проверьте порядок <script>.");
    }
  
    const pdfjsLib = window.pdfjsLib;
    if (!pdfjsLib) {
      console.error("PDF.js не найден!");
    }
  
    let savedTaskIds   = JSON.parse(localStorage.getItem("task_ids")    || "[]");
    const tabNames     = JSON.parse(localStorage.getItem("tab_names")   || "{}");
    const editedTexts  = JSON.parse(localStorage.getItem("edited_texts")|| "{}");
  
    function persistState() {
      localStorage.setItem("task_ids",     JSON.stringify(savedTaskIds));
      localStorage.setItem("tab_names",    JSON.stringify(tabNames));
      localStorage.setItem("edited_texts", JSON.stringify(editedTexts));
    }
  
    // ======== Вернуть вкладки ========
    (async function restoreTabs() {
      const goodIds = [];
      for (const taskId of savedTaskIds) {
        try {
          const resp = await fetch(`/status/${taskId}`);
          if (resp.ok) {
            goodIds.push(taskId);
            createTabPlaceholder(taskId, goodIds.length - 1);
            pollStatus(taskId);
          }
        } catch {}
      }
      savedTaskIds = goodIds;
      persistState();
    })();
  
    // ======== Upload ========
    uploadBtn.addEventListener("click", async () => {
      const files     = Array.from(fileInput.files);
      const profileId = profileSelect.value;
      if (!profileId || !files.length) {
        alert("Выберите профиль и хотя бы один файл");
        return;
      }
  
      const prepared = await Promise.all(files.map(async f => {
        const ext = f.name.split(".").pop().toLowerCase();
        if (ext === "pdf") {
          const ab  = await f.arrayBuffer();
          const pdf = await pdfjsLib.getDocument({ data: ab }).promise;
          let txt   = "";
          for (let i = 1; i <= pdf.numPages; i++) {
            const page    = await pdf.getPage(i);
            const content = await page.getTextContent();
            txt += content.items.map(it => it.str).join(" ") + "\n\n";
          }
          return new File([txt], f.name.replace(/\.pdf$/i, ".txt"), { type: "text/plain" });
        }
        return f;
      }));
  
      const fd = new FormData();
      fd.append("profile_id", profileId);
      prepared.forEach(f => fd.append("files", f));
  
      try {
        const resp = await fetch("/upload", { method: "POST", body: fd });
        if (!resp.ok) throw new Error("Некорректный файл");
        const { task_id: taskId } = await resp.json();
  
        if (!savedTaskIds.includes(taskId)) {
          savedTaskIds.push(taskId);
          tabNames[taskId] = `Задача ${savedTaskIds.length}`;
          persistState();
          createTabPlaceholder(taskId, savedTaskIds.length - 1);
          pollStatus(taskId);
        }
      } catch (err) {
        console.error("[UPLOAD]", err);
        alert("Ошибка отправки: " + err.message);
      }
    });
  
    // ======== Создание вкладки ========
    function createTabPlaceholder(taskId, idx = 0) {
      if (document.getElementById("tab-" + taskId)) return;
      const tab = document.createElement("div");
      tab.className      = "tab";
      tab.id             = "tab-" + taskId;
      tab.dataset.taskId = taskId;
  
      const label = document.createElement("span");
      label.className   = "tab-label";
      label.textContent = tabNames[taskId] || `Задача ${idx+1}`;
      tab.appendChild(label);
  
      const closeBtn = document.createElement("span");
      closeBtn.className   = "close";
      closeBtn.textContent = "×";
      closeBtn.onclick     = () => {
        tab.remove();
        document.getElementById("content-" + taskId)?.remove();
        savedTaskIds = savedTaskIds.filter(id => id !== taskId);
        delete tabNames[taskId];
        delete editedTexts[taskId];
        persistState();
      };
      tab.appendChild(closeBtn);
  
      label.ondblclick = () => {
        const inp = document.createElement("input");
        inp.type  = "text";
        inp.value = label.textContent;
        tab.replaceChild(inp, label);
        inp.focus();
        inp.onblur = () => {
          const v = inp.value.trim() || label.textContent;
          tabNames[taskId] = v;
          label.textContent = v;
          tab.replaceChild(label, inp);
          persistState();
        };
      };
  
      tab.onclick = () => {
        document.querySelectorAll(".tab").forEach(t => t.classList.remove("active"));
        document.querySelectorAll(".tab-content").forEach(c => c.style.display = "none");
        tab.classList.add("active");
        document.getElementById("content-" + taskId).style.display = "block";
      };
      tabsContainer.appendChild(tab);
  
      const ct = document.createElement("div");
      ct.className    = "tab-content";
      ct.id           = "content-" + taskId;
      ct.style.display = "none";
      ct.innerHTML    = `
        <section class="task-header">
          <strong>${label.textContent}</strong>
          <span class="status">Статус: <span class="task-status">Ожидание...</span></span>
        </section>
        <section class="main-content">
          <div class="text-column"><h2>Оригинал</h2><textarea class="original-text" readonly>—</textarea></div>
          <div class="text-column"><h2>Редактировано</h2><textarea class="redacted-text">—</textarea></div>
        </section>
        <section class="report"><h2>Отчёт</h2><pre class="report-content">—</pre></section>
      `;
      contentsContainer.appendChild(ct);
    }
  
    // ======== Статусы ========
    function pollStatus(taskId) {
      const iv = setInterval(async () => {
        try {
          const resp = await fetch(`/status/${taskId}`);
          if (!resp.ok) {
            clearInterval(iv);
            document.getElementById("tab-"+taskId)?.remove();
            document.getElementById("content-"+taskId)?.remove();
            savedTaskIds = savedTaskIds.filter(id => id !== taskId);
            persistState();
            return;
          }
          const { status } = await resp.json();
          const stEl = document.querySelector(`#content-${taskId} .task-status`);
          if (stEl) stEl.textContent = status;
          if (status === "completed") {
            clearInterval(iv);
            loadResults(taskId);
          }
        } catch(e) {
          console.error(e);
          clearInterval(iv);
        }
      }, 2000);
    }
  
    // ======== Загружаем обработанные файлы ========
    async function loadResults(taskId) {
      const { reports } = await (await fetch(`/results/${taskId}`)).json();
  
      document.getElementById("tab-"+taskId)?.remove();
      document.getElementById("content-"+taskId)?.remove();
  
      reports.forEach((entry, idx) => {
        const subId = `${taskId}_${idx}`;
        if (!tabNames[subId]) {
          tabNames[subId] = `Задача ${idx+1}`;
        }
        createFileTab(subId, entry.report);
      });
  
      persistState();
  
      const first = `${taskId}_0`;
      document.getElementById("tab-"+first)?.click();
    }
  
    // ======== Вкладки и сделанные файлы ========
    function createFileTab(tabId, report) {
      if (document.getElementById("tab-"+tabId)) return;
  
      const tab = document.createElement("div");
      tab.className = "tab";
      tab.id        = "tab-"+tabId;
  
      const lbl = document.createElement("span");
      lbl.className   = "tab-label";
      lbl.textContent = tabNames[tabId];
      tab.appendChild(lbl);
  
      const cls = document.createElement("span");
      cls.className   = "close";
      cls.textContent = "×";
      cls.onclick     = () => {
        tab.remove();
        document.getElementById("content-"+tabId)?.remove();
        delete tabNames[tabId];
        delete editedTexts[tabId];
        persistState();
      };
      tab.appendChild(cls);
  
      lbl.ondblclick = () => {
        const inp = document.createElement("input");
        inp.type  = "text";
        inp.value = lbl.textContent;
        tab.replaceChild(inp, lbl);
        inp.focus();
        inp.onblur = () => {
          const v = inp.value.trim() || lbl.textContent;
          tabNames[tabId] = v;
          lbl.textContent = v;
          tab.replaceChild(lbl, inp);
          persistState();
        };
      };
  
      tab.onclick = () => {
        document.querySelectorAll(".tab").forEach(t=>t.classList.remove("active"));
        document.querySelectorAll(".tab-content").forEach(c=>c.style.display="none");
        tab.classList.add("active");
        document.getElementById("content-"+tabId).style.display = "block";
      };
      tabsContainer.appendChild(tab);
  
      const ct = document.createElement("div");
      ct.className    = "tab-content";
      ct.id           = "content-"+tabId;
      ct.style.display = "none";
      ct.innerHTML    = `
        <section class="task-header">
          <strong>${lbl.textContent}</strong>
          <span class="status">Статус: <span class="task-status">completed</span></span>
          <label>Формат:</label>
          <select class="download-format">
            <option value="txt">TXT</option>
            <option value="pdf">PDF</option>
            <option value="docx">DOCX</option>
          </select>
          <button class="download-zip">Скачать ZIP</button>
          <button class="download-single">Скачать файл</button>
        </section>
        <section class="main-content">
          <div class="text-column">
            <h2>Оригинал</h2>
            <textarea class="original-text" readonly></textarea>
          </div>
          <div class="text-column">
            <h2>Редактировано</h2>
            <textarea class="redacted-text"></textarea>
          </div>
        </section>
        <section class="report">
          <h2>Отчёт</h2>
          <pre class="report-content"></pre>
        </section>
      `;
      contentsContainer.appendChild(ct);
  
      const pane = ct;
      pane.querySelector(".original-text").value = report.original_text || "";
      const rt = pane.querySelector(".redacted-text");
      rt.value = editedTexts[tabId] ?? report.reduced_text ?? "";
      rt.oninput = e => {
        editedTexts[tabId] = e.target.value;
        persistState();
      };
      const reps = report.replacements || [];
      pane.querySelector(".report-content").textContent = 
        reps.length
          ? reps.map(r=>`${r.entity_type}: ${r.original} → ${r.replacement}`).join("\n")
          : "Нет замен";
  
      pane.querySelector(".download-zip").onclick = () => {
        const batch = tabId.split("_")[0];
        window.location.href = `/download/${batch}`;
      };
  
      pane.querySelector(".download-single").onclick = () => {
        const fmt  = pane.querySelector(".download-format").value;
        const txt  = rt.value;
        const name = lbl.textContent;
        if (fmt === "txt") return downloadBlob(new Blob([txt],{type:"text/plain"}), name+".txt");
        if (fmt === "pdf") {
          const pdf = new window.jspdf.jsPDF();
          pdf.setFont("Courier"); pdf.setFontSize(12);
          pdf.text(pdf.splitTextToSize(txt,180),10,10);
          return downloadBlob(pdf.output("blob"), name+".pdf");
        }
        if (fmt === "docx") {
          const { Document,Packer,Paragraph } = docxLib;
          const doc = new Document({ sections:[{ children:[new Paragraph(txt)] }] });
          return Packer.toBlob(doc).then(b=>downloadBlob(b,name+".docx"));
        }
      };
    }
  
    function downloadBlob(blobOrUrl, filename) {
      const url = typeof blobOrUrl === "string"
        ? blobOrUrl
        : URL.createObjectURL(blobOrUrl);
      const a = document.createElement("a");
      a.href    = url;
      a.download= filename;
      document.body.appendChild(a);
      a.click();
      a.remove();
      if (typeof blobOrUrl !== "string") URL.revokeObjectURL(url);
    }
  });
  