document.addEventListener('DOMContentLoaded', () => {
    const chatForm = document.getElementById('chat-form');
    const userInput = document.getElementById('user-input');
    const chatMessages = document.getElementById('chat-messages');
    const subjectButtons = document.querySelectorAll('.subject-btn');
    const subjectTitle = document.getElementById('current-subject-title');
    const fileUpload = document.getElementById('file-upload');
    const uploadStatus = document.getElementById('upload-status');
    const audioToggle = document.getElementById('audio-toggle');

    // Syllabus Filter UI Elements
    const syllabusFilters = document.getElementById('syllabus-filters');
    const filterCurso = document.getElementById('filter-curso');
    const filterBloque = document.getElementById('filter-bloque');
    const filterContenido = document.getElementById('filter-contenido');
    const btnEstudiar = document.getElementById('btn-estudiar');
    let temarioDataLengua = [];
    let temarioDataMatematicas = [];
    let temarioDataValenciano = [];
    let temarioDataIngles = [];
    let temarioDataCompetenciaLectora = [];
    let currentTemarioData = [];

    // Store chat history HTML per subject
    const chatHistoriesHTML = {};

    // Fetch Syllabus Data
    async function loadTemario(subject, endpoint) {
        try {
            const resp = await fetch(endpoint);
            if (resp.ok) {
                const data = await resp.json();
                if (subject === 'lengua') {
                    temarioDataLengua = data.temario || [];
                } else if (subject === 'matematicas') {
                    temarioDataMatematicas = data.temario || [];
                    // If math is default on load
                    if (currentSubject === 'matematicas') {
                        currentTemarioData = temarioDataMatematicas;
                        syllabusFilters.style.display = 'block';
                        populateCursos();
                    }
                } else if (subject === 'valenciano') {
                    temarioDataValenciano = data.temario || [];
                } else if (subject === 'ingles') {
                    temarioDataIngles = data.temario || [];
                } else if (subject === 'competencia_lectora') {
                    temarioDataCompetenciaLectora = data.temario || [];
                }
            }
        } catch (e) {
            console.error(`Error loading temario for ${subject}:`, e);
        }
    }
    loadTemario('lengua', '/api/temario/lengua');
    loadTemario('matematicas', '/api/temario/matematicas');
    loadTemario('valenciano', '/api/temario/valenciano');
    loadTemario('ingles', '/api/temario/ingles');
    loadTemario('competencia_lectora', '/api/temario/competencia_lectora');

    let audioEnabled = false;

    // Modern Outline SVG Icons
    const muteIcon = `<svg viewBox="0 0 24 24" width="24" height="24" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"><polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"></polygon><line x1="23" y1="9" x2="17" y2="15"></line><line x1="17" y1="9" x2="23" y2="15"></line></svg>`;
    const soundIcon = `<svg viewBox="0 0 24 24" width="24" height="24" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"><polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"></polygon><path d="M19.07 4.93a10 10 0 0 1 0 14.14M15.54 8.46a5 5 0 0 1 0 7.07"></path></svg>`;

    // Initial load
    audioToggle.innerHTML = muteIcon;

    // Toggle Audio
    audioToggle.addEventListener('click', () => {
        audioEnabled = !audioEnabled;
        if (audioEnabled) {
            audioToggle.innerHTML = soundIcon;
            audioToggle.title = "Desactivar Narración por Voz";
            audioToggle.classList.remove('muted');
            // Try playing a silent utterance to unlock audio context on iOS/Safari
            try {
                const unlock = new SpeechSynthesisUtterance('');
                window.speechSynthesis.speak(unlock);
            } catch (e) { }
        } else {
            audioToggle.innerHTML = muteIcon;
            audioToggle.title = "Activar Narración por Voz";
            audioToggle.classList.add('muted');
            if (window.speechSynthesis) window.speechSynthesis.cancel();
        }
    });

    // Subject theme colors
    const themes = {
        'matematicas': { title: 'Pizarra Digital - Matemáticas', color: 'var(--color-blue)', name: 'Mates' },
        'lengua': { title: 'Pizarra Digital - Lengua', color: 'var(--color-green)', name: 'Lengua' },
        'valenciano': { title: 'Pizarra Digital - Valencià', color: 'var(--color-orange)', name: 'Valencià' },
        'ingles': { title: 'Pizarra Digital - Inglés', color: 'var(--color-yellow)', name: 'Inglés' },
        'competencia_lectora': { title: 'Pizarra Digital - Lectura', color: 'var(--color-purple)', name: 'Lectura' }
    };

    let currentSubject = 'matematicas';

    // Handle Subject switching
    subjectButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            if (currentSubject === btn.dataset.subject) return;

            subjectButtons.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');

            const nextSubject = btn.dataset.subject;

            // Save current subject's chat history
            chatHistoriesHTML[currentSubject] = chatMessages.innerHTML;

            // Switch subject
            currentSubject = nextSubject;

            // Update UI
            subjectTitle.textContent = themes[currentSubject].title;
            subjectTitle.style.color = themes[currentSubject].color;

            // Toggle Syllabus Filters visibility
            if (currentSubject === 'lengua') {
                syllabusFilters.style.display = 'block';
                currentTemarioData = temarioDataLengua;
                if (currentTemarioData.length > 0) populateCursos();
            } else if (currentSubject === 'matematicas') {
                syllabusFilters.style.display = 'block';
                currentTemarioData = temarioDataMatematicas;
                if (currentTemarioData.length > 0) populateCursos();
            } else if (currentSubject === 'valenciano') {
                syllabusFilters.style.display = 'block';
                currentTemarioData = temarioDataValenciano;
                if (currentTemarioData.length > 0) populateCursos();
            } else if (currentSubject === 'ingles') {
                syllabusFilters.style.display = 'block';
                currentTemarioData = temarioDataIngles;
                if (currentTemarioData.length > 0) populateCursos();
            } else if (currentSubject === 'competencia_lectora') {
                syllabusFilters.style.display = 'block';
                currentTemarioData = temarioDataCompetenciaLectora;
                if (currentTemarioData.length > 0) populateCursos();
            } else {
                syllabusFilters.style.display = 'none';
                currentTemarioData = [];
            }

            // Restore or initialize chat history for the new subject
            if (chatHistoriesHTML[currentSubject]) {
                chatMessages.innerHTML = chatHistoriesHTML[currentSubject];
            } else {
                const welcomeText = (currentSubject === 'valenciano')
                    ? "Hola! Què repassem hui? 😊"
                    : "¡Hola! ¿Qué repasamos hoy? 😊";

                chatMessages.innerHTML = `
                    <div class="message assistant">
                        <div class="bubble" id="welcome-message">
                            ${welcomeText}
                        </div>
                    </div>`;
            }

            // Update Input Placeholder
            if (currentSubject === 'valenciano') {
                userInput.placeholder = "Pregunta el que vulgues...";
            } else {
                userInput.placeholder = "Pregunta lo que quieras...";
            }

            // Scroll to bottom
            chatMessages.scrollTop = chatMessages.scrollHeight;
        });
    });

    // --- SYLLABUS FILTERS LOGIC ---
    function populateCursos() {
        filterCurso.innerHTML = '<option value="">Selecciona Curso...</option>';
        currentTemarioData.forEach((cursoObj, index) => {
            const opt = document.createElement('option');
            opt.value = index;
            opt.textContent = cursoObj.curso;
            filterCurso.appendChild(opt);
        });
        filterBloque.innerHTML = '<option value="">Selecciona Bloque...</option>';
        filterBloque.disabled = true;
        filterContenido.innerHTML = '<option value="">Selecciona Contenido...</option>';
        filterContenido.disabled = true;
        btnEstudiar.disabled = true;
    }

    filterCurso.addEventListener('change', (e) => {
        const cursoIdx = e.target.value;
        filterBloque.innerHTML = '<option value="">Selecciona Bloque...</option>';
        filterContenido.innerHTML = '<option value="">Selecciona Contenido...</option>';
        filterContenido.disabled = true;
        btnEstudiar.disabled = true;

        if (cursoIdx === "") {
            filterBloque.disabled = true;
            return;
        }

        const cursoObj = currentTemarioData[cursoIdx];
        if (cursoObj && cursoObj.bloques) {
            Object.keys(cursoObj.bloques).forEach(bloqueName => {
                const opt = document.createElement('option');
                opt.value = bloqueName;
                // Capitalize first letter, handle valencian translation
                let displayText = bloqueName.charAt(0).toUpperCase() + bloqueName.slice(1);
                if (currentSubject === 'valenciano' && bloqueName === 'gramatica') {
                    displayText = 'Gramàtica';
                }
                opt.textContent = displayText;
                filterBloque.appendChild(opt);
            });
            filterBloque.disabled = false;
        }
    });

    filterBloque.addEventListener('change', (e) => {
        const cursoIdx = filterCurso.value;
        const bloqueName = e.target.value;
        filterContenido.innerHTML = '<option value="">Selecciona Contenido...</option>';
        btnEstudiar.disabled = true;

        if (bloqueName === "") {
            filterContenido.disabled = true;
            return;
        }

        const cursoObj = currentTemarioData[cursoIdx];
        if (cursoObj && cursoObj.bloques && cursoObj.bloques[bloqueName]) {
            const contenidos = cursoObj.bloques[bloqueName];
            contenidos.forEach((contenido, idx) => {
                const opt = document.createElement('option');
                opt.value = idx;
                opt.textContent = contenido;
                filterContenido.appendChild(opt);
            });
            filterContenido.disabled = false;
        }
    });

    filterContenido.addEventListener('change', (e) => {
        btnEstudiar.disabled = (e.target.value === "");
    });

    btnEstudiar.addEventListener('click', async () => {
        const cursoIdx = filterCurso.value;
        const bloqueName = filterBloque.value;
        const contenidoIdx = filterContenido.value;

        if (cursoIdx === "" || bloqueName === "" || contenidoIdx === "") return;

        const cursoStr = currentTemarioData[cursoIdx].curso;
        let bloqueStr = bloqueName.charAt(0).toUpperCase() + bloqueName.slice(1);
        if (currentSubject === 'valenciano' && bloqueName === 'gramatica') {
            bloqueStr = 'Gramàtica';
        }
        const contenidoStr = currentTemarioData[cursoIdx].bloques[bloqueName][contenidoIdx];

        // Format the message just like if the user typed it
        const generatedMessage = (currentSubject === 'valenciano')
            ? `Vull repassar ${bloqueStr}: ${contenidoStr}`
            : `Quiero repasar ${bloqueStr}: ${contenidoStr}`;

        // Add to UI visibly
        addMessage(generatedMessage, 'user');

        // Reset dropdowns for next time (optional, maybe keep them selected)
        // filterCurso.value = "";
        // filterBloque.value = "";
        // filterContenido.value = "";
        // filterBloque.disabled = true; filterContenido.disabled = true; btnEstudiar.disabled = true;

        // Instead of calling the AI, we fetch a deterministic question from our new DB Question Bank
        await fetchNextDBQuestion(generatedMessage);
    });

    // Helper to send message to backend
    async function sendMessageToBackend(messageText, isHidden = false, resetHistory = false) {
        // Show loading indicator
        const loadingId = addLoadingIndicator();

        try {
            // Include context in the prompt temporarily since we don't have true RAG yet
            const prefixedMessage = `[Contexto: asignatura actual es ${themes[currentSubject].name}] ${messageText}`;

            const formData = new URLSearchParams();
            formData.append('message', prefixedMessage);
            formData.append('subject', currentSubject);

            if (resetHistory) {
                formData.append('reset_history', 'true');
            }

            let courseLevel = "";
            if ((currentSubject === 'lengua' || currentSubject === 'matematicas' || currentSubject === 'valenciano' || currentSubject === 'ingles') && filterCurso.value !== "") {
                courseLevel = currentTemarioData[filterCurso.value].curso;
            }
            formData.append('course_level', courseLevel);

            const response = await fetch('/chat', {
                method: 'POST',
                body: formData,
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded'
                }
            });

            const data = await response.json();

            // Remove loading
            removeMessage(loadingId);

            if (data.error) {
                const errorMsg = (currentSubject === 'valenciano')
                    ? `Ui, hi ha hagut un xicotet error: ${data.error}`
                    : `Oops, un pequeño error falló: ${data.error}`;
                addMessage(errorMsg, 'assistant');
            } else {
                // Play audio for the entire response once
                playAudioForResponse(data.response);

                // Clean the response slightly to remove standalone [CORRECTO] blocks 
                // so they don't form empty bubbles or mess up splitting
                let cleanResponse = data.response;

                // We want to extract [CORRECTO]/[INCORRECTO] to handle UI state, 
                // but we can do that inside addMessage. To prevent them from creating 
                // empty bubbles, we'll let addMessage handle it, but we'll add a check 
                // in addMessage to abort rendering if the resulting text is empty.

                // Stop buttons from separating from the question text
                cleanResponse = cleanResponse.replace(/\n\n+(?=\s*\[BOTON:)/gi, '\n');

                // Split AI response by double newlines into blocks to render as separate bubbles
                const blocks = cleanResponse.split('\n\n').filter(b => b.trim() !== '');

                blocks.forEach(block => {
                    const parsedResponse = marked.parse(block);
                    addMessage(parsedResponse, 'assistant', true, false, true);
                });
            }
        } catch (error) {
            removeMessage(loadingId);
            const connError = (currentSubject === 'valenciano')
                ? "Alguna cosa ha anat malament amb la connexió. Pots tornar a enviar-ho?"
                : "Algo fue mal con la conexión. ¿Puedes enviarlo de nuevo?";
            addMessage(connError, 'assistant');
        }
    }

    chatForm.addEventListener('submit', async (e) => {
        e.preventDefault();

        const message = userInput.value.trim();
        if (!message) return;

        // Add User Message (visible)
        addMessage(message, 'user');

        // Clear input
        userInput.value = '';

        // Hit the backend
        await sendMessageToBackend(message, false);
    });

    function addMessage(text, sender, isHTML = false, isHidden = false, preventAudio = false) {
        if (isHidden) return; // Do not render anything if it's a hidden message

        const msgEl = document.createElement('div');
        const messageId = 'msg-' + Date.now();
        msgEl.id = messageId;
        msgEl.className = `message ${sender}`;

        const contentEl = document.createElement('div');
        contentEl.className = 'bubble'; // Changed from 'message-content' to 'bubble' to match existing CSS

        // Parse custom interactive buttons: [BOTON: text]
        let formattedText = text;

        // Intercept [CORRECTO] and [INCORRECTO] tags for animations and button states
        // Adding English variations because Gemini sometimes translates the tag
        const correctoRegex = /\[CORRECTO\]|\[CORRECT\]/gi;
        const incorrectoRegex = /\[INCORRECTO\]|\[INCORRECT\]/gi;

        let foundStatus = null; // Can be 'correct' or 'incorrect'

        if (formattedText.match(correctoRegex)) {
            formattedText = formattedText.replace(correctoRegex, '').trim();
            // Wait slightly so the message renders first
            setTimeout(playSuccessAnimation, 0);
            foundStatus = 'correct';
        } else if (formattedText.match(incorrectoRegex)) {
            formattedText = formattedText.replace(incorrectoRegex, '').trim();
            foundStatus = 'incorrect';
        }

        // Intercept [DB_ID: X] tag to set currentDBQuestion state
        const dbIdRegex = /\[DB_ID:\s*(\d+)\]/i;
        const dbIdMatch = formattedText.match(dbIdRegex);
        if (dbIdMatch) {
            const qid = dbIdMatch[1];
            // We set the state so the next button click knows to use the DB checker
            // Note: We don't have the options yet, but sendDBAnswer only really needs the ID and the text of the clicked button
            window.currentDBQuestion = { id: qid };
            formattedText = formattedText.replace(dbIdRegex, '').trim();
        }

        // If there is a pending button, resolve its state visually
        if (sender === 'assistant' && window.lastClickedInteractiveButton) {
            if (foundStatus === 'correct') {
                window.lastClickedInteractiveButton.classList.remove('loading');
                window.lastClickedInteractiveButton.classList.add('correct');
            } else if (foundStatus === 'incorrect') {
                window.lastClickedInteractiveButton.classList.remove('loading');
                window.lastClickedInteractiveButton.classList.add('incorrect');
            } else {
                // Fallback, if bot didn't include the tag but responded, just clear loading
                window.lastClickedInteractiveButton.classList.remove('loading');
            }
            // Clear the reference since we've handled it
            window.lastClickedInteractiveButton = null;
        }

        // Parse custom interactive buttons: [BOTON: text]
        let interactiveButtonsHtml = '';

        if (formattedText.includes('[BOTON:')) {
            // Extract all button matches
            const buttonRegex = /\[BOTON:\s*([^\]]+)\]/g;
            let match;
            const buttons = [];

            while ((match = buttonRegex.exec(formattedText)) !== null) {
                buttons.push(match[1].trim());
            }

            // Remove the raw syntax from the message text
            formattedText = formattedText.replace(buttonRegex, '').trim();

            // Generate HTML for the interactive buttons container
            if (buttons.length > 0) {
                // Safeguard: Disable all PREVIOUS interactive buttons in the chat to avoid duplication and clutter
                // This ensures the student only interacts with the most recent question
                document.querySelectorAll('.interactive-btn').forEach(btn => {
                    btn.disabled = true;
                    btn.style.opacity = '0.6';
                    btn.style.pointerEvents = 'none';
                });

                interactiveButtonsHtml = '<div class="interactive-options">';
                buttons.forEach(btnText => {
                    // Escape quotes just in case
                    const safeText = btnText.replace(/"/g, '&quot;');
                    interactiveButtonsHtml += `<button class="interactive-btn" onclick="window.sendInteractiveAnswer('${safeText}', this)">${btnText}</button>`;
                });
                interactiveButtonsHtml += '</div>';
            }
        }

        // Always convert markdown-like bold text **text** to HTML just in case marked missed it
        formattedText = formattedText.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');

        // Only run these manual replacements if it wasn't already processed by Marked
        if (!isHTML) {
            // Convert newlines to <br>
            formattedText = formattedText.replace(/\n/g, '<br>');
        }

        // Remove edge `<br>` tags that might be left over from removals
        formattedText = formattedText.replace(/^(<br>\s*)+|(<br>\s*)+$/g, '').trim();

        // Check if the resulting bubble would be completely empty visually
        // Remove HTML tags temporarily to check if there is actual text
        const tempCheck = document.createElement('div');
        tempCheck.innerHTML = formattedText;
        const textContent = tempCheck.textContent || tempCheck.innerText || '';

        // If no text AND no interactive buttons, abort rendering this bubble
        if (textContent.trim() === '' && interactiveButtonsHtml === '') {
            return;
        }

        contentEl.innerHTML = formattedText + interactiveButtonsHtml;
        msgEl.appendChild(contentEl);
        chatMessages.appendChild(msgEl);

        // Scroll to bottom
        chatMessages.scrollTop = chatMessages.scrollHeight;

        // Speak the message if audio is enabled and it's from the assistant
        if (sender === 'assistant' && !isHidden && !preventAudio) {
            // The incoming text is already parsed as HTML by marked.js, so we first strip all HTML tags
            let tempDiv = document.createElement("div");
            tempDiv.innerHTML = text;
            let cleanText = tempDiv.textContent || tempDiv.innerText || "";

            // Now clean out the proprietary bracket syntax that remains in the plain text
            cleanText = cleanText.replace(/\[BOTON:.*?\]/gi, ''); // Remove button tags
            cleanText = cleanText.replace(/\[CORRECTO\]/gi, ''); // Remove grading tags
            cleanText = cleanText.replace(/\[INCORRECTO\]/gi, '');
            cleanText = cleanText.replace(/\[CORRECT\]/gi, '');
            cleanText = cleanText.replace(/\[INCORRECT\]/gi, '');
            speakText(cleanText.trim());
        }
    }

    // Process the full response text for audio before splitting it into visual bubbles
    function playAudioForResponse(rawText) {
        if (!audioEnabled || !window.speechSynthesis) return;
        let tempDiv = document.createElement("div");
        // Parse markdown to HTML first, so characters like ** doesn't get spoken
        tempDiv.innerHTML = marked.parse(rawText);
        let cleanText = tempDiv.textContent || tempDiv.innerText || "";
        cleanText = cleanText.replace(/\[BOTON:.*?\]/gi, '');
        cleanText = cleanText.replace(/\[CORRECTO\]/gi, '');
        cleanText = cleanText.replace(/\[INCORRECTO\]/gi, '');
        cleanText = cleanText.replace(/\[CORRECT\]/gi, '');
        cleanText = cleanText.replace(/\[INCORRECT\]/gi, '');
        speakText(cleanText.trim());
    }

    // Speak helper using Web Speech API
    function speakText(text) {
        if (!audioEnabled || !window.speechSynthesis) return;

        window.speechSynthesis.cancel(); // Stop whatever is currently playing

        if (!text) return;

        const utterance = new SpeechSynthesisUtterance(text);

        // Select language based on subject
        if (currentSubject === 'ingles') {
            utterance.lang = 'en-GB';
        } else if (currentSubject === 'valenciano') {
            utterance.lang = 'ca-ES'; // Catalan/Valencian usually works
        } else {
            utterance.lang = 'es-ES';
        }

        // Try to pick a natural voice
        const voices = window.speechSynthesis.getVoices();
        // Find a male voice from all voices first (prioritizing the requested ones)
        const maleNames = ["Diego", "Jorge", "Jordi", "Daniel", "Arthur", "Pablo"];
        const boyVoice = voices.find(v => maleNames.some(name => v.name.includes(name)));

        if (boyVoice) {
            utterance.voice = boyVoice;
            // Also override the lang if we picked a specific voice to match its internal lang
            utterance.lang = boyVoice.lang;
        } else {
            // Fallback: filter by language prefix and pick the best available
            const targetVoices = voices.filter(v => v.lang.startsWith(utterance.lang.substring(0, 2)));
            if (targetVoices.length > 0) {
                utterance.voice = targetVoices[0];
                const premium = targetVoices.find(v =>
                    (v.name.includes("Premium") || v.name.includes("Enhanced") || v.name.includes("Google")) &&
                    !v.name.includes("Monica") && !v.name.includes("Victoria") && !v.name.includes("Paulina")
                );
                if (premium) utterance.voice = premium;
            }
        }

        utterance.rate = 1.0;
        utterance.pitch = 1.1; // Slightly higher pitch for a friendlier/teacher tone

        window.speechSynthesis.speak(utterance);
    }

    function addLoadingIndicator() {
        const id = 'loading-' + Date.now();
        const msgDiv = document.createElement('div');
        msgDiv.className = 'message assistant';
        msgDiv.id = id;

        msgDiv.innerHTML = `
            <div class="bubble typing-indicator">
                <div class="dot"></div>
                <div class="dot"></div>
                <div class="dot"></div>
            </div>
        `;

        chatMessages.appendChild(msgDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;

        return id;
    }

    function removeMessage(id) {
        const el = document.getElementById(id);
        if (el) el.remove();
    }

    // Track the current DB question (if any)
    window.currentDBQuestion = null; // { id, question, options }

    // Global function to handle clicks on interactive buttons
    window.sendInteractiveAnswer = function (answer, btnElement) {
        // Find the container parent and disable all buttons inside it
        const container = btnElement.parentElement;
        const allButtons = container.querySelectorAll('.interactive-btn');
        allButtons.forEach(btn => {
            btn.disabled = true;
            if (btn !== btnElement) {
                btn.style.opacity = '0.5';
            }
        });

        // Highlight the selected one as loading
        btnElement.classList.add('loading');
        window.lastClickedInteractiveButton = btnElement;

        // Route to DB checker or AI depending on question source
        if (window.currentDBQuestion && window.currentDBQuestion.id) {
            // ── Server-side evaluation (instant, 100% reliable) ──
            window.sendDBAnswer(answer, btnElement);
        } else {
            // ── AI evaluation (legacy path) ──
            if (window.doHiddenSend) {
                // We add a prefix to help the AI understand this is a button click, 
                // preventing it from thinking it's a new command or a page number.
                window.doHiddenSend(`[OPCION_ELEGIDA]: ${answer}`);
            }
        }
    };

    // Server-side evaluation for DB questions — no AI involved in grading
    window.sendDBAnswer = async function (answer, btnElement) {
        const qid = window.currentDBQuestion.id;
        try {
            const res = await fetch('/questions/check', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ question_id: qid, selected_option: answer })
            });
            const data = await res.json();

            // Immediately color the button
            btnElement.classList.remove('loading');
            if (data.correct) {
                btnElement.classList.add('correct');
                playSuccessAnimation();

                // Ask AI for a brief congratulatory explanation
                const loadingId = addLoadingIndicator();
                setTimeout(async () => {
                    const formData = new URLSearchParams();
                    formData.append('message', `[CORRECTO] El alumno eligió "${answer}" correctamente en esta pregunta: "${window.currentDBQuestion.question}". Felicítale brevemente (máximo 1 frase) y avanza.`);
                    formData.append('subject', currentSubject);
                    formData.append('course_level', filterCurso.value ? currentTemarioData[filterCurso.value].curso : '');
                    const chatRes = await fetch('/chat', { method: 'POST', body: formData, headers: { 'Content-Type': 'application/x-www-form-urlencoded' } });
                    const chatData = await chatRes.json();
                    removeMessage(loadingId);
                    if (chatData.response) {
                        let txt = chatData.response.replace(/\[CORRECTO\]/gi, '').replace(/\[INCORRECTO\]/gi, '').trim();
                        // No stripping buttons anymore
                        txt = txt.replace(/\n\n+(?=\s*\[BOTON:)/gi, '\n');
                        txt.split('\n\n').filter(b => b.trim()).forEach(block => {
                            addMessage(marked.parse(block), 'assistant', true, false, true);
                        });
                    }
                    // Clear DB question and fetch next
                    window.currentDBQuestion = null;
                    fetchNextDBQuestion();
                }, 300);

            } else {
                btnElement.classList.add('incorrect');

                // Re-enable all buttons in this question so user can try again
                const container = btnElement.parentElement;
                container.querySelectorAll('.interactive-btn').forEach(btn => {
                    btn.disabled = false;
                    btn.style.opacity = '1';
                });
                window.lastClickedInteractiveButton = null;

                // Ask AI for a hint
                const loadingId = addLoadingIndicator();
                setTimeout(async () => {
                    const formData = new URLSearchParams();
                    formData.append('message', `[INCORRECTO] El alumno eligió "${answer}" pero la respuesta correcta es "${data.answer}" en la pregunta: "${window.currentDBQuestion.question}". Da una pista breve y anímale a intentarlo de nuevo.`);
                    formData.append('subject', currentSubject);
                    formData.append('course_level', filterCurso.value ? currentTemarioData[filterCurso.value].curso : '');
                    const chatRes = await fetch('/chat', { method: 'POST', body: formData, headers: { 'Content-Type': 'application/x-www-form-urlencoded' } });
                    const chatData = await chatRes.json();
                    removeMessage(loadingId);
                    if (chatData.response) {
                        let txt = chatData.response.replace(/\[CORRECTO\]/gi, '').replace(/\[INCORRECTO\]/gi, '').trim();
                        // No stripping buttons anymore
                        txt.split('\n\n').filter(b => b.trim()).forEach(block => {
                            addMessage(marked.parse(block), 'assistant', true, false, true);
                        });
                    }
                }, 300);
            }
        } catch (err) {
            console.error('DB check error:', err);
            btnElement.classList.remove('loading');
            window.lastClickedInteractiveButton = null;
        }
    };

    // Fetch the next question from the DB and render it in the chat
    async function fetchNextDBQuestion(fallbackMessage = "") {

        if (!currentSubject) return;
        const params = new URLSearchParams({ subject: currentSubject });
        if (filterCurso.value && currentTemarioData[filterCurso.value]) {
            params.append('grade', currentTemarioData[filterCurso.value].curso.replace(/[^0-9]/g, '') || '');
        }
        if (filterBloque.value) params.append('bloque', filterBloque.value);
        if (filterContenido.value) params.append('contenido', filterContenido.value);

        try {
            const res = await fetch(`/questions/random?${params}`);
            if (!res.ok) {
                if (fallbackMessage) await sendMessageToBackend(fallbackMessage, false, true);
                return;
            }
            const q = await res.json();
            if (q.error) {
                if (fallbackMessage) await sendMessageToBackend(fallbackMessage, false, true);
                return;
            }

            window.currentDBQuestion = q;

            let html = `${q.question}\n\n`;
            q.options.forEach(opt => { html += `[BOTON: ${opt}]\n`; });
            addMessage(marked.parse(html), 'assistant', true, false, true);
        } catch (e) {
            console.log('fetchNextDBQuestion error (falling back to AI):', e);
            if (fallbackMessage) await sendMessageToBackend(fallbackMessage, false, true);
        }
    }

    // Expose fetchNextDBQuestion globally for the "Estudiar" button
    window.fetchNextDBQuestion = fetchNextDBQuestion;


    // Expose the internal send function globally so the buttons can hit the API silently
    window.doHiddenSend = function (answer) {
        // Find the sendMessageToBackend function in the current scope
        // We'll dispatch a custom event that chat.js listens to
        document.dispatchEvent(new CustomEvent('sendHiddenMessage', { detail: { text: answer } }));
    };

    document.addEventListener('sendHiddenMessage', (e) => {
        const messageText = e.detail.text;
        // The addMessage step is skipped for hidden messages. Just show loading and fetch

        // Show loading indicator
        const loadingId = addLoadingIndicator();

        // Let's copy the backend logic here to avoid scope issues inside the event listener
        const prefixedMessage = `[Contexto: asignatura actual es ${themes[currentSubject].name}] ${messageText}`;
        const formData = new URLSearchParams();
        formData.append('message', prefixedMessage);
        formData.append('subject', currentSubject);

        let courseLevel = "";
        if ((currentSubject === 'lengua' || currentSubject === 'matematicas' || currentSubject === 'valenciano' || currentSubject === 'ingles') && filterCurso.value !== "") {
            courseLevel = currentTemarioData[filterCurso.value].curso;
        }
        formData.append('course_level', courseLevel);

        fetch('/chat', {
            method: 'POST',
            body: formData,
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded'
            }
        })
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    removeMessage(loadingId);
                    const errorMsg = (currentSubject === 'valenciano')
                        ? `Ui, hi ha hagut un error: ${data.error}`
                        : `Oops, un error falló: ${data.error}`;
                    addMessage(errorMsg, 'assistant');
                } else {
                    let cleanResponse = data.response;

                    // Evaluate correctness immediately to update the clicked button
                    let isCorrect = false;
                    let isIncorrect = false;
                    if (cleanResponse.match(/\[CORRECTO\]|\[CORRECT\]/i)) {
                        isCorrect = true;
                    } else if (cleanResponse.match(/\[INCORRECTO\]|\[INCORRECT\]/i)) {
                        isIncorrect = true;
                    }

                    if (window.lastClickedInteractiveButton) {
                        window.lastClickedInteractiveButton.classList.remove('loading');
                        if (isCorrect) {
                            window.lastClickedInteractiveButton.classList.add('correct');
                            setTimeout(playSuccessAnimation, 0);
                        } else if (isIncorrect) {
                            window.lastClickedInteractiveButton.classList.add('incorrect');
                            // Re-enable all buttons in the same container so user can try again
                            const container = window.lastClickedInteractiveButton.parentElement;
                            container.querySelectorAll('.interactive-btn').forEach(btn => {
                                btn.disabled = false;
                                btn.style.opacity = '1';
                            });
                        }
                        window.lastClickedInteractiveButton = null;
                    }

                    // Strip tags so addMessage doesn't process them again
                    cleanResponse = cleanResponse.replace(/\[CORRECTO\]/gi, '').trim();
                    cleanResponse = cleanResponse.replace(/\[CORRECT\]/gi, '').trim();
                    cleanResponse = cleanResponse.replace(/\[INCORRECTO\]/gi, '').trim();
                    cleanResponse = cleanResponse.replace(/\[INCORRECT\]/gi, '').trim();

                    // No stripping buttons anymore, we allow duplication but handle it in addMessage

                    // Stop buttons from separating from the question text
                    cleanResponse = cleanResponse.replace(/\n\n+(?=\s*\[BOTON:)/gi, '\n');

                    const blocks = cleanResponse.split('\n\n').filter(b => b.trim() !== '');

                    // Wait 300ms so the user can process the UI feedback (red/green) and star animation before text arrives
                    setTimeout(() => {
                        removeMessage(loadingId);
                        playAudioForResponse(cleanResponse);

                        // Add elements immediately without stagger
                        blocks.forEach((block, index) => {
                            setTimeout(() => {
                                const parsedResponse = marked.parse(block);
                                addMessage(parsedResponse, 'assistant', true, false, true);
                            }, 0);
                        });
                    }, 300);
                }
            })
            .catch(error => {
                removeMessage(loadingId);
                const connError = (currentSubject === 'valenciano')
                    ? "Alguna cosa ha anat malament amb la connexió."
                    : "Algo fue mal con la conexión.";
                addMessage(connError, 'assistant');
            });
    });

    // Function to play the magical star animation
    function playSuccessAnimation() {
        const star = document.createElement('div');
        star.className = 'success-star';
        // Use an SVG to allow for perfectly soft, rounded corners while keeping it solid yellow
        star.innerHTML = `<svg viewBox="0 0 24 24" width="100" height="100" fill="#FFD700" stroke="#F59E0B" stroke-width="2.5" stroke-linejoin="round" stroke-linecap="round"><path d="M12 17.27L18.18 21l-1.64-7.03L22 9.24l-7.19-.61L12 2 9.19 8.63 2 9.24l5.46 4.73L5.82 21z"/></svg>`;
        document.body.appendChild(star);

        // Play success sound
        const audio = new Audio('/static/audio/acierto.mp3');
        audio.play().catch(e => console.log('Audio autoplay prevented:', e));

        // Remove from DOM after animation completes (1.65 seconds)
        setTimeout(() => {
            star.remove();
        }, 1650);
    }
});
