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
    const groupBloque = document.getElementById('group-bloque');
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

                        // ── Default selection: 1º Primaria > Probabilidad > Lenguaje de azar ──
                        const defaultCurso    = '1º de primaria';
                        const defaultBloque   = 'probabilidad';
                        const defaultContenido = 'lenguaje de azar: nunca, a veces, siempre';

                        const cursoIdx = currentTemarioData.findIndex(c =>
                            c.curso.toLowerCase() === defaultCurso.toLowerCase());
                        if (cursoIdx !== -1) {
                            filterCurso.value = cursoIdx;
                            filterCurso.dispatchEvent(new Event('change'));

                            // Wait a tick for bloque options to render
                            setTimeout(() => {
                                // Select bloque
                                const bloqueOpt = [...filterBloque.options].find(o =>
                                    o.value.toLowerCase() === defaultBloque.toLowerCase());
                                if (bloqueOpt) {
                                    filterBloque.value = bloqueOpt.value;
                                    filterBloque.dispatchEvent(new Event('change'));

                                    setTimeout(() => {
                                        // Select contenido
                                        const contenidoOpt = [...filterContenido.options].find(o =>
                                            o.text.toLowerCase() === defaultContenido.toLowerCase());
                                        if (contenidoOpt) {
                                            filterContenido.value = contenidoOpt.value;
                                            filterContenido.dispatchEvent(new Event('change'));
                                        }
                                    }, 50);
                                }
                            }, 50);
                        }
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
    console.log("Cargando temarios...");
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
        'competencia_lectora': { title: 'Pizarra Digital - Lectura', color: 'var(--color-red)', name: 'Lectura' }
    };

    let currentSubject = 'matematicas';
    let currentExerciseIndex = 0;
    let totalExercisesInSeries = 3;
    let userStars = parseInt(localStorage.getItem('aula_stars') || '0');

    // Session state: persist the active topic labels across all turns
    let activeSessionCurso = "";
    let activeSessionBloque = "";
    let activeSessionContenido = "";

    // UI Elements for gamification
    const progressBar = document.getElementById('series-progress');
    const starsCountLabel = document.getElementById('stars-count');

    // Initialize stars
    starsCountLabel.textContent = userStars;

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
            if (currentSubject === 'lengua' || currentSubject === 'matematicas' || currentSubject === 'valenciano' || currentSubject === 'ingles' || currentSubject === 'competencia_lectora') {
                syllabusFilters.style.display = 'block';
                // Always reset block group to visible when switching subject
                if (groupBloque) groupBloque.style.display = 'block';

                if (currentSubject === 'lengua') {
                    currentTemarioData = temarioDataLengua;
                } else if (currentSubject === 'matematicas') {
                    currentTemarioData = temarioDataMatematicas;
                } else if (currentSubject === 'valenciano') {
                    currentTemarioData = temarioDataValenciano;
                } else if (currentSubject === 'ingles') {
                    currentTemarioData = temarioDataIngles;
                } else if (currentSubject === 'competencia_lectora') {
                    currentTemarioData = temarioDataCompetenciaLectora;
                }

                if (currentTemarioData.length > 0) populateCursos();
            } else {
                syllabusFilters.style.display = 'none';
                currentTemarioData = [];
            }

            // Restore or initialize chat history for the new subject
            if (chatHistoriesHTML[currentSubject]) {
                chatMessages.innerHTML = chatHistoriesHTML[currentSubject];
            } else {
                let welcomeText = "¡Hola! Soy tu chat de aprendizaje. ¿Qué quieres repasar hoy? 😊";
                if (currentSubject === 'valenciano') {
                    welcomeText = "Hola! Què repassem hui? 😊";
                } else if (currentSubject === 'competencia_lectora') {
                    welcomeText = "¡Hola! ¿Qué leemos hoy? 😊";
                }

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
                btnEstudiar.textContent = "Anem a repassar!";
            } else if (currentSubject === 'competencia_lectora') {
                userInput.placeholder = "Pregunta lo que quieras...";
                btnEstudiar.textContent = "¡Vamos a leer!";
            } else if (currentSubject === 'ingles') {
                userInput.placeholder = "Pregunta lo que quieras...";
                btnEstudiar.textContent = "Let's go!";
            } else {
                userInput.placeholder = "Pregunta lo que quieras...";
                btnEstudiar.textContent = "¡Vamos a repasar!";
            }

            // Scroll to bottom
            chatMessages.scrollTop = chatMessages.scrollHeight;
        });
    });

    console.log("Setup inicial completado");

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
            const bloqueNames = Object.keys(cursoObj.bloques);
            bloqueNames.forEach(bloqueName => {
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

            // If there's only 1 block, select it automatically and hide the selector
            if (bloqueNames.length === 1) {
                filterBloque.value = bloqueNames[0];
                if (groupBloque) groupBloque.style.display = 'none';
                // Manually trigger change to populate contents dropdown
                filterBloque.dispatchEvent(new Event('change'));
            } else {
                if (groupBloque) groupBloque.style.display = 'block';
                filterBloque.disabled = false;
            }
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

        // ✅ Save active session labels so every subsequent turn uses them
        activeSessionCurso = cursoStr;
        activeSessionBloque = bloqueStr;
        activeSessionContenido = contenidoStr;
        currentExerciseIndex = 0;
        window._lastQuestionId = 0;

        // Show user message
        let generatedMessage = (currentSubject === 'valenciano')
            ? `Vull repassar: ${contenidoStr}`
            : `Quiero repasar: ${contenidoStr}`;
        if (currentSubject === 'competencia_lectora') {
            generatedMessage = `Quiero leer: ${contenidoStr}`;
        }
        addMessage(generatedMessage, 'user');

        // ── DB-ONLY FLOW (ALL SUBJECTS) ──────────────────────────────────
        // 1. Get initial content (Explanation or Reading) from DB
        const loadingId = addLoadingIndicator();
        try {
            const gradeMatch = cursoStr.match(/\d+/);
            const grade = gradeMatch ? parseInt(gradeMatch[0]) : 0;
            const expParams = new URLSearchParams({ subject: currentSubject, grade, bloque: bloqueStr, contenido: contenidoStr });
            const expResp = await fetch(`/explanations/get?${expParams}`);
            removeMessage(loadingId);
            if (expResp.ok) {
                const expData = await expResp.json();
                if (expData.content) {
                    addMessage(marked.parse(expData.content), 'assistant', true, false, true, expData.visual_url || null, expData.audio_url || null);
                }
            }
        } catch (e) {
            removeMessage(loadingId);
        }

        // 2. Fetch and show first question from DB
        totalExercisesInSeries = (currentSubject === 'competencia_lectora') ? 10 : 3;
        await fetchAndShowQuestion(currentSubject, cursoStr, bloqueStr, contenidoStr, 1);
    });

    const DIF_LABELS = { basica: '🟢 Básico', normal: '🟡 Medio', avanzada: '🔴 Avanzado' };

    // ── Fetch question from DB and render it ─────────────────────────────
    async function fetchAndShowQuestion(subject, curso, bloque, contenido, exerciseNum) {
        // Parse grade from curso string (e.g. "1º Primaria" → 1)
        const gradeMatch = curso.match(/\d+/);
        const grade = gradeMatch ? parseInt(gradeMatch[0]) : 0;

        const params = new URLSearchParams({ subject, grade, bloque, contenido });
        if (window._lastQuestionId) params.append('exclude_id', window._lastQuestionId);

        const loadingId = addLoadingIndicator();
        try {
            const resp = await fetch(`/questions/next?${params}`);
            removeMessage(loadingId);

            if (!resp.ok) {
                const err = await resp.json();
                addMessage(`No hay más ejercicios verificados para este tema.`, 'assistant');
                return;
            }

            const q = await resp.json();
            window._lastQuestionId = q.id;
            window.currentDBQuestion = {
                id: q.id,
                question: q.question,
                answer: q.answer,
                feedback_correct: q.feedback_correct || '',
                feedback_incorrect: q.feedback_incorrect || ''
            };
            window.currentCorrectAnswer = q.answer;
            currentExerciseIndex = exerciseNum;

            // Build exercise bubble — difficulty badge from DB field
            const dif = q.dificultad || '';
            const difLabel = DIF_LABELS[dif] || '';
            let idTag = q.id ? `<span class="exercise-id" title="ID: ${q.id}">#${q.id}</span>` : '';
            let difTag = difLabel ? `<span class="dif-badge dif-${dif}">${difLabel}</span>` : '';
            let html = `<p><strong>Ejercicio ${exerciseNum}/${totalExercisesInSeries}</strong> ${difTag}: ${q.question} ${idTag}</p>`;
            html += '<div class="interactive-options">';
            q.options.forEach(opt => {
                const safe = opt.replace(/"/g, '&quot;');
                html += `<button class="interactive-btn" onclick="window.sendInteractiveAnswer('${safe}', this)">${opt}</button>`;
            });
            html += '</div>';

            // Disable previous buttons
            document.querySelectorAll('.interactive-btn').forEach(btn => {
                btn.disabled = true;
                btn.style.opacity = '0.6';
                btn.style.pointerEvents = 'none';
            });

            addMessage(html, 'assistant', true, false, true, q.visual_url || null, q.audio_url || null);

            // Update progress bar
            if (progressBar) {
                const pct = (exerciseNum / totalExercisesInSeries) * 100;
                progressBar.style.width = `${pct}%`;
            }
        } catch (e) {
            removeMessage(loadingId);
            addMessage('Error al obtener la pregunta. Inténtalo de nuevo.', 'assistant');
        }
    }

    // Helper to send message to backend
    async function sendMessageToBackend(messageText, isHidden = false, resetHistory = false, exerciseNum = 0) {
        // Clear DB state to ensure we always prioritize the AI's natural flow
        window.currentDBQuestion = null;

        // Show loading indicator
        const loadingId = addLoadingIndicator();

        try {
            const prefixedMessage = `[Contexto: asignatura actual es ${themes[currentSubject].name}] ${messageText}`;

            const formData = new URLSearchParams();
            formData.append('message', prefixedMessage);
            formData.append('subject', currentSubject);

            if (resetHistory) {
                formData.append('reset_history', 'true');
            }
            if (exerciseNum > 0) {
                formData.append('exercise_num', exerciseNum);
            }

            let courseLevel = "";
            let bloqueStr = "";
            let contenidoStr = "";

            // Use persisted session labels if available, otherwise fall back to UI dropdowns
            if (activeSessionCurso) {
                courseLevel = activeSessionCurso;
                bloqueStr = activeSessionBloque;
                contenidoStr = activeSessionContenido;
            } else if (filterCurso.value !== "") {
                const cursoIdx = filterCurso.value;
                courseLevel = currentTemarioData[cursoIdx].curso;
                if (filterBloque.value !== "") {
                    bloqueStr = filterBloque.value;
                    if (filterContenido.value !== "") {
                        const contentIdx = filterContenido.value;
                        contenidoStr = currentTemarioData[cursoIdx].bloques[bloqueStr][contentIdx];
                    }
                }
            }

            formData.append('course_level', courseLevel);
            formData.append('bloque', bloqueStr);
            formData.append('contenido', contenidoStr);

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
                let cleanResponse = data.response;

                // Update the clicked button's visual state (green/red)
                if (window.lastClickedInteractiveButton) {
                    const looksCorrect = /\[CORRECTO\]|\[CORRECTE\]|\[CORRECT\]/i.test(cleanResponse);
                    const looksIncorrect = /\[INCORRECTO\]|\[INCORRECTE\]|\[INCORRECT\]/i.test(cleanResponse);
                    window.lastClickedInteractiveButton.classList.remove('loading');
                    if (looksCorrect) {
                        window.lastClickedInteractiveButton.classList.add('correct');
                    } else if (looksIncorrect) {
                        window.lastClickedInteractiveButton.classList.add('incorrect');
                        const container = window.lastClickedInteractiveButton.parentElement;
                        container.querySelectorAll('.interactive-btn').forEach(btn => {
                            btn.disabled = false;
                            btn.style.opacity = '1';
                        });
                    }
                    window.lastClickedInteractiveButton = null;
                }

                // Clean evaluation tags and formatting artifacts
                cleanResponse = cleanResponse.replace(/\[CORRECTO\]|\[CORRECTE\]|\[CORRECT\]/gi, '');
                cleanResponse = cleanResponse.replace(/\[INCORRECTO\]|\[INCORRECTE\]|\[INCORRECT\]/gi, '');
                cleanResponse = cleanResponse.replace(/\n+(?=\s*\[BOTON:)/gi, ' ');
                cleanResponse = cleanResponse.replace(/[¡!]{2,}/g, '!');
                cleanResponse = cleanResponse.replace(/[¿?]{2,}/g, '?');
                cleanResponse = cleanResponse.replace(/([¡!¿?])\s+([¡!¿?])/g, '$1');
                // Strip any '¿Quieres seguir?' the AI adds by itself — JS controls this
                cleanResponse = cleanResponse.replace(/---?\s*[\n]?\s*¿Quieres seguir\?/gi, '').trim();
                cleanResponse = cleanResponse.trim();

                playAudioForResponse(cleanResponse);

                // Split by '---' into separate bubbles
                const segments = cleanResponse.split('---').map(s => s.trim()).filter(s => {
                    if (!s) return false;
                    if (!/[a-z0-9áéíóúÁÉÍÓÚñÑ]/i.test(s) && !s.includes('[BOTON:')) return false;
                    if (s.length < 5 && /^[¡! \.]+$/.test(s)) return false;
                    return true;
                });

                segments.forEach((segment, idx) => {
                    const parsedResponse = marked.parse(segment.trim());
                    const isExerciseSegment = segment.toLowerCase().includes('ejercicio') || segment.includes('[BOTON:');
                    const vUrl = isExerciseSegment ? data.visual_url : null;
                    const aUrl = isExerciseSegment ? data.audio_url : null;
                    addMessage(parsedResponse, 'assistant', true, false, true, vUrl, aUrl);
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

    function addMessage(text, sender, isHTML = false, isHidden = false, preventAudio = false, visualUrl = null, audioUrl = null) {
        if (isHidden) return; // Do not render anything if it's a hidden message

        const msgEl = document.createElement('div');
        const messageId = 'msg-' + Date.now();
        msgEl.id = messageId;
        msgEl.className = `message ${sender}`;

        const contentEl = document.createElement('div');
        contentEl.className = 'bubble';

        // Add Media if present
        let mediaHtml = '';
        if (visualUrl) {
            mediaHtml += `<div class="message-media"><img src="${visualUrl}" alt="Ejercicio visual" class="chat-img" onclick="window.open('${visualUrl}')"></div>`;
        }
        if (audioUrl) {
            mediaHtml += `<div class="message-audio"><audio controls src="${audioUrl}" class="chat-audio"></audio></div>`;
        }

        // Parse custom interactive buttons: [BOTON: text]
        let formattedText = text;
        let foundStatus = null;

        // Detect Exercise Number (e.g. Ejercicio 1/3) for progress bar
        const exerciseRegex = /Ejercicio\s+(\d+)\/(\d+)/i;
        const exerciseMatch = formattedText.match(exerciseRegex);
        if (exerciseMatch) {
            const current = parseInt(exerciseMatch[1]);
            const total = parseInt(exerciseMatch[2]);
            const percent = (current / total) * 100;
            if (progressBar) {
                progressBar.style.width = `${percent}%`;
                progressBar.style.background = percent === 100
                    ? 'linear-gradient(90deg, var(--color-green), #4ade80)'
                    : 'linear-gradient(90deg, var(--color-blue), #60a5fa)';
            }
        }


        // Style Exercise Identifier [ID: PMAT1N0001]
        const exerciseIdRegex = /\[ID:\s*([^\]]+)\]/gi;
        formattedText = formattedText.replace(exerciseIdRegex, '<span class="exercise-id" title="Referencia del ejercicio">$1</span>');


        // Parse custom interactive buttons: [BOTON: text]
        let interactiveButtonsHtml = '';

        if (formattedText.includes('[BOTON:')) {
            // Extract the hidden correct answer key FIRST (before removing it from text)
            const correctAnswerMatch = formattedText.match(/\[RESPUESTA_CORRECTA:\s*([^\]]+)\]/i);
            if (correctAnswerMatch) {
                window.currentCorrectAnswer = correctAnswerMatch[1].trim();
                // Remove the hidden tag from the displayed text
                formattedText = formattedText.replace(/\[RESPUESTA_CORRECTA:[^\]]+\]/gi, '').trim();
            }

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
                document.querySelectorAll('.interactive-btn').forEach(btn => {
                    btn.disabled = true;
                    btn.style.opacity = '0.6';
                    btn.style.pointerEvents = 'none';
                });

                interactiveButtonsHtml = '<div class="interactive-options">';
                buttons.forEach(btnText => {
                    const safeText = btnText.replace(/"/g, '&quot;');
                    interactiveButtonsHtml += `<button class="interactive-btn" onclick="window.sendInteractiveAnswer('${safeText}', this)">${btnText}</button>`;
                });
                interactiveButtonsHtml += '</div>';
            }
        }

        // Always convert markdown-like bold text **text** to HTML just in case marked missed it
        formattedText = formattedText.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');

        // No longer using stylized labels for Explicación to reduce repetition

        // Convert any "quoted text" to bold (as requested by user)
        // CRITICAL FIX: Skip this if the text looks like an SVG attribute (e.g. fill="purple" or width="200")
        // We use a negative lookbehind/lookahead strategy or simply avoid common SVG keywords
        formattedText = formattedText.replace(/(?<![=a-zA-Z])"([^"<>]+)"(?![=a-zA-Z])/g, '<strong>$1</strong>');

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

        contentEl.innerHTML = formattedText + mediaHtml + interactiveButtonsHtml;
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

    // Handler for end-of-series Sí/No buttons
    window.handleSeriesEnd = function (continuar, btnElement) {
        // Disable both buttons
        const allBtns = btnElement.parentElement.querySelectorAll('.interactive-btn');
        allBtns.forEach(b => { b.disabled = true; b.style.opacity = '0.6'; b.style.pointerEvents = 'none'; });
        btnElement.classList.add('correct');

        if (continuar) {
            currentExerciseIndex = 0;
            window._lastQuestionId = 0;
            fetchAndShowQuestion(currentSubject, activeSessionCurso, activeSessionBloque, activeSessionContenido, 1);
        } else {
            addMessage('<p>¡Hasta luego! 👋</p>', 'assistant', true, false, true);
        }
    };

    // Global function to handle clicks on interactive buttons
    window.sendInteractiveAnswer = async function (answer, btnElement) {
        // ── Save correct answer BEFORE anything can nullify it ───────────
        const savedCorrectAnswer = window.currentCorrectAnswer || '';
        const isCorrect = savedCorrectAnswer
            ? answer.trim().toLowerCase() === savedCorrectAnswer.trim().toLowerCase()
            : false;
        const q = window.currentDBQuestion || {};

        // ── Disable ALL buttons in the container ─────────────────────────
        const container = btnElement.parentElement;
        const allButtons = container.querySelectorAll('.interactive-btn');
        allButtons.forEach(btn => {
            btn.disabled = true;
            if (btn !== btnElement) btn.style.opacity = '0.5';
        });
        btnElement.classList.remove('loading');

        // ── Visual feedback on button ─────────────────────────────────────
        if (isCorrect) {
            btnElement.classList.add('correct');
            // Stars
            userStars = parseInt(localStorage.getItem('aula_stars') || '0') + 1;
            localStorage.setItem('aula_stars', userStars);
            const starsLabel = document.getElementById('stars-count');
            if (starsLabel) {
                starsLabel.textContent = userStars;
                starsLabel.parentElement.classList.add('pop');
                setTimeout(() => starsLabel.parentElement.classList.remove('pop'), 800);
            }
            setTimeout(playSuccessAnimation, 0);
        } else {
            btnElement.classList.add('incorrect');
            // Re-enable buttons so student can retry
            allButtons.forEach(btn => {
                btn.disabled = false;
                btn.style.opacity = '1';
            });
            btnElement.disabled = true; // keep selected one locked
        }

        // ── Clear global state ────────────────────────────────────────────
        window.currentCorrectAnswer = null;

        // ── Track answer in DB (progress) ─────────────────────────────────
        if (window.currentDBQuestion && window.currentDBQuestion.id) {
            fetch('/questions/check', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ question_id: window.currentDBQuestion.id, selected_option: answer })
            }).catch(() => { });
        }

        // ── Text feedback (solo si hay texto en la BD) ──────────────────
        if (isCorrect) {
            const fb = q.feedback_correct || '';
            if (fb) addMessage(`<p>✅ ${fb}</p>`, 'assistant', true, false, true);

            // ── Advance counter and fetch next question ───────────────────
            const exerciseNum = currentExerciseIndex; // already set by fetchAndShowQuestion
            const isLastExercise = exerciseNum >= totalExercisesInSeries;

            setTimeout(async () => {
                if (!isLastExercise) {
                    await fetchAndShowQuestion(currentSubject, activeSessionCurso, activeSessionBloque, activeSessionContenido, exerciseNum + 1);
                } else {
                    const endHtml = `<p>¿Quieres seguir practicando?</p><div class="interactive-options"><button class="interactive-btn" onclick="window.handleSeriesEnd(true, this)">Sí</button><button class="interactive-btn" onclick="window.handleSeriesEnd(false, this)">No</button></div>`;
                    addMessage(endHtml, 'assistant', true, false, true);
                    currentExerciseIndex = 0;
                }
            }, 1000);
        } else {
            // ── Do NOT advance — let student retry ────────────────────────
            const fb = q.feedback_incorrect || '';
            if (fb) addMessage(`<p>❌ ${fb}</p>`, 'assistant', true, false, true);
            // Restore currentCorrectAnswer so the next attempt can be checked
            window.currentCorrectAnswer = savedCorrectAnswer;
        }
    };


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
